"""Alternative Portfolios Generator & Explainable Evidence Engine

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Decision Intelligence Layer

Generates structured alternative portfolios under varied strategic objectives:
1. Balanced ROI & Cost-Efficiency (Selected)
2. Maximum Modeled Risk Reduction
3. Cost-Constrained / Low Capital Outlay
4. Fast-Track Deployment / Low Operational Workforce
5. Critical Asset Coverage Focus

Generates deterministic, structured evidence without calling an LLM.
"""

from typing import Dict, List, Optional, Set, Tuple
from .schemas import (
    AlternativePortfolio,
    AlternativesResponse,
    CandidateControl,
    ControlExplanation,
    OptimizationResult,
)


def _compute_control_roi(ctrl: CandidateControl) -> float:
    """Calculate Return on Security Investment: (risk_reduction - cost) / cost."""
    if ctrl.cost <= 0:
        return 0.0
    return (ctrl.risk_reduction - ctrl.cost) / ctrl.cost


def _build_control_explanation(
    ctrl: CandidateControl,
    selected: bool,
    budget_limit: float,
    currency: str,
    rejection_reason: Optional[str] = None,
) -> ControlExplanation:
    """Construct deterministic, evidence-based bullet reasons for a control."""
    reasons: List[str] = []
    roi = _compute_control_roi(ctrl)
    curr_sym = "₹" if currency == "INR" else "$"

    if selected:
        reasons.append(f"High modeled benefit ({curr_sym}{ctrl.risk_reduction:,.0f} risk reduction)")
        reasons.append(f"Fits within budget (Cost: {curr_sym}{ctrl.cost:,.0f})")
        if ctrl.critical_assets_covered > 0:
            reasons.append(f"Applies to {ctrl.critical_assets_covered} critical assets")
        if ctrl.implementation_days <= 21:
            reasons.append(f"Rapid deployment timeframe ({ctrl.implementation_days} days)")
        if roi >= 0.5:
            reasons.append(f"High modeled cost-benefit ratio (ROI: {roi:.2f}x)")
    else:
        if rejection_reason:
            reasons.append(rejection_reason)
        else:
            if ctrl.cost > budget_limit:
                reasons.append(f"Standalone cost ({curr_sym}{ctrl.cost:,.0f}) exceeds total budget ceiling ({curr_sym}{budget_limit:,.0f})")
            else:
                reasons.append(f"Exceeds remaining capital allocation within {curr_sym}{budget_limit:,.0f} budget constraint")
            if roi < 0.8:
                reasons.append(f"Lower relative cost-efficiency (ROI: {roi:.2f}x) compared to selected alternatives")
            if ctrl.workforce_hours >= 150:
                reasons.append(f"High workforce requirement ({ctrl.workforce_hours:.0f} engineering hours)")
            if ctrl.implementation_days >= 35:
                reasons.append(f"Longer implementation timeline ({ctrl.implementation_days} days)")
        if not reasons:
            reasons.append("Marginal modeled risk reduction surpassed by higher-ranked candidate controls")

    friendly_name = ctrl.name.replace("Phishing-Resistant ", "").replace("Next-Gen ", "").replace("Automated ", "")

    return ControlExplanation(
        control=friendly_name,
        control_id=ctrl.control_id,
        selected=selected,
        cost=ctrl.cost,
        risk_reduction=ctrl.risk_reduction,
        reasons=reasons,
    )


def _solve_portfolio(
    portfolio_id: str,
    objective: str,
    sorted_controls: List[CandidateControl],
    budget_limit: float,
    baseline_risk: float,
    currency: str,
    all_candidate_controls: List[CandidateControl],
    is_selected: bool = False,
    max_days_filter: Optional[int] = None,
    max_hours_filter: Optional[float] = None,
) -> AlternativePortfolio:
    """Pack candidate controls greedily according to sorted priority order."""
    selected_ctrls: List[CandidateControl] = []
    current_cost = 0.0
    current_reduction = 0.0
    current_hours = 0.0
    max_days = 0

    eligible = [
        c for c in sorted_controls
        if (max_days_filter is None or c.implementation_days <= max_days_filter)
        and (max_hours_filter is None or c.workforce_hours <= max_hours_filter)
    ]

    for ctrl in eligible:
        if current_cost + ctrl.cost <= budget_limit:
            selected_ctrls.append(ctrl)
            current_cost += ctrl.cost
            current_reduction += ctrl.risk_reduction
            current_hours += ctrl.workforce_hours
            if ctrl.implementation_days > max_days:
                max_days = ctrl.implementation_days

    selected_ids = {c.control_id for c in selected_ctrls}
    residual = max(0.0, baseline_risk - current_reduction)
    roi = (current_reduction - current_cost) / current_cost if current_cost > 0 else 0.0

    explanations: List[ControlExplanation] = []
    for ctrl in all_candidate_controls:
        is_ctrl_sel = ctrl.control_id in selected_ids
        rejection_reason = None
        if not is_ctrl_sel:
            if max_days_filter and ctrl.implementation_days > max_days_filter:
                rejection_reason = f"Implementation timeline ({ctrl.implementation_days} days) exceeds portfolio filter ({max_days_filter} days)"
            elif max_hours_filter and ctrl.workforce_hours > max_hours_filter:
                rejection_reason = f"Workforce hours ({ctrl.workforce_hours:.0f} hrs) exceed portfolio limit ({max_hours_filter:.0f} hrs)"
            elif current_cost + ctrl.cost > budget_limit:
                curr_sym = "₹" if currency == "INR" else "$"
                rejection_reason = f"Fits neither remaining budget ({curr_sym}{max(0.0, budget_limit - current_cost):,.0f}) nor optimization ceiling ({curr_sym}{budget_limit:,.0f})"
        
        explanations.append(
            _build_control_explanation(
                ctrl=ctrl,
                selected=is_ctrl_sel,
                budget_limit=budget_limit,
                currency=currency,
                rejection_reason=rejection_reason,
            )
        )

    return AlternativePortfolio(
        portfolio_id=portfolio_id,
        objective=objective,
        total_cost=current_cost,
        risk_reduction=current_reduction,
        residual_risk=residual,
        workforce_hours=current_hours,
        implementation_days=max_days,
        selected_controls=[c.name for c in selected_ctrls],
        control_explanations=explanations,
        is_selected=is_selected,
        roi=round(roi, 2),
    )


