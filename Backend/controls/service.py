"""Service Logic for Security Controls Catalog Assessment

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Evaluates individual controls against asset risk and financial parameters:
- Applicability validation
- Dependency chain verification
- Marginal risk reduction estimation
- Expected Annual Loss (EAL) avoidance modeling
- Cost-benefit efficiency ratio computation
"""

from typing import List, Optional
from financial_crq.engine import calculate_financial_crq
from financial_crq.schemas import FinancialCRQInput
from risk.engine import calculate_risk
from risk.schemas import RiskCalculationRequest

from .catalog import get_all_controls, get_control_by_id
from .models import (
    ControlAssessRequest,
    ControlAssessResponse,
    ControlAssessmentItem,
    SecurityControl,
)


def assess_controls(request: ControlAssessRequest) -> ControlAssessResponse:
    """Evaluate controls against an asset context using deterministic modeling."""
    # 1. Resolve controls to assess
    if request.control_ids:
        controls_to_assess = []
        for cid in request.control_ids:
            c = get_control_by_id(cid)
            if c:
                controls_to_assess.append(c)
    else:
        controls_to_assess = get_all_controls()

    # 2. Compute Baseline Risk & Financial CRQ
    baseline_risk_input = RiskCalculationRequest(
        asset_id=request.asset_id or "AST-001",
        cve_id="CVE-ASSESS",
        cvss=request.cvss if request.cvss is not None else 9.8,
        epss=request.epss if request.epss is not None else 0.82,
        kev=request.kev if request.kev is not None else True,
        internet_exposed=request.internet_exposed if request.internet_exposed is not None else True,
        criticality=request.criticality or "Critical",
    )
    baseline_risk_res = calculate_risk(baseline_risk_input)

    baseline_crq_input = FinancialCRQInput(
        asset_id=request.asset_id or "AST-001",
        cve_id="CVE-ASSESS",
        likelihood=baseline_risk_res.likelihood,
        risk_score=baseline_risk_res.risk_score,
        criticality=request.criticality or "Critical",
        revenue_loss_per_hour=request.revenue_loss_per_hour or 250000.0,
        downtime_hours=request.downtime_hours or 8.0,
        incident_response_cost=request.incident_response_cost or 150000.0,
        recovery_cost=request.recovery_cost or 200000.0,
        regulatory_legal_cost=request.regulatory_legal_cost or 500000.0,
        customer_business_impact=request.customer_business_impact or 300000.0,
    )
    baseline_crq_res = calculate_financial_crq(baseline_crq_input)
    baseline_eal = baseline_crq_res.expected_annual_loss

    existing_set = set(request.existing_controls or [])
    norm_asset_type = (request.asset_type or "all").strip().lower()

    items: List[ControlAssessmentItem] = []

    # 3. Assess each control individually
    for ctrl in controls_to_assess:
        # Check applicability
        is_applicable = (
            "all" in [t.lower() for t in ctrl.applicable_asset_types]
            or norm_asset_type in [t.lower() for t in ctrl.applicable_asset_types]
        )

        # Check dependencies
        missing_deps = [dep for dep in ctrl.required_dependencies if dep not in existing_set]
        dependencies_satisfied = len(missing_deps) == 0

        # Calculate control-specific factor alterations
        eff = ctrl.risk_reduction_effect
        mod_cvss = max(0.0, baseline_risk_input.cvss - eff.cvss_reduction)
        mod_epss = max(0.001, baseline_risk_input.epss * eff.epss_multiplier)
        mod_kev = False if eff.kev_neutralized else baseline_risk_input.kev
        mod_exposed = False if eff.exposure_mitigation else baseline_risk_input.internet_exposed

        res_risk_input = RiskCalculationRequest(
            asset_id=baseline_risk_input.asset_id,
            cve_id=baseline_risk_input.cve_id,
            cvss=mod_cvss,
            epss=mod_epss,
            kev=mod_kev,
            internet_exposed=mod_exposed,
            criticality=baseline_risk_input.criticality,
        )
        res_risk_res = calculate_risk(res_risk_input)

        # Apply likelihood mitigation factor if specified
        final_likelihood = max(0.0, res_risk_res.likelihood * (1.0 - eff.likelihood_mitigation_factor))
        final_risk_score = round(final_likelihood * res_risk_res.impact * 100.0, 2)
        estimated_risk_reduction = round(max(0.0, baseline_risk_res.risk_score - final_risk_score), 2)

        # Financial parameters modification
        mod_downtime = max(0.0, baseline_crq_input.downtime_hours * (1.0 - eff.downtime_reduction_pct))
        mod_ir = max(0.0, baseline_crq_input.incident_response_cost * (1.0 - eff.incident_response_reduction_pct))
        mod_rec = max(0.0, baseline_crq_input.recovery_cost * (1.0 - eff.recovery_cost_reduction_pct))
        mod_reg = max(0.0, baseline_crq_input.regulatory_legal_cost * (1.0 - eff.regulatory_reduction_pct))
        mod_cust = max(0.0, baseline_crq_input.customer_business_impact * (1.0 - eff.customer_impact_reduction_pct))

        res_crq_input = FinancialCRQInput(
            asset_id=baseline_crq_input.asset_id,
            cve_id=baseline_crq_input.cve_id,
            likelihood=final_likelihood,
            risk_score=final_risk_score,
            criticality=baseline_crq_input.criticality,
            revenue_loss_per_hour=baseline_crq_input.revenue_loss_per_hour,
            downtime_hours=mod_downtime,
            incident_response_cost=mod_ir,
            recovery_cost=mod_rec,
            regulatory_legal_cost=mod_reg,
            customer_business_impact=mod_cust,
        )
        res_crq_res = calculate_financial_crq(res_crq_input)
        estimated_eal_avoided = round(max(0.0, baseline_eal - res_crq_res.expected_annual_loss), 2)

        cost = ctrl.implementation_cost
        efficiency = round(estimated_eal_avoided / cost, 2) if cost > 0 else 0.0

        if not is_applicable:
            rec = f"Not applicable for asset type '{norm_asset_type}'."
        elif not dependencies_satisfied:
            rec = f"Prerequisite dependency missing: {', '.join(missing_deps)}."
        elif efficiency >= 2.0:
            rec = f"Highly Recommended: Strong financial ROI ({efficiency}x loss avoided per rupee)."
        elif efficiency >= 1.0:
            rec = f"Recommended: Positive ROI ({efficiency}x loss avoided per rupee)."
        else:
            rec = f"Selective: Moderate efficiency ({efficiency}x), prioritize based on risk tolerance."

        items.append(
            ControlAssessmentItem(
                control_id=ctrl.control_id,
                control_name=ctrl.control_name,
                is_applicable=is_applicable,
                dependencies_satisfied=dependencies_satisfied,
                missing_dependencies=missing_deps,
                implementation_cost=ctrl.implementation_cost,
                annual_cost=ctrl.annual_cost,
                estimated_risk_reduction=estimated_risk_reduction,
                estimated_eal_avoided=estimated_eal_avoided,
                efficiency_ratio=efficiency,
                recommendation=rec,
            )
        )

    return ControlAssessResponse(
        asset_id=request.asset_id or "AST-001",
        asset_type=norm_asset_type,
        baseline_risk_score=baseline_risk_res.risk_score,
        baseline_eal=baseline_eal,
        assessments=items,
        assessed_count=len(items),
    )
