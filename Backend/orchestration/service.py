"""Continuous Re-Optimization Orchestrator Service (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Coordinates the automated multi-stage pipeline:
1. Threat & Asset Trigger Ingestion -> Identify Affected Assets
2. Recalculate Deterministic Risk Score (/risk)
3. Recalculate Financial CRQ & Expected Annual Loss (/financial-crq)
4. Run Stochastic Monte Carlo Uncertainty Simulation (/monte-carlo)
5. Re-run Cybersecurity Control Portfolio Optimization (/decision)
6. Compare Old vs New Decision Deltas (Risk, P95, Controls, Costs)
7. Optionally Anchor Decision Provenance to Blockchain Ledger (/blockchain)
"""

import copy
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from blockchain.hashing import (
    compute_composite_hash,
    compute_data_snapshot_hash,
    compute_result_hash,
)
from blockchain.provider import get_blockchain_provider
from blockchain.schemas import ProvenanceRecord
from decision.alternatives import generate_alternative_portfolios
from decision.schemas import CandidateControl, OptimizationResult
from decision.store import get_optimization, save_optimization
from financial_crq.engine import calculate_financial_crq
from financial_crq.schemas import FinancialCRQInput
from monte_carlo.simulator import build_monte_carlo_input_from_crq, run_simulation
from risk.engine import calculate_risk
from risk.schemas import RiskCalculationRequest

from . import ORCHESTRATION_MODEL_VERSION
from .schemas import (
    PortfolioDeltaSummary,
    ReoptimizeRequest,
    ReoptimizeResponse,
)
from .state import (
    AssetState,
    detect_change_reasons,
    get_asset_state,
    identify_affected_assets,
    increment_reoptimization_counter,
    update_asset_state,
)

logger = logging.getLogger("trinetra.orchestration")


def _get_benchmark_candidate_controls(multiplier: float = 1.0) -> List[CandidateControl]:
    """Retrieve standard candidate control catalog scaled by risk multiplier."""
    base = [
        CandidateControl(
            control_id="CTRL-MFA",
            name="Phishing-Resistant MFA",
            cost=350000.0,
            risk_reduction=680000.0 * multiplier,
            workforce_hours=80.0,
            implementation_days=14,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-004"],
            critical_assets_covered=4,
            category="Identity & Access",
        ),
        CandidateControl(
            control_id="CTRL-EDR",
            name="Next-Gen EDR",
            cost=600000.0,
            risk_reduction=1050000.0 * multiplier,
            workforce_hours=140.0,
            implementation_days=21,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-005"],
            critical_assets_covered=4,
            category="Endpoint Security",
        ),
        CandidateControl(
            control_id="CTRL-PATCH",
            name="Automated Patch Management",
            cost=400000.0,
            risk_reduction=720000.0 * multiplier,
            workforce_hours=100.0,
            implementation_days=28,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-004"],
            critical_assets_covered=4,
            category="Vulnerability Management",
        ),
        CandidateControl(
            control_id="CTRL-BACKUP",
            name="Immutable Cloud Backups",
            cost=450000.0,
            risk_reduction=800000.0 * multiplier,
            workforce_hours=90.0,
            implementation_days=18,
            applicable_assets=["AST-001", "AST-002", "AST-003"],
            critical_assets_covered=3,
            category="Data Resilience",
        ),
        CandidateControl(
            control_id="CTRL-WAF",
            name="Cloud Web Application Firewall",
            cost=500000.0,
            risk_reduction=650000.0 * multiplier,
            workforce_hours=110.0,
            implementation_days=20,
            applicable_assets=["AST-001", "AST-002", "AST-004"],
            critical_assets_covered=3,
            category="Application Security",
        ),
        CandidateControl(
            control_id="CTRL-PAM",
            name="Privileged Access Management",
            cost=700000.0,
            risk_reduction=750000.0 * multiplier,
            workforce_hours=160.0,
            implementation_days=35,
            applicable_assets=["AST-001", "AST-002"],
            critical_assets_covered=2,
            category="Identity & Access",
        ),
        CandidateControl(
            control_id="CTRL-SIEM",
            name="SIEM & 24/7 SOC Triage",
            cost=1200000.0,
            risk_reduction=1100000.0 * multiplier,
            workforce_hours=220.0,
            implementation_days=60,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-004"],
            critical_assets_covered=4,
            category="Security Operations",
        ),
    ]
    return base


