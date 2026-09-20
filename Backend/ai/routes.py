"""FastAPI Router for Explainable AI Layer Endpoints

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Explainable AI Endpoints
"""

from fastapi import APIRouter, status
from . import AI_EXPLAIN_VERSION
from .schemas import (
    AIExplanationRequest,
    AIExplanationResponse,
    AIHealthResponse,
    StructuredContext,
)
from .engine import (
    explain_optimization_context,
    explain_risk_context,
    explain_scenario_context,
    query_general_explanation,
)


router = APIRouter(prefix="/ai", tags=["Explainable AI"])


@router.get(
    "/health",
    response_model=AIHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check for the Explainable AI Layer",
    description="Returns operational status, model version, and grounding enforcement status.",
)
def health_check() -> AIHealthResponse:
    """Health check endpoint for Explainable AI module monitoring."""
    return AIHealthResponse(
        status="ok",
        module="explainable-ai",
        model_version=AI_EXPLAIN_VERSION,
        grounding_enforced=True,
    )


@router.post(
    "/explain-risk",
    response_model=AIExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Explain Asset Cyber Risk, Financial CRQ, and Monte Carlo Uncertainty",
    description="""
Generates an executive, board-ready natural-language explanation of an asset's cyber risk,
Expected Annual Loss (EAL), downtime outage costs, and stochastic Monte Carlo tail distributions.

**Strict Grounding Rule:**
The explanation is strictly derived from the provided `context` object. The AI engine does NOT
invent new financial losses, risk scores, or probability distributions.
""",
)
def explain_risk_endpoint(request: AIExplanationRequest) -> AIExplanationResponse:
    """Explain asset cyber risk and financial exposures."""
    return explain_risk_context(request.context, request.prompt)


@router.post(
    "/explain-optimization",
    response_model=AIExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Explain Portfolio Selection, Control Rationale, and Trade-offs",
    description="""
Explains why specific controls were selected (e.g. "Why was MFA selected?"), why candidate
controls were rejected (e.g. "Why was EDR rejected?"), and the opportunity costs across alternative portfolios.
""",
)
def explain_optimization_endpoint(request: AIExplanationRequest) -> AIExplanationResponse:
    """Explain portfolio optimization and control selection rationale."""
    return explain_optimization_context(request.context, request.prompt)


@router.post(
    "/explain-scenario",
    response_model=AIExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Explain Budget Sensitivity and Scenario Expansions",
    description="""
Explains what happens under modified capital bounds (e.g. "What happens if the budget is ₹25L?"),
highlighting newly unlocked controls, incremental risk reduction, and marginal efficiency per rupee.
""",
)
def explain_scenario_endpoint(request: AIExplanationRequest) -> AIExplanationResponse:
    """Explain budget scenarios and marginal investment value."""
    return explain_scenario_context(request.context, request.prompt)


@router.post(
    "/query",
    response_model=AIExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Flexible Natural-Language Grounded Query Engine",
    description="""
Accepts arbitrary natural-language cybersecurity governance questions and routes them
against the unified structured context object with strict anti-hallucination guarantees.
""",
)
def query_ai_endpoint(request: AIExplanationRequest) -> AIExplanationResponse:
    """Answer natural language inquiries grounded in structured context."""
    return query_general_explanation(request)
