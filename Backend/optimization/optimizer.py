"""Deterministic Fixed-Budget Cybersecurity Investment Optimizer

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Coordinates:
1. Candidate control ingestion, deduplication, and applicability validation.
2. Dependency resolution and budget constraint enforcement.
3. Factor-based quantitative impact evaluation (no arbitrary risk subtraction).
4. Deterministic greedy / 0-1 knapsack portfolio packing based on Return on Security Investment (ROSI).
5. Evidence-based selection and rejection reason generation.
6. Seamless registration into the Decision Intelligence store.
"""

import copy
import logging
import uuid
from typing import Dict, List, Optional, Set, Tuple

from controls.catalog import get_all_controls, get_control_by_id
from controls.models import ControlDependencyResolution, SecurityControl
from controls.resolver import (
    CircularDependencyError,
    ControlDependencyResolver,
    is_control_applicable,
)
from decision.schemas import CandidateControl, OptimizationResult
from decision.store import save_optimization


from .evaluator import FactorEvaluationResult, evaluate_controls_portfolio
from .schemas import (
    OPTIMIZATION_MODEL_VERSION,
    OptimizationRunRequest,
    OptimizationRunResponse,
)

logger = logging.getLogger("trinetra.optimization")


def _deduplicate_controls(controls: List[SecurityControl]) -> List[SecurityControl]:
    """Remove duplicate controls preserving the first unique instance."""
    seen: Set[str] = set()
    deduped: List[SecurityControl] = []
    for c in controls:
        cid = c.control_id.strip().upper()
        if cid not in seen:
            seen.add(cid)
            deduped.append(c)
    return deduped


def _is_applicable(control: SecurityControl, target_asset_type: str) -> bool:
    """Validate whether a control is architecturally applicable to an asset archetype."""
    target_norm = target_asset_type.strip().lower()
    for app_type in control.applicable_asset_types:
        app_norm = app_type.strip().lower()
        if app_norm == "all" or app_norm == target_norm:
            return True
    return False


