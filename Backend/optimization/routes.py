"""FastAPI Routes for Deterministic Cybersecurity Investment Optimization

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Provides endpoints:
- POST /optimization/run: Execute deterministic fixed-budget optimization with factor evaluation
- POST /optimization/before-after: Comparative before-and-after quantitative risk & loss analysis
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from controls.catalog import get_controls_by_ids
from decision.store import get_optimization

from .evaluator import evaluate_controls_portfolio
from .optimizer import run_optimization
from .schemas import (
    OPTIMIZATION_MODEL_VERSION,
    BeforeAfterRequest,
    BeforeAfterResponse,
    DeltaMetrics,
    OptimizationRunRequest,
    OptimizationRunResponse,
    RiskSnapshot,
)

logger = logging.getLogger("trinetra.optimization")

router = APIRouter(prefix="/optimization", tags=["Investment Optimization"])


@router.post(
    "/run",
    response_model=OptimizationRunResponse,
    summary="Execute Deterministic Investment Portfolio Optimization",
    description="Optimizes security controls under fixed budget constraint, applying factor modifications to calculate residual risk and EAL.",
)
def run_optimization_endpoint(request: OptimizationRunRequest):
    """Run deterministic knapsack/greedy portfolio optimization."""
    try:
        return run_optimization(request)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"[Optimization] Error executing optimization: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(exc)}",
        )


@router.post(
    "/before-after",
    response_model=BeforeAfterResponse,
    summary="Before-and-After Quantitative Portfolio Comparison",
    description="Provides granular before-and-after comparison of deterministic risk scores, Open FAIR loss metrics, and ROSI.",
)
def before_after_endpoint(request: BeforeAfterRequest):
    """Compare baseline versus post-control deployment states."""
    try:
        if request.run_parameters:
            opt_run = run_optimization(request.run_parameters)
            params = request.run_parameters
            controls_applied = opt_run.selected_controls
            opt_id = opt_run.optimization_id
        elif request.optimization_id:
            stored = get_optimization(request.optimization_id)
            if not stored:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Optimization '{request.optimization_id}' not found.",
                )
            params = OptimizationRunRequest(
                budget_limit=stored.budget_limit,
                asset_id="AST-001",
            )
            opt_run = run_optimization(params)
            controls_applied = opt_run.selected_controls
            opt_id = request.optimization_id
        else:
            # Default enterprise baseline evaluation
            params = OptimizationRunRequest(budget_limit=1800000.0)
            opt_run = run_optimization(params)
            controls_applied = opt_run.selected_controls
            opt_id = opt_run.optimization_id

        # Retrieve full control objects for evaluation
        selected_ctrl_objs = get_controls_by_ids(controls_applied)

        eval_result = evaluate_controls_portfolio(
            selected_controls=selected_ctrl_objs,
            asset_id=params.asset_id or "AST-001",
            cve_id=params.cve_id or "CVE-2026-1234",
            cvss=params.cvss if params.cvss is not None else 9.8,
            epss=params.epss if params.epss is not None else 0.82,
            kev=params.kev if params.kev is not None else True,
            internet_exposed=params.internet_exposed if params.internet_exposed is not None else True,
            criticality=params.criticality or "Critical",
            revenue_loss_per_hour=params.revenue_loss_per_hour or 250000.0,
            downtime_hours=params.downtime_hours or 8.0,
            incident_response_cost=params.incident_response_cost or 150000.0,
            recovery_cost=params.recovery_cost or 200000.0,
            regulatory_legal_cost=params.regulatory_legal_cost or 500000.0,
            customer_business_impact=params.customer_business_impact or 300000.0,
        )

        b_risk = eval_result.baseline_risk_response
        r_risk = eval_result.residual_risk_response
        b_crq = eval_result.baseline_crq_response
        r_crq = eval_result.residual_crq_response

        baseline_snapshot = RiskSnapshot(
            risk_score=b_risk.risk_score,
            risk_level=b_risk.risk_level.value if hasattr(b_risk.risk_level, "value") else str(b_risk.risk_level),
            likelihood=b_risk.likelihood,
            impact=b_risk.impact,
            expected_annual_loss=b_crq.expected_annual_loss,
            total_loss_magnitude=b_crq.total_loss_magnitude,
            annual_event_frequency=b_crq.annual_event_frequency,
            downtime_loss=b_crq.downtime_loss,
        )

        residual_snapshot = RiskSnapshot(
            risk_score=r_risk.risk_score,
            risk_level=r_risk.risk_level.value if hasattr(r_risk.risk_level, "value") else str(r_risk.risk_level),
            likelihood=r_risk.likelihood,
            impact=r_risk.impact,
            expected_annual_loss=r_crq.expected_annual_loss,
            total_loss_magnitude=r_crq.total_loss_magnitude,
            annual_event_frequency=r_crq.annual_event_frequency,
            downtime_loss=r_crq.downtime_loss,
        )

        total_cost = sum(c.implementation_cost for c in selected_ctrl_objs)
        loss_avoided = round(max(0.0, b_crq.expected_annual_loss - r_crq.expected_annual_loss), 2)
        risk_reduction = round(max(0.0, b_risk.risk_score - r_risk.risk_score), 2)

        risk_red_pct = round((risk_reduction / b_risk.risk_score * 100.0), 2) if b_risk.risk_score > 0 else 0.0
        loss_avoided_pct = (
            round((loss_avoided / b_crq.expected_annual_loss * 100.0), 2)
            if b_crq.expected_annual_loss > 0
            else 0.0
        )
        net_benefit = round(loss_avoided - total_cost, 2)
        rosi = round((loss_avoided - total_cost) / total_cost, 2) if total_cost > 0 else 0.0

        deltas = DeltaMetrics(
            risk_reduction_points=risk_reduction,
            risk_reduction_percent=risk_red_pct,
            financial_loss_avoided=loss_avoided,
            financial_loss_avoided_percent=loss_avoided_pct,
            total_investment_cost=round(total_cost, 2),
            net_annual_financial_benefit=net_benefit,
            return_on_security_investment=rosi,
        )

        return BeforeAfterResponse(
            optimization_id=opt_id,
            baseline=baseline_snapshot,
            residual=residual_snapshot,
            deltas=deltas,
            controls_applied=controls_applied,
            model_version=OPTIMIZATION_MODEL_VERSION,
        )

    except HTTPException:
        raise
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"[Optimization] Error in before-after endpoint: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Before-After analysis failed: {str(exc)}",
        )
