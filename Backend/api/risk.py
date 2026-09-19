"""FastAPI Router for Risk Engine Endpoints

TRINETRA - SIH 2026

Handles HTTP request ingestion, delegates directly to the decoupled core Risk Engine,
and returns structured risk quantification and health status responses.
"""

from fastapi import APIRouter, status
from risk.schemas import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    HealthResponse,
)
from risk.engine import calculate_risk
from risk.constants import MODEL_VERSION

router = APIRouter(prefix="/risk", tags=["Risk Engine"])


@router.post(
    "/calculate",
    response_model=RiskCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Quantify Cyber Risk for an Asset-Vulnerability pair",
    description="""
Evaluates the deterministic risk score, categorical risk level, factor contributions,
and explainable risk drivers for a given vulnerability on a specific asset.

**Inputs:**
- **asset_id**: Unique identifier of the asset (e.g. `AST-001`)
- **cve_id**: CVE identifier (e.g. `CVE-2026-1234`)
- **cvss**: Base CVSS score [0.0 - 10.0]
- **epss**: EPSS exploitation probability [0.0 - 1.0]
- **kev**: CISA KEV catalog boolean flag
- **internet_exposed**: Asset exposure boolean flag
- **criticality**: Business criticality rating (`Critical`, `High`, `Medium`, `Low`)
""",
)
def calculate_risk_endpoint(
    request: RiskCalculationRequest,
) -> RiskCalculationResponse:
    """Calculate deterministic risk score and breakdown."""
    return calculate_risk(request)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check for the Risk Engine module",
    description="Returns operational status and active risk scoring model version.",
)
def health_check() -> HealthResponse:
    """Health check endpoint for module monitoring."""
    return HealthResponse(
        status="ok",
        module="risk-engine",
        model_version=MODEL_VERSION,
    )