def run_optimization(request: OptimizationRunRequest) -> OptimizationRunResponse:
    """Execute deterministic cybersecurity investment optimization under fixed budget."""
    if request.budget_limit < 0:
        raise ValueError("Budget limit must be non-negative.")

    # 1. Resolve candidate controls pool
    pool: List[SecurityControl] = []
    if request.candidate_control_ids:
        for cid in request.candidate_control_ids:
            found = get_control_by_id(cid)
            if found:
                pool.append(found)
            else:
                logger.warning(f"[Optimizer] Requested control ID '{cid}' not found in catalog.")
    else:
        pool.extend(get_all_controls())

    if request.custom_controls:
        pool.extend(request.custom_controls)

    # 2. Deduplicate candidate controls
    unique_candidates = _deduplicate_controls(pool)

    # 2b. Initialize Dependency Resolver and validate circular dependencies
    target_asset_type = request.asset_type or "web_application"
    candidate_ids_set = (
        set(c.upper() for c in request.candidate_control_ids)
        if request.candidate_control_ids is not None
        else None
    )
    resolver = ControlDependencyResolver(
        controls_pool=unique_candidates,
        asset_type=target_asset_type,
        budget_limit=request.budget_limit,
        existing_controls=request.existing_controls,
        candidate_ids=candidate_ids_set,
    )
    # Validate cycles among requested candidates
    candidate_ids = [c.control_id for c in unique_candidates]
    resolver.detect_cycles(candidate_ids)


    # 3. Baseline Evaluation (No controls applied)
    baseline_eval = evaluate_controls_portfolio(
        selected_controls=[],
        asset_id=request.asset_id or "AST-001",
        cve_id=request.cve_id or "CVE-2026-1234",
        cvss=request.cvss if request.cvss is not None else 9.8,
        epss=request.epss if request.epss is not None else 0.82,
        kev=request.kev if request.kev is not None else True,
        internet_exposed=request.internet_exposed if request.internet_exposed is not None else True,
        criticality=request.criticality or "Critical",
        revenue_loss_per_hour=request.revenue_loss_per_hour or 250000.0,
        downtime_hours=request.downtime_hours or 8.0,
        incident_response_cost=request.incident_response_cost or 150000.0,
        recovery_cost=request.recovery_cost or 200000.0,
        regulatory_legal_cost=request.regulatory_legal_cost or 500000.0,
        customer_business_impact=request.customer_business_impact or 300000.0,
    )

    selection_reasons: Dict[str, List[str]] = {}
    rejection_reasons: Dict[str, List[str]] = {}

    existing_set: Set[str] = set(c.upper() for c in (request.existing_controls or []))
    eligible_candidates: List[SecurityControl] = []

    # 4. Filter Inapplicable Controls & Zero-Budget Edge Cases
    for ctrl in unique_candidates:
        cid = ctrl.control_id.upper()
        # Zero Budget check
        if request.budget_limit <= 0 and ctrl.implementation_cost > 0:
            rejection_reasons[ctrl.control_id] = [
                f"Budget constraint: Zero budget allocated (Control cost: ₹{ctrl.implementation_cost:,.0f})"
            ]
            continue

        # Applicability check
        if not _is_applicable(ctrl, target_asset_type):
            rejection_reasons[ctrl.control_id] = [
                f"Inapplicable: Control is not designated for asset type '{target_asset_type}' (Applies to: {', '.join(ctrl.applicable_asset_types)})"
            ]
            continue

        # Standalone cost exceeding total budget ceiling
        if ctrl.implementation_cost > request.budget_limit:
            rejection_reasons[ctrl.control_id] = [
                f"Budget constraint: Implementation cost (₹{ctrl.implementation_cost:,.0f}) exceeds total budget ceiling (₹{request.budget_limit:,.0f})"
            ]
            continue

        eligible_candidates.append(ctrl)

    # 5. Evaluate Individual Efficiency (ROSI = EAL Avoided / Cost)
    scored_candidates: List[Tuple[SecurityControl, float, float]] = []
    for ctrl in eligible_candidates:
        single_eval = evaluate_controls_portfolio(
            selected_controls=[ctrl],
            asset_id=request.asset_id or "AST-001",
            cve_id=request.cve_id or "CVE-2026-1234",
            cvss=request.cvss if request.cvss is not None else 9.8,
            epss=request.epss if request.epss is not None else 0.82,
            kev=request.kev if request.kev is not None else True,
            internet_exposed=request.internet_exposed if request.internet_exposed is not None else True,
            criticality=request.criticality or "Critical",
            revenue_loss_per_hour=request.revenue_loss_per_hour or 250000.0,
            downtime_hours=request.downtime_hours or 8.0,
            incident_response_cost=request.incident_response_cost or 150000.0,
            recovery_cost=request.recovery_cost or 200000.0,
            regulatory_legal_cost=request.regulatory_legal_cost or 500000.0,
            customer_business_impact=request.customer_business_impact or 300000.0,
        )
        cost = ctrl.implementation_cost
        avoided = single_eval.financial_loss_avoided
        efficiency = (avoided / cost) if cost > 0 else (avoided * 100.0)
        scored_candidates.append((ctrl, efficiency, avoided))

    # Deterministic sort: Primary = efficiency descending, Secondary = avoided loss descending, Tertiary = cost ascending
    scored_candidates.sort(key=lambda item: (-item[1], -item[2], item[0].implementation_cost))

    # 6. Portfolio Packing with Recursive Dependency Resolution
    selected_controls: List[SecurityControl] = []
    selected_ids: Set[str] = set(existing_set)
    dependency_resolutions: List[ControlDependencyResolution] = []
    current_cost = 0.0
    remaining_budget = request.budget_limit

    for ctrl, efficiency, avoided in scored_candidates:
        cid = ctrl.control_id.upper()
        if cid in selected_ids:
            continue

        resolution = resolver.resolve_bundle(
            control=ctrl,
            already_selected_ids=selected_ids,
            remaining_budget=remaining_budget,
        )
        dependency_resolutions.append(resolution)

        if resolution.status == "selected":
            selected_controls.append(ctrl)
            selected_ids.add(cid)
            # Add any dependencies included in this bundle
            for dep_item in resolution.dependencies:
                dep_cid = dep_item.control_id.upper()
                if dep_cid not in selected_ids:
                    dep_ctrl = resolver.get_control(dep_item.control_id)
                    if dep_ctrl and dep_ctrl not in selected_controls:
                        selected_controls.append(dep_ctrl)
                    selected_ids.add(dep_cid)
                    selection_reasons[dep_item.control_id] = [
                        f"Selected as prerequisite dependency for {ctrl.control_id}",
                        f"Fits within budget (Cost: ₹{dep_ctrl.implementation_cost:,.0f})" if dep_ctrl else "Fits within budget",
                    ]
            current_cost += resolution.bundle_cost
            remaining_budget = max(0.0, remaining_budget - resolution.bundle_cost)

            roi_metric = round(efficiency, 2)
            reasons = [
                f"High modeled cost-benefit efficiency (ROSI: {roi_metric:.2f}x loss avoided per rupee)",
                f"Fits within available budget allocation (Bundle cost: ₹{resolution.bundle_cost:,.0f})",
                f"Directly mitigates primary risk factors ({ctrl.category})",
            ]
            if ctrl.implementation_time <= 21:
                reasons.append(f"Rapid deployment timeframe ({ctrl.implementation_time} days)")
            if resolution.dependencies:
                reasons.append(f"All prerequisite dependencies verified ({', '.join(d.control_id for d in resolution.dependencies)})")
            selection_reasons[ctrl.control_id] = reasons
        else:
            rejection_reasons[ctrl.control_id] = [
                resolution.rejection_reason or "Dependency constraint or exceeds available budget"
            ]

    # Also record resolutions for initially filtered-out candidates (zero budget, inapplicability, standalone budget exceed)
    for ctrl in unique_candidates:
        if ctrl not in eligible_candidates:
            res = resolver.resolve_bundle(
                control=ctrl,
                already_selected_ids=selected_ids,
                remaining_budget=remaining_budget,
            )
            # Avoid duplicate in dependency_resolutions
            if not any(r.control_id == ctrl.control_id for r in dependency_resolutions):
                dependency_resolutions.append(res)

    # 7. Final Quantitative Factor Re-Evaluation across Entire Portfolio
    final_eval = evaluate_controls_portfolio(
        selected_controls=selected_controls,
        asset_id=request.asset_id or "AST-001",
        cve_id=request.cve_id or "CVE-2026-1234",
        cvss=request.cvss if request.cvss is not None else 9.8,
        epss=request.epss if request.epss is not None else 0.82,
        kev=request.kev if request.kev is not None else True,
        internet_exposed=request.internet_exposed if request.internet_exposed is not None else True,
        criticality=request.criticality or "Critical",
        revenue_loss_per_hour=request.revenue_loss_per_hour or 250000.0,
        downtime_hours=request.downtime_hours or 8.0,
        incident_response_cost=request.incident_response_cost or 150000.0,
        recovery_cost=request.recovery_cost or 200000.0,
        regulatory_legal_cost=request.regulatory_legal_cost or 500000.0,
        customer_business_impact=request.customer_business_impact or 300000.0,
    )

    selected_ids_list = [c.control_id for c in selected_controls]
    all_candidate_ids = [c.control_id for c in unique_candidates]
    rejected_ids_list = [cid for cid in all_candidate_ids if cid not in selected_ids_list]

    # Fill default rejection reasons for any unselected controls without reasons
    for cid in rejected_ids_list:
        if cid not in rejection_reasons:
            rejection_reasons[cid] = [
                "Marginal modeled benefit surpassed by higher-ranked candidate controls within budget"
            ]

    opt_id = request.optimization_id or f"OPT-RUN-{uuid.uuid4().hex[:8].upper()}"

    # 8. Register into Decision Intelligence Store (if enabled)
    if request.record_to_decision_store:
        candidate_controls_for_decision: List[CandidateControl] = []
        for c in unique_candidates:
            # Standalone risk reduction estimate for Decision Intelligence compatibility
            c_avoided = next((item[2] for item in scored_candidates if item[0].control_id == c.control_id), 500000.0)
            candidate_controls_for_decision.append(
                CandidateControl(
                    control_id=c.control_id,
                    name=c.control_name,
                    cost=c.implementation_cost,
                    risk_reduction=c_avoided,
                    workforce_hours=float(c.implementation_time * 8),
                    implementation_days=c.implementation_time,
                    applicable_assets=[request.asset_id or "AST-001"],
                    critical_assets_covered=1 if (request.criticality or "").lower() in ["critical", "high"] else 0,
                    category=c.category,
                    description=c.description,
                )
            )

        opt_result = OptimizationResult(
            optimization_id=opt_id,
            title=f"Cyber Investment Optimization for {request.asset_id or 'AST-001'} ({opt_id})",
            baseline_risk=final_eval.baseline_eal,
            budget_limit=request.budget_limit,
            currency="INR",
            selected_portfolio_id="portfolio-balanced-roi",
            candidate_controls=candidate_controls_for_decision,
            data_source="actual_optimizer",
            is_benchmark=False,
            model_version=OPTIMIZATION_MODEL_VERSION,
            assessment_id=request.asset_id or "AST-001",
        )
        save_optimization(opt_result, is_benchmark=False)

    return OptimizationRunResponse(
        selected_controls=selected_ids_list,
        rejected_controls=rejected_ids_list,
        total_cost=round(current_cost, 2),
        remaining_budget=round(remaining_budget, 2),
        baseline_risk=final_eval.baseline_risk,
        residual_risk=final_eval.residual_risk,
        risk_reduction=final_eval.risk_reduction,
        baseline_eal=final_eval.baseline_eal,
        residual_eal=final_eval.residual_eal,
        financial_loss_avoided=final_eval.financial_loss_avoided,
        selection_reasons=selection_reasons,
        rejection_reasons=rejection_reasons,
        model_version=OPTIMIZATION_MODEL_VERSION,
        optimization_id=opt_id,
        data_source="actual_optimizer",
        is_benchmark=False,
        assessment_id=request.asset_id or "AST-001",
        dependency_resolution=dependency_resolutions,
    )

