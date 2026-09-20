"""FastAPI Router for Decision Intelligence Layer Endpoints

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Decision Intelligence Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from . import DECISION_MODEL_VERSION
from .schemas import (
    AlternativePortfolio,
    AlternativesResponse,
    ControlExplanation,
    DecisionHealthResponse,
    MarginalBudgetResponse,
    OpportunityCostResponse,
    OptimizationResult,
)
from .alternatives import generate_alternative_portfolios
from .opportunity_cost import calculate_opportunity_cost
from .marginal_value import evaluate_marginal_budget
from .store import get_optimization, list_optimizations, save_optimization, store_count


router = APIRouter(prefix="/decision", tags=["Decision Intelligence"])


@router.get(
    "/health",
    response_model=DecisionHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check for the Decision Intelligence Layer",
    description="Returns operational status, model version, and count of active stored optimizations.",
)
def health_check() -> DecisionHealthResponse:
    """Health check endpoint for Decision Intelligence module monitoring."""
    return DecisionHealthResponse(
        status="ok",
        module="decision-intelligence",
        model_version=DECISION_MODEL_VERSION,
        seeded_optimizations=store_count(),
    )


@router.get(
    "/optimizations",
    response_model=List[OptimizationResult],
    status_code=status.HTTP_200_OK,
    summary="List all available optimization scenarios",
    description="Returns all registered enterprise optimization datasets and benchmark scenarios.",
)
def get_all_optimizations() -> List[OptimizationResult]:
    """List all registered optimizations in the store."""
    return list_optimizations()


@router.post(
    "/register",
    response_model=OptimizationResult,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new custom optimization scenario",
    description="Stores a custom OptimizationResult with candidate controls for Decision Intelligence analysis.",
)
def register_optimization(optimization: OptimizationResult) -> OptimizationResult:
    """Register or update an optimization scenario in memory."""
    save_optimization(optimization)
    return optimization


@router.get(
    "/{optimization_id}/alternatives",
    response_model=AlternativesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Structured Alternative Cyber Investment Portfolios",
    description="""
Evaluates and returns structured alternative investment portfolios:
1. **Balanced ROI & Cost-Efficiency** (Selected baseline)
2. **Maximum Risk Reduction**
3. **Cost-Constrained / Low Capital Outlay**
4. **Fast-Track Deployment (<25 Days rollout)**
5. **Critical Asset Coverage Focus**
""",
)
def get_alternatives(optimization_id: str) -> AlternativesResponse:
    """Return structured alternative portfolios for the requested optimization scenario."""
    optimization = get_optimization(optimization_id)
    if not optimization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization result with ID '{optimization_id}' was not found in the decision store.",
        )
    return generate_alternative_portfolios(optimization)


@router.get(
    "/{optimization_id}/opportunity-cost",
    response_model=OpportunityCostResponse,
    status_code=status.HTTP_200_OK,
    summary="Quantify Opportunity Cost Across Alternative Portfolios",
    description="""
Calculates modeled risk reduction, capital outlay, and engineering workforce sacrificed
by selecting one portfolio instead of another.
""",
)
def get_opportunity_cost(
    optimization_id: str,
    target_portfolio_id: Optional[str] = Query(
        None,
        description="Optional portfolio ID to treat as the baseline selected portfolio",
    ),
) -> OpportunityCostResponse:
    """Quantify modeled risk reduction sacrificed between portfolios."""
    optimization = get_optimization(optimization_id)
    if not optimization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization result with ID '{optimization_id}' was not found in the decision store.",
        )
    return calculate_opportunity_cost(optimization, target_portfolio_id)


@router.get(
    "/{optimization_id}/marginal-budget",
    response_model=MarginalBudgetResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Marginal Value of Additional Budget",
    description="""
Evaluates the incremental risk reduction unlocked across additional budget increments:
- **+₹5L** (+₹500,000)
- **+₹10L** (+₹1,000,000)
- **+₹25L** (+₹2,500,000)
""",
)
def get_marginal_budget(
    optimization_id: str,
    increments: Optional[str] = Query(
        None,
        description="Comma-separated custom budget increments (e.g. '500000,1000000,2500000' or '0')",
    ),
) -> MarginalBudgetResponse:
    """Evaluate marginal returns per rupee at incremental budget tiers."""
    optimization = get_optimization(optimization_id)
    if not optimization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization result with ID '{optimization_id}' was not found in the decision store.",
        )

    parsed_increments: Optional[List[float]] = None
    if increments is not None:
        try:
            parsed_increments = [float(x.strip()) for x in increments.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid increment format. Provide comma-separated numeric values (e.g. '500000,1000000,2500000').",
            )

    return evaluate_marginal_budget(optimization, parsed_increments)


@router.get(
    "/{optimization_id}/explanation",
    response_model=List[ControlExplanation],
    status_code=status.HTTP_200_OK,
    summary="Get Structured Control Selection & Rejection Explanations",
    description="Returns deterministic, structured evidence explaining why each candidate control was selected or rejected.",
)
def get_control_explanations(
    optimization_id: str,
    portfolio_id: Optional[str] = Query(
        None,
        description="Optional portfolio ID to explain (defaults to primary selected portfolio)",
    ),
) -> List[ControlExplanation]:
    """Return explainable evidence structures for all candidate controls."""
    optimization = get_optimization(optimization_id)
    if not optimization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization result with ID '{optimization_id}' was not found in the decision store.",
        )
    
    alt_response = generate_alternative_portfolios(optimization)
    target_id = portfolio_id or alt_response.selected_portfolio_id
    target_portfolio = next((p for p in alt_response.alternatives if p.portfolio_id == target_id), alt_response.alternatives[0])
    return target_portfolio.control_explanations or []