def generate_alternative_portfolios(optimization: OptimizationResult) -> AlternativesResponse:
    """Generate structured alternative portfolios and transparent decision evidence."""
    if optimization.custom_alternatives and len(optimization.custom_alternatives) > 0:
        return AlternativesResponse(
            optimization_id=optimization.optimization_id,
            baseline_risk=optimization.baseline_risk,
            budget_limit=optimization.budget_limit,
            currency=optimization.currency,
            selected_portfolio_id=optimization.selected_portfolio_id,
            alternatives=optimization.custom_alternatives,
            decision_summary=f"Evaluated {len(optimization.custom_alternatives)} pre-configured alternative portfolios.",
        )

    controls = optimization.candidate_controls
    budget = optimization.budget_limit
    baseline_risk = optimization.baseline_risk
    currency = optimization.currency

    # 1. Balanced ROI
    by_roi = sorted(controls, key=lambda c: (c.risk_reduction / c.cost if c.cost > 0 else 0.0), reverse=True)
    portfolio_balanced = _solve_portfolio(
        portfolio_id="portfolio-balanced-roi",
        objective="Balanced ROI & Cost-Efficiency",
        sorted_controls=by_roi,
        budget_limit=budget,
        baseline_risk=baseline_risk,
        currency=currency,
        all_candidate_controls=controls,
        is_selected=True,
    )

    # 2. Maximum Risk Reduction
    by_reduction = sorted(controls, key=lambda c: c.risk_reduction, reverse=True)
    portfolio_max_reduction = _solve_portfolio(
        portfolio_id="portfolio-max-risk-reduction",
        objective="Maximum Modeled Risk Reduction",
        sorted_controls=by_reduction,
        budget_limit=budget,
        baseline_risk=baseline_risk,
        currency=currency,
        all_candidate_controls=controls,
        is_selected=False,
    )

    # 3. Cost-Constrained / Lean
    lean_budget = max(budget * 0.5, 500000.0)
    portfolio_lean = _solve_portfolio(
        portfolio_id="portfolio-cost-constrained",
        objective="Cost-Constrained / Low Capital Outlay",
        sorted_controls=by_roi,
        budget_limit=lean_budget,
        baseline_risk=baseline_risk,
        currency=currency,
        all_candidate_controls=controls,
        is_selected=False,
    )

    # 4. Fast-Track Deployment
    by_speed = sorted(controls, key=lambda c: (c.implementation_days, c.workforce_hours))
    portfolio_fast = _solve_portfolio(
        portfolio_id="portfolio-fast-track",
        objective="Fast-Track Deployment (<25 Days Implementation)",
        sorted_controls=by_speed,
        budget_limit=budget,
        baseline_risk=baseline_risk,
        currency=currency,
        all_candidate_controls=controls,
        is_selected=False,
        max_days_filter=28,
        max_hours_filter=120.0,
    )

    # 5. Critical Asset Coverage Focus
    by_critical = sorted(
        controls,
        key=lambda c: (c.critical_assets_covered, c.risk_reduction / c.cost if c.cost > 0 else 0.0),
        reverse=True,
    )
    portfolio_critical = _solve_portfolio(
        portfolio_id="portfolio-critical-assets",
        objective="Critical Asset Defense Priority",
        sorted_controls=by_critical,
        budget_limit=budget,
        baseline_risk=baseline_risk,
        currency=currency,
        all_candidate_controls=controls,
        is_selected=False,
    )

    alternatives = [
        portfolio_balanced,
        portfolio_max_reduction,
        portfolio_lean,
        portfolio_fast,
        portfolio_critical,
    ]

    curr_sym = "₹" if currency == "INR" else "$"
    summary = (
        f"Selected '{portfolio_balanced.portfolio_id}' achieving {curr_sym}{portfolio_balanced.risk_reduction:,.0f} "
        f"modeled risk reduction ({round((portfolio_balanced.risk_reduction/baseline_risk)*100, 1)}% reduction) "
        f"at a total cost of {curr_sym}{portfolio_balanced.total_cost:,.0f} within {curr_sym}{budget:,.0f} budget limit."
    )

    return AlternativesResponse(
        optimization_id=optimization.optimization_id,
        baseline_risk=baseline_risk,
        budget_limit=budget,
        currency=currency,
        selected_portfolio_id="portfolio-balanced-roi",
        alternatives=alternatives,
        decision_summary=summary,
    )
