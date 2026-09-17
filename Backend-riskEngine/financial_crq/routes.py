"""FastAPI Router for Financial Cyber Risk Quantification (CRQ) Endpoints

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Exposes REST endpoints to transform cyber risk metrics into modeled financial
loss representations (Downtime Loss, Total Loss Magnitude, Event Frequency, and EAL)
and generate structured inputs for DEV 2's Monte Carlo simulation engine.
"""

from fastapi import APIRouter, status
from .schemas import (
    FinancialCRQInput,
    FinancialCRQResult,
    FinancialCRQHealthResponse,
)
from .engine import calculate_financial_crq, FINANCIAL_MODEL_VERSION

router = APIRouter(prefix="/financial-crq", tags=["Financial CRQ"])


@router.post(
    "/calculate",
    response_model=FinancialCRQResult,
    status_code=status.HTTP_200_OK,
    summary="Quantify Financial Cyber Risk and Expected Annual Loss (EAL)",
    description="""
Transforms technical/operational cyber risk metrics and enterprise business cost parameters
into a modeled financial cyber-risk representation.

**Key Financial Computations:**
1. **Downtime Loss:** `revenue_loss_per_hour × downtime_hours`
2. **Total Loss Magnitude:** Sum of downtime, incident response, recovery, regulatory/legal, and customer impacts
3. **Loss Event Frequency:** Modeled annual frequency = `baseline_annual_frequency × likelihood`
4. **Expected Annual Loss (EAL):** `annual_event_frequency × total_loss_magnitude`
5. **Monte Carlo Bridge Payload:** Structured input prepared for downstream Monte Carlo simulation (DEV 2)

**Note on Modeling Assumptions:**
- Cyber risk likelihood is a modeled score from CVSS/EPSS/KEV indicators, not an empirical attack probability.
- All monetary and duration inputs are organization-provided estimates or synthetic demonstration values.
- EAL represents a modeled expectation under current assumptions, not a guaranteed prediction.
""",
)
def calculate_financial_crq_endpoint(
    request: FinancialCRQInput,
) -> FinancialCRQResult:
    """Calculate modeled financial loss components, event frequency, EAL, and Monte Carlo input."""
    return calculate_financial_crq(request)


@router.get(
    "/health",
    response_model=FinancialCRQHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check for the Financial CRQ module",
    description="Returns operational status and active Financial CRQ model version.",
)
def health_check() -> FinancialCRQHealthResponse:
    """Health check endpoint for Financial CRQ module monitoring."""
    return FinancialCRQHealthResponse(
        status="ok",
        module="financial-crq",
        model_version=FINANCIAL_MODEL_VERSION,
    )
