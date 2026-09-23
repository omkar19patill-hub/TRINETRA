"""Deterministic Factor Evaluator for Risk and Financial CRQ

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Pure mathematical evaluation engine that applies control effects directly
to underlying risk and financial factors, and calls the core Risk Engine
and Financial CRQ Engine to compute true residual risk and residual EAL.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from controls.models import SecurityControl
from financial_crq.engine import calculate_financial_crq
from financial_crq.schemas import FinancialCRQInput, FinancialCRQResult
from risk.engine import calculate_risk
from risk.schemas import RiskCalculationRequest, RiskCalculationResponse
from risk.scoring import get_risk_level


@dataclass
class FactorEvaluationResult:
    """Complete evaluation outcome showing baseline, residual, and avoided losses."""

    baseline_risk_response: RiskCalculationResponse
    residual_risk_response: RiskCalculationResponse
    baseline_crq_response: FinancialCRQResult
    residual_crq_response: FinancialCRQResult
    baseline_risk: float
    residual_risk: float
    risk_reduction: float
    baseline_eal: float
    residual_eal: float
    financial_loss_avoided: float


def evaluate_controls_portfolio(
    selected_controls: List[SecurityControl],
    asset_id: str = "AST-001",
    cve_id: str = "CVE-2026-1234",
    cvss: float = 9.8,
    epss: float = 0.82,
    kev: bool = True,
    internet_exposed: bool = True,
    criticality: str = "Critical",
    revenue_loss_per_hour: float = 250000.0,
    downtime_hours: float = 8.0,
    incident_response_cost: float = 150000.0,
    recovery_cost: float = 200000.0,
    regulatory_legal_cost: float = 500000.0,
    customer_business_impact: float = 300000.0,
    baseline_annual_frequency: float = 1.0,
) -> FactorEvaluationResult:
    """Evaluate pre- and post-intervention risk and financial states deterministically."""
    # -------------------------------------------------------------
    # 1. Baseline Calculations
    # -------------------------------------------------------------
    base_risk_req = RiskCalculationRequest(
        asset_id=asset_id,
        cve_id=cve_id,
        cvss=cvss,
        epss=epss,
        kev=kev,
        internet_exposed=internet_exposed,
        criticality=criticality,
    )
    base_risk_res = calculate_risk(base_risk_req)

    base_crq_req = FinancialCRQInput(
        asset_id=asset_id,
        cve_id=cve_id,
        likelihood=base_risk_res.likelihood,
        risk_score=base_risk_res.risk_score,
        criticality=criticality,
        revenue_loss_per_hour=revenue_loss_per_hour,
        downtime_hours=downtime_hours,
        incident_response_cost=incident_response_cost,
        recovery_cost=recovery_cost,
        regulatory_legal_cost=regulatory_legal_cost,
        customer_business_impact=customer_business_impact,
        baseline_annual_frequency=baseline_annual_frequency,
    )
    base_crq_res = calculate_financial_crq(base_crq_req)

    # If no controls selected, residual equals baseline
    if not selected_controls:
        return FactorEvaluationResult(
            baseline_risk_response=base_risk_res,
            residual_risk_response=base_risk_res,
            baseline_crq_response=base_crq_res,
            residual_crq_response=base_crq_res,
            baseline_risk=base_risk_res.risk_score,
            residual_risk=base_risk_res.risk_score,
            risk_reduction=0.0,
            baseline_eal=base_crq_res.expected_annual_loss,
            residual_eal=base_crq_res.expected_annual_loss,
            financial_loss_avoided=0.0,
        )

    # -------------------------------------------------------------
    # 2. Compounding Control Effects on Underlying Risk Factors
    # -------------------------------------------------------------
    eff_cvss_reduction = sum(c.risk_reduction_effect.cvss_reduction for c in selected_controls)
    eff_cvss = max(0.5, cvss - eff_cvss_reduction)

    eff_epss = epss
    for c in selected_controls:
        eff_epss *= c.risk_reduction_effect.epss_multiplier
    eff_epss = max(0.001, min(1.0, round(eff_epss, 4)))

    eff_kev = kev
    if any(c.risk_reduction_effect.kev_neutralized for c in selected_controls):
        eff_kev = False

    eff_exposed = internet_exposed
    if any(c.risk_reduction_effect.exposure_mitigation for c in selected_controls):
        eff_exposed = False

    # Likelihood mitigation factor compounding: 1 - prod(1 - factor)
    rem_likelihood_factor = 1.0
    for c in selected_controls:
        rem_likelihood_factor *= (1.0 - c.risk_reduction_effect.likelihood_mitigation_factor)
    eff_mitigation = min(0.88, max(0.0, 1.0 - rem_likelihood_factor))

    # Recalculate Risk Engine outputs
    res_risk_req = RiskCalculationRequest(
        asset_id=asset_id,
        cve_id=cve_id,
        cvss=eff_cvss,
        epss=eff_epss,
        kev=eff_kev,
        internet_exposed=eff_exposed,
        criticality=criticality,
    )
    raw_res_risk_res = calculate_risk(res_risk_req)

    # Apply compounded likelihood mitigation factor
    final_likelihood = max(0.001, round(raw_res_risk_res.likelihood * (1.0 - eff_mitigation), 4))
    final_risk_score = round(final_likelihood * raw_res_risk_res.impact * 100.0, 2)
    final_risk_level = get_risk_level(final_risk_score)

    # Construct final residual risk response
    res_risk_res = RiskCalculationResponse(
        asset_id=asset_id,
        cve_id=cve_id,
        risk_score=final_risk_score,
        risk_level=final_risk_level,
        likelihood=final_likelihood,
        impact=raw_res_risk_res.impact,
        risk_drivers=raw_res_risk_res.risk_drivers,
        calculation=raw_res_risk_res.calculation,
        model=raw_res_risk_res.model,
    )

    # -------------------------------------------------------------
    # 3. Compounding Control Effects on Financial Parameters
    # -------------------------------------------------------------
    eff_downtime = downtime_hours
    for c in selected_controls:
        eff_downtime *= (1.0 - c.risk_reduction_effect.downtime_reduction_pct)
    eff_downtime = max(0.2, round(eff_downtime, 2))

    eff_ir = incident_response_cost
    for c in selected_controls:
        eff_ir *= (1.0 - c.risk_reduction_effect.incident_response_reduction_pct)
    eff_ir = max(0.0, round(eff_ir, 2))

    eff_rec = recovery_cost
    for c in selected_controls:
        eff_rec *= (1.0 - c.risk_reduction_effect.recovery_cost_reduction_pct)
    eff_rec = max(0.0, round(eff_rec, 2))

    eff_reg = regulatory_legal_cost
    for c in selected_controls:
        eff_reg *= (1.0 - c.risk_reduction_effect.regulatory_reduction_pct)
    eff_reg = max(0.0, round(eff_reg, 2))

    eff_cust = customer_business_impact
    for c in selected_controls:
        eff_cust *= (1.0 - c.risk_reduction_effect.customer_impact_reduction_pct)
    eff_cust = max(0.0, round(eff_cust, 2))

    res_crq_req = FinancialCRQInput(
        asset_id=asset_id,
        cve_id=cve_id,
        likelihood=final_likelihood,
        risk_score=final_risk_score,
        criticality=criticality,
        revenue_loss_per_hour=revenue_loss_per_hour,
        downtime_hours=eff_downtime,
        incident_response_cost=eff_ir,
        recovery_cost=eff_rec,
        regulatory_legal_cost=eff_reg,
        customer_business_impact=eff_cust,
        baseline_annual_frequency=baseline_annual_frequency,
    )
    res_crq_res = calculate_financial_crq(res_crq_req)

    risk_reduction = round(max(0.0, base_risk_res.risk_score - final_risk_score), 2)
    financial_loss_avoided = round(max(0.0, base_crq_res.expected_annual_loss - res_crq_res.expected_annual_loss), 2)

    return FactorEvaluationResult(
        baseline_risk_response=base_risk_res,
        residual_risk_response=res_risk_res,
        baseline_crq_response=base_crq_res,
        residual_crq_response=res_crq_res,
        baseline_risk=base_risk_res.risk_score,
        residual_risk=final_risk_score,
        risk_reduction=risk_reduction,
        baseline_eal=base_crq_res.expected_annual_loss,
        residual_eal=res_crq_res.expected_annual_loss,
        financial_loss_avoided=financial_loss_avoided,
    )