def run_continuous_reoptimization(request: ReoptimizeRequest) -> ReoptimizeResponse:
    """Execute the end-to-end continuous re-optimization orchestration pipeline.
    
    Workflow:
    1. Identify Affected Asset & Baseline State.
    2. Detect concrete change reasons comparing old vs new trigger parameters.
    3. Compute Previous Baseline calculations (Risk, CRQ, Monte Carlo, Decision Portfolio).
    4. Compute New Recalculated outputs (Deterministic Risk, Financial CRQ, Monte Carlo, Portfolio Optimization).
    5. Evaluate Decision Deltas (Risk score delta, EAL delta, P95 delta, Control diffs).
    6. Update live asset registry.
    7. Optionally record new decision provenance on the Blockchain layer (append-only, never overwriting history).
    """
    counter = increment_reoptimization_counter()
    now_iso = datetime.now(timezone.utc).isoformat()
    reopt_id = f"REOPT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{counter:04d}"

    # -------------------------------------------------------------
    # 1. Identify Affected Asset & Baseline Context
    # -------------------------------------------------------------
    affected_assets = identify_affected_assets(cve_id=request.cve_id, asset_id=request.asset_id)
    target_asset = affected_assets[0]
    previous_state = copy.deepcopy(target_asset)

    # -------------------------------------------------------------
    # 2. Detect Concrete Change Reasons
    # -------------------------------------------------------------
    change_reasons = detect_change_reasons(
        previous=previous_state,
        new_cvss=request.cvss,
        new_epss=request.epss,
        new_kev=request.kev,
        new_exposed=request.internet_exposed,
        new_criticality=request.criticality,
        new_patched=request.is_patched,
        new_budget=request.budget_limit,
        new_rev_loss=request.revenue_loss_per_hour,
        new_downtime=request.downtime_hours,
    )

    # -------------------------------------------------------------
    # 3. Calculate PREVIOUS Baseline Metrics
    # -------------------------------------------------------------
    prev_risk_input = RiskCalculationRequest(
        asset_id=previous_state.asset_id,
        cve_id=previous_state.cve_id,
        cvss=previous_state.cvss if not previous_state.is_patched else 1.0,
        epss=previous_state.epss if not previous_state.is_patched else 0.01,
        kev=previous_state.kev if not previous_state.is_patched else False,
        internet_exposed=previous_state.internet_exposed,
        criticality=previous_state.criticality,
    )
    prev_risk_res = calculate_risk(prev_risk_input)

    prev_crq_input = FinancialCRQInput(
        asset_id=previous_state.asset_id,
        cve_id=previous_state.cve_id,
        likelihood=prev_risk_res.likelihood,
        risk_score=prev_risk_res.risk_score,
        criticality=previous_state.criticality,
        revenue_loss_per_hour=previous_state.revenue_loss_per_hour,
        downtime_hours=previous_state.downtime_hours,
        incident_response_cost=previous_state.incident_response_cost,
        recovery_cost=previous_state.recovery_cost,
        regulatory_legal_cost=previous_state.regulatory_fine_estimate,
        customer_business_impact=previous_state.customer_impact_cost,
    )
    prev_crq_res = calculate_financial_crq(prev_crq_input)

    prev_mc_input = build_monte_carlo_input_from_crq(
        crq_input=prev_crq_input,
        iterations=request.iterations,
        seed=request.seed,
    )
    prev_mc_res = run_simulation(prev_mc_input)
    prev_p95 = prev_mc_res.p95

    # Baseline portfolio from store or calculated
    prev_opt_id = request.optimization_id or "OPT-BENCHMARK-001"
    existing_opt = get_optimization(prev_opt_id)
    if existing_opt:
        prev_alt_res = generate_alternative_portfolios(existing_opt)
        prev_portfolio_obj = next(
            (p for p in prev_alt_res.alternatives if p.portfolio_id == prev_alt_res.selected_portfolio_id),
            prev_alt_res.alternatives[0],
        )
    else:
        # Fallback baseline optimization
        fallback_opt = OptimizationResult(
            optimization_id=prev_opt_id,
            title="Baseline Optimization Portfolio",
            baseline_risk=prev_crq_res.expected_annual_loss,
            budget_limit=previous_state.budget_limit,
            currency="INR",
            candidate_controls=_get_benchmark_candidate_controls(),
        )
        prev_alt_res = generate_alternative_portfolios(fallback_opt)
        prev_portfolio_obj = prev_alt_res.alternatives[0]

    # -------------------------------------------------------------
    # 4. Resolve NEW Parameters & Recalculate Downstream
    # -------------------------------------------------------------
    new_cvss = request.cvss if request.cvss is not None else previous_state.cvss
    new_epss = request.epss if request.epss is not None else previous_state.epss
    new_kev = request.kev if request.kev is not None else previous_state.kev
    new_exposed = request.internet_exposed if request.internet_exposed is not None else previous_state.internet_exposed
    new_criticality = request.criticality if request.criticality is not None else previous_state.criticality
    new_patched = request.is_patched if request.is_patched is not None else previous_state.is_patched
    new_budget = request.budget_limit if request.budget_limit is not None else previous_state.budget_limit
    new_rev_loss = request.revenue_loss_per_hour if request.revenue_loss_per_hour is not None else previous_state.revenue_loss_per_hour
    new_downtime = request.downtime_hours if request.downtime_hours is not None else previous_state.downtime_hours

    # If patched, effectively neutralize vulnerability risk
    effective_cvss = 1.0 if new_patched else new_cvss
    effective_epss = 0.01 if new_patched else new_epss
    effective_kev = False if new_patched else new_kev

    # 4a. Recalculate Deterministic Risk
    new_risk_input = RiskCalculationRequest(
        asset_id=previous_state.asset_id,
        cve_id=previous_state.cve_id,
        cvss=effective_cvss,
        epss=effective_epss,
        kev=effective_kev,
        internet_exposed=new_exposed,
        criticality=new_criticality,
    )
    new_risk_res = calculate_risk(new_risk_input)

    # 4b. Recalculate Financial CRQ
    new_crq_input = FinancialCRQInput(
        asset_id=previous_state.asset_id,
        cve_id=previous_state.cve_id,
        likelihood=new_risk_res.likelihood,
        risk_score=new_risk_res.risk_score,
        criticality=new_criticality,
        revenue_loss_per_hour=new_rev_loss,
        downtime_hours=new_downtime,
        incident_response_cost=previous_state.incident_response_cost,
        recovery_cost=previous_state.recovery_cost,
        regulatory_legal_cost=previous_state.regulatory_fine_estimate,
        customer_business_impact=previous_state.customer_impact_cost,
    )
    new_crq_res = calculate_financial_crq(new_crq_input)

    # 4c. Run Stochastic Monte Carlo Simulation
    new_mc_input = build_monte_carlo_input_from_crq(
        crq_input=new_crq_input,
        iterations=request.iterations,
        seed=request.seed,
    )
    new_mc_res = run_simulation(new_mc_input)
    new_p95 = new_mc_res.p95

    # 4d. Re-run Portfolio Optimization
    new_opt_id = f"OPT-{previous_state.asset_id}-{counter:03d}"
    risk_scaling = max(0.2, new_crq_res.expected_annual_loss / 1800000.0)
    new_controls = _get_benchmark_candidate_controls(multiplier=risk_scaling)

    new_opt_scenario = OptimizationResult(
        optimization_id=new_opt_id,
        title=f"Continuous Re-Optimization for {previous_state.asset_id} ({reopt_id})",
        baseline_risk=new_crq_res.expected_annual_loss,
        budget_limit=new_budget,
        currency="INR",
        candidate_controls=new_controls,
        created_at=now_iso,
    )
    save_optimization(new_opt_scenario)

    new_alt_res = generate_alternative_portfolios(new_opt_scenario)
    new_portfolio_obj = next(
        (p for p in new_alt_res.alternatives if p.portfolio_id == new_alt_res.selected_portfolio_id),
        new_alt_res.alternatives[0],
    )

    # -------------------------------------------------------------
    # 5. Evaluate Decision Deltas
    # -------------------------------------------------------------
    risk_delta = round(new_risk_res.risk_score - prev_risk_res.risk_score, 2)
    crq_eal_delta = round(new_crq_res.expected_annual_loss - prev_crq_res.expected_annual_loss, 2)
    p95_delta = round(new_p95 - prev_p95, 2)

    old_ctrl_ids = prev_portfolio_obj.selected_controls
    new_ctrl_ids = new_portfolio_obj.selected_controls

    controls_added = [c for c in new_ctrl_ids if c not in old_ctrl_ids]
    controls_removed = [c for c in old_ctrl_ids if c not in new_ctrl_ids]
    portfolio_changed = bool(controls_added or controls_removed or abs(new_portfolio_obj.total_cost - prev_portfolio_obj.total_cost) > 1.0)

    portfolio_delta = PortfolioDeltaSummary(
        previous_portfolio_id=prev_portfolio_obj.portfolio_id,
        new_portfolio_id=new_portfolio_obj.portfolio_id,
        previous_cost=prev_portfolio_obj.total_cost,
        new_cost=new_portfolio_obj.total_cost,
        cost_delta=round(new_portfolio_obj.total_cost - prev_portfolio_obj.total_cost, 2),
        previous_risk_reduction=prev_portfolio_obj.risk_reduction,
        new_risk_reduction=new_portfolio_obj.risk_reduction,
        risk_reduction_delta=round(new_portfolio_obj.risk_reduction - prev_portfolio_obj.risk_reduction, 2),
        previous_controls=old_ctrl_ids,
        new_controls=new_ctrl_ids,
        controls_added=controls_added,
        controls_removed=controls_removed,
        portfolio_changed=portfolio_changed,
    )

    # -------------------------------------------------------------
    # 6. Update Live Asset State in Registry
    # -------------------------------------------------------------
    updated_asset = AssetState(
        asset_id=previous_state.asset_id,
        name=previous_state.name,
        cve_id=previous_state.cve_id,
        cvss=new_cvss,
        epss=new_epss,
        kev=new_kev,
        internet_exposed=new_exposed,
        criticality=new_criticality,
        is_patched=new_patched,
        revenue_loss_per_hour=new_rev_loss,
        downtime_hours=new_downtime,
        budget_limit=new_budget,
    )
    update_asset_state(previous_state.asset_id, updated_asset)

    # -------------------------------------------------------------
    # 7. Optionally Record New Decision Provenance on Blockchain
    # -------------------------------------------------------------
    receipt = None
    provenance_recorded = False
    new_assessment_id = f"CRQ-{previous_state.asset_id}-{counter:03d}"

    if request.record_provenance:
        provider = get_blockchain_provider()

        # Build snapshot data for canonical hashing
        snapshot_data = {
            "assessment_id": new_assessment_id,
            "reoptimization_id": reopt_id,
            "asset_id": previous_state.asset_id,
            "cve_id": previous_state.cve_id,
            "cvss": new_cvss,
            "epss": new_epss,
            "kev": new_kev,
            "internet_exposed": new_exposed,
            "criticality": new_criticality,
            "is_patched": new_patched,
            "budget_limit": new_budget,
        }

        result_data = {
            "assessment_id": new_assessment_id,
            "decision_id": new_opt_id,
            "risk_score": new_risk_res.risk_score,
            "expected_annual_loss": new_crq_res.expected_annual_loss,
            "monte_carlo_p95": new_p95,
            "selected_portfolio_id": new_portfolio_obj.portfolio_id,
            "selected_controls": new_ctrl_ids,
            "total_cost": new_portfolio_obj.total_cost,
            "risk_reduction": new_portfolio_obj.risk_reduction,
        }

        data_snapshot_hash = compute_data_snapshot_hash(snapshot_data)
        result_hash = compute_result_hash(result_data)

        canonical_hash = compute_composite_hash(
            assessment_id=new_assessment_id,
            decision_id=new_opt_id,
            model_version=ORCHESTRATION_MODEL_VERSION,
            timestamp=now_iso,
            data_snapshot_hash=data_snapshot_hash,
            result_hash=result_hash,
        )

        provenance_rec = ProvenanceRecord(
            assessment_id=new_assessment_id,
            decision_id=new_opt_id,
            model_version=ORCHESTRATION_MODEL_VERSION,
            timestamp=now_iso,
            data_snapshot_hash=data_snapshot_hash,
            result_hash=result_hash,
            canonical_hash=canonical_hash,
            metadata={
                "trigger_reasons": change_reasons,
                "reoptimization_id": reopt_id,
            },
        )

        try:
            receipt = provider.record_hash(provenance_rec)
            provenance_recorded = True
            logger.info(
                "[Orchestrator] Anchored re-optimization %s (Tx: %s, Block #%d)",
                new_assessment_id,
                receipt.tx_hash[:16],
                receipt.block_height,
            )
        except Exception as e:
            logger.warning("[Orchestrator] Blockchain provenance recording warning: %s", e)

    return ReoptimizeResponse(
        reoptimization_id=reopt_id,
        asset_id=previous_state.asset_id,
        cve_id=previous_state.cve_id,
        status="REOPTIMIZATION_COMPLETE",
        timestamp=now_iso,
        change_reasons=change_reasons,
        previous_risk={
            "score": prev_risk_res.risk_score,
            "level": prev_risk_res.risk_level.value if hasattr(prev_risk_res.risk_level, "value") else str(prev_risk_res.risk_level),
            "likelihood": prev_risk_res.likelihood,
            "impact": prev_risk_res.impact,
        },
        new_risk={
            "score": new_risk_res.risk_score,
            "level": new_risk_res.risk_level.value if hasattr(new_risk_res.risk_level, "value") else str(new_risk_res.risk_level),
            "likelihood": new_risk_res.likelihood,
            "impact": new_risk_res.impact,
        },
        risk_delta=risk_delta,
        previous_crq_eal=prev_crq_res.expected_annual_loss,
        new_crq_eal=new_crq_res.expected_annual_loss,
        crq_eal_delta=crq_eal_delta,
        previous_p95=prev_p95,
        new_p95=new_p95,
        p95_delta=p95_delta,
        previous_portfolio={
            "portfolio_id": prev_portfolio_obj.portfolio_id,
            "objective": prev_portfolio_obj.objective,
            "total_cost": prev_portfolio_obj.total_cost,
            "risk_reduction": prev_portfolio_obj.risk_reduction,
            "residual_risk": prev_portfolio_obj.residual_risk,
            "selected_controls": prev_portfolio_obj.selected_controls,
        },
        new_portfolio={
            "portfolio_id": new_portfolio_obj.portfolio_id,
            "objective": new_portfolio_obj.objective,
            "total_cost": new_portfolio_obj.total_cost,
            "risk_reduction": new_portfolio_obj.risk_reduction,
            "residual_risk": new_portfolio_obj.residual_risk,
            "selected_controls": new_portfolio_obj.selected_controls,
        },
        portfolio_delta=portfolio_delta,
        new_optimization_id=new_opt_id,
        assessment_id=new_assessment_id,
        provenance_recorded=provenance_recorded,
        blockchain_receipt=receipt,
    )
