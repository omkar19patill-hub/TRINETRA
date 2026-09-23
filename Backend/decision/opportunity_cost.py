"""Opportunity Cost Quantification & Trade-off Analysis Engine

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Decision Intelligence Layer

Quantifies the exact modeled risk reduction, capital outlay, and operational labor
sacrificed or gained when selecting one portfolio over another.

Enforces strictly neutral, objective language.
"""

from typing import List, Optional
from .schemas import (
    AlternativePortfolio,
    OpportunityCostComparison,
    OpportunityCostResponse,
    OptimizationResult,
)
from .alternatives import generate_alternative_portfolios


def calculate_opportunity_cost(
    optimization: OptimizationResult,
    target_portfolio_id: Optional[str] = None,
) -> OpportunityCostResponse:
    """Compute pairwise opportunity cost comparisons across all alternative portfolios."""
    alt_response = generate_alternative_portfolios(optimization)
    alternatives = alt_response.alternatives

    selected_id = target_portfolio_id or optimization.selected_portfolio_id or "portfolio-balanced-roi"
    selected_portfolio = next((p for p in alternatives if p.portfolio_id == selected_id), alternatives[0])

    currency = optimization.currency
    curr_sym = "₹" if currency == "INR" else "$"

    comparisons: List[OpportunityCostComparison] = []

    for alt in alternatives:
        if alt.portfolio_id == selected_portfolio.portfolio_id:
            continue

        reduction_diff = alt.risk_reduction - selected_portfolio.risk_reduction
        cost_diff = alt.total_cost - selected_portfolio.total_cost
        hours_diff = alt.workforce_hours - selected_portfolio.workforce_hours
        days_diff = alt.implementation_days - selected_portfolio.implementation_days

        selected_controls_set = set(selected_portfolio.selected_controls)
        alt_controls_set = set(alt.selected_controls)

        gained = sorted(list(alt_controls_set - selected_controls_set))
        sacrificed = sorted(list(selected_controls_set - alt_controls_set))

        if reduction_diff < 0:
            abs_red = abs(reduction_diff)
            narrative = (
                f"Under the same constraints, Portfolio '{alt.objective}' provides "
                f"{curr_sym}{abs_red:,.0f} less modeled reduction than Portfolio '{selected_portfolio.objective}'."
            )
            if cost_diff < 0:
                narrative += f" It requires {curr_sym}{abs(cost_diff):,.0f} less capital outlay."
            elif cost_diff > 0:
                narrative += f" It requires {curr_sym}{cost_diff:,.0f} higher capital outlay."
        elif reduction_diff > 0:
            narrative = (
                f"Under the same constraints, Portfolio '{alt.objective}' provides "
                f"{curr_sym}{reduction_diff:,.0f} more modeled reduction than Portfolio '{selected_portfolio.objective}'."
            )
            if cost_diff > 0:
                narrative += f" It requires {curr_sym}{cost_diff:,.0f} higher capital outlay and {hours_diff:+.0f} workforce hours."
        else:
            narrative = (
                f"Under the same constraints, Portfolio '{alt.objective}' provides equivalent "
                f"modeled reduction ({curr_sym}{alt.risk_reduction:,.0f}) compared to Portfolio '{selected_portfolio.objective}'."
            )

        comparisons.append(
            OpportunityCostComparison(
                compared_portfolio_id=alt.portfolio_id,
                compared_objective=alt.objective,
                selected_risk_reduction=selected_portfolio.risk_reduction,
                compared_risk_reduction=alt.risk_reduction,
                risk_reduction_difference=reduction_diff,
                cost_difference=cost_diff,
                workforce_hours_difference=hours_diff,
                implementation_days_difference=days_diff,
                tradeoff_narrative=narrative,
                controls_gained=gained,
                controls_sacrificed=sacrificed,
            )
        )

    summary = (
        f"Compared primary portfolio '{selected_portfolio.objective}' against {len(comparisons)} alternatives. "
        f"Trade-offs span from {curr_sym}{min((c.risk_reduction_difference for c in comparisons), default=0):,.0f} "
        f"to +{curr_sym}{max((c.risk_reduction_difference for c in comparisons), default=0):,.0f} in modeled reduction variance."
    )

    assumptions = [
        "All opportunity cost comparisons assume deterministic modeled risk reductions.",
        "Monetary values reflect Expected Annual Loss (EAL) delta under stated budget and workforce boundaries.",
        "Explanations use neutral, evidence-based comparative metrics without subjective qualification.",
    ]

    return OpportunityCostResponse(
        optimization_id=optimization.optimization_id,
        selected_portfolio_id=selected_portfolio.portfolio_id,
        selected_portfolio_name=selected_portfolio.objective,
        selected_risk_reduction=selected_portfolio.risk_reduction,
        selected_total_cost=selected_portfolio.total_cost,
        currency=currency,
        comparisons=comparisons,
        summary_statement=summary,
        assumptions=assumptions,
        data_source=getattr(optimization, "data_source", "actual_optimizer"),
        is_benchmark=getattr(optimization, "is_benchmark", False),
        model_version=getattr(optimization, "model_version", "DEC-1.0"),
        assessment_id=getattr(optimization, "assessment_id", None),
    )

