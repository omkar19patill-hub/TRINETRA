"""FastAPI Router for Monte Carlo Cyber Risk Simulation Endpoints

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Stochastic Uncertainty & Monte Carlo Simulation Endpoints
"""

from fastapi import APIRouter, status
from .schemas import (
    MonteCarloInput,
    MonteCarloResult,
    MonteCarloHealthResponse,
    SimulateFromCRQRequest,
)
from .simulator import (
    run_simulation,
    build_monte_carlo_input_from_crq,
    MONTE_CARLO_MODEL_VERSION,
)

router = APIRouter(prefix="/monte-carlo", tags=["Monte Carlo Simulation"])


@router.post(
    "/simulate",
    response_model=MonteCarloResult,
    status_code=status.HTTP_200_OK,
    summary="Execute Monte Carlo Cyber Risk Simulation",
    description="""
Executes stochastic Monte Carlo simulations (up to 100,000 iterations) across
uncertain event frequencies and loss magnitude parameters using triangular distributions.

**Returns:**
- Mean Annual Loss
- Percentiles: **P50** (Median), **P75**, **P90** (1-in-10 yr VaR), **P95**, **P99** (Catastrophic tail loss)
- Min and Max observed losses
- Compact histogram intervals for frontend visual charting
- Transparent modeling assumptions and explainability narratives
""",
)
def simulate_endpoint(
    request: MonteCarloInput,
) -> MonteCarloResult:
    """Execute stochastic Monte Carlo simulation from explicit (min, mode, max) parameter ranges."""
    return run_simulation(request)


@router.post(
    "/from-crq",
    response_model=MonteCarloResult,
    status_code=status.HTTP_200_OK,
    summary="Simulate Uncertainty Directly from Financial CRQ Inputs",
    description="""
Transforms DEV 1's deterministic Financial CRQ input into stochastic parameter ranges
using configurable spread multipliers, then executes Monte Carlo simulation.
""",
)
def simulate_from_crq_endpoint(
    request: SimulateFromCRQRequest,
) -> MonteCarloResult:
    """Convenience bridge endpoint connecting Financial CRQ inputs to Monte Carlo simulation."""
    mc_input = build_monte_carlo_input_from_crq(
        crq_input=request.crq_input,
        iterations=request.iterations,
        seed=request.seed,
        frequency_spread_min=request.frequency_spread_min,
        frequency_spread_max=request.frequency_spread_max,
        cost_spread_min=request.cost_spread_min,
        cost_spread_max=request.cost_spread_max,
    )
    return run_simulation(mc_input)


@router.get(
    "/health",
    response_model=MonteCarloHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check for Monte Carlo Simulation module",
    description="Returns operational status and active Monte Carlo model version.",
)
def health_check() -> MonteCarloHealthResponse:
    """Health check endpoint for Monte Carlo module monitoring."""
    return MonteCarloHealthResponse(
        status="ok",
        module="monte-carlo",
        model_version=MONTE_CARLO_MODEL_VERSION,
    )
