"""Marginal Budget Sensitivity & Incremental Value Engine

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Decision Intelligence Layer

Evaluates marginal risk reduction when additional budget (+₹5L, +₹10L, +₹25L, or custom increments)
is allocated to the security program.
"""

from typing import List, Optional
from .schemas import (
    CandidateControl,
    MarginalBudgetEvaluation,
    MarginalBudgetResponse,
    OptimizationResult,
)


def _solve_optimal_selection(
    controls: List[CandidateControl],
    budget_limit: float,
) -> tuple[float, float, List[CandidateControl]]:
    """Greedily select controls optimizing ROI within the provided budget ceiling."""
    sorted_ctrls = sorted(
        controls,
        key=lambda c: (c.risk_reduction / c.cost if c.cost > 0 else 0.0),
        reverse=True,
    )
    selected: List[CandidateControl] = []
    total_cost = 0.0
    total_reduction = 0.0

    for c in sorted_ctrls:
        if total_cost + c.cost <= budget_limit:
            selected.append(c)
            total_cost += c.cost
            total_reduction += c.risk_reduction

    return total_cost, total_reduction, selected


def evaluate_marginal_budget(
    optimization: OptimizationResult,
    additional_budgets: Optional[List[float]] = None,
) -> MarginalBudgetResponse:
    """Evaluate incremental risk reduction and marginal efficiency across budget increments."""
    if additional_budgets is None or len(additional_budgets) == 0:
        additional_budgets = [500000.0, 1000000.0, 2500000.0]

    base_budget = optimization.budget_limit
    controls = optimization.candidate_controls
    currency = optimization.currency
    curr_sym = "₹" if currency == "INR" else "$"

    _, base_reduction, base_selected = _solve_optimal_selection(controls, base_budget)
    base_selected_ids = {c.control_id for c in base_selected}

    evaluations: List[MarginalBudgetEvaluation] = []
    marginal_rates: List[float] = []

    for add_budget in additional_budgets:
        if add_budget <= 0.0:
            evaluations.append(
                MarginalBudgetEvaluation(
                    additional_budget=0.0,
                    additional_risk_reduction=0.0,
                    marginal_reduction_per_rupee=0.0,
                    total_budget=base_budget,
                    total_risk_reduction=base_reduction,
                    additional_controls_selected=[],
                    efficiency_assessment="Baseline Budget (No Marginal Increase)",
                    explanation="Zero additional budget added. Modeled risk reduction remains at baseline.",
                )
            )
            continue

        new_budget = base_budget + add_budget
        _, new_reduction, new_selected = _solve_optimal_selection(controls, new_budget)

        delta_reduction = max(0.0, new_reduction - base_reduction)
        marginal_rate = delta_reduction / add_budget if add_budget > 0 else 0.0
        marginal_rates.append(marginal_rate)

        new_controls = [c.name for c in new_selected if c.control_id not in base_selected_ids]

        if marginal_rate >= 1.2:
            efficiency = f"High Marginal Return ({marginal_rate:.2f}x)"
        elif marginal_rate >= 0.8:
            efficiency = f"Moderate Marginal Return ({marginal_rate:.2f}x)"
        elif marginal_rate > 0.0:
            efficiency = f"Diminishing Marginal Return ({marginal_rate:.2f}x)"
        else:
            efficiency = "Zero Additional Benefit (Candidate Pool Exhausted / Budget Insufficient for Next Tier)"

        if new_controls:
            explanation = (
                f"Adding {curr_sym}{add_budget:,.0f} enables {', '.join(new_controls)}, "
                f"yielding an additional {curr_sym}{delta_reduction:,.0f} in modeled risk reduction "
                f"({marginal_rate:.2f} reduction per rupee invested)."
            )
        else:
            explanation = (
                f"Adding {curr_sym}{add_budget:,.0f} does not unlock an additional candidate control "
                f"due to individual control cost thresholds."
            )

        evaluations.append(
            MarginalBudgetEvaluation(
                additional_budget=add_budget,
                additional_risk_reduction=delta_reduction,
                marginal_reduction_per_rupee=round(marginal_rate, 4),
                total_budget=new_budget,
                total_risk_reduction=new_reduction,
                additional_controls_selected=new_controls,
                efficiency_assessment=efficiency,
                explanation=explanation,
            )
        )

    diminishing_returns = False
    if len(marginal_rates) >= 2:
        diminishing_returns = all(
            marginal_rates[i] >= marginal_rates[i + 1]
            for i in range(len(marginal_rates) - 1)
        )

    positive_evals = [e for e in evaluations if e.additional_budget > 0]
    if positive_evals:
        best_eval = max(positive_evals, key=lambda e: e.marginal_reduction_per_rupee)
        if best_eval.marginal_reduction_per_rupee > 0:
            rec = (
                f"An incremental budget of +{curr_sym}{best_eval.additional_budget:,.0f} delivers the highest "
                f"marginal efficiency at {best_eval.marginal_reduction_per_rupee:.2f} reduction per rupee, "
                f"unlocking {', '.join(best_eval.additional_controls_selected) or 'higher-tier controls'}."
            )
        else:
            rec = "Current baseline budget captures all feasible high-ROI candidate controls."
    else:
        rec = "Baseline budget maintained without incremental capital allocation."

    return MarginalBudgetResponse(
        optimization_id=optimization.optimization_id,
        base_budget=base_budget,
        base_risk_reduction=base_reduction,
        currency=currency,
        evaluations=evaluations,
        diminishing_returns_observed=diminishing_returns,
        recommendation=rec,
        data_source=getattr(optimization, "data_source", "actual_optimizer"),
        is_benchmark=getattr(optimization, "is_benchmark", False),
        model_version=getattr(optimization, "model_version", "DEC-1.0"),
        assessment_id=getattr(optimization, "assessment_id", None),
    )

