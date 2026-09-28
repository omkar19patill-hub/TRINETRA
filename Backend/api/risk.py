"""FastAPI Router for Risk Engine Endpoints

TRINETRA - SIH 2026

Handles HTTP request ingestion, delegates directly to the decoupled core Risk Engine,
and returns structured risk quantification and health status responses.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from risk.schemas import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    HealthResponse,
    AssessmentBatchCreate,
    AssessmentBatchResponse,
    RiskSnapshotResponse,
)
from risk.engine import calculate_risk
from risk.constants import MODEL_VERSION
from risk.storage import AssessmentStorage, get_assessment_storage

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


@router.post(
    "/assessment-batch",
    response_model=AssessmentBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Persist Bulk Assessment batch, asset results, and computed risk snapshot",
    description="""
Persists an assessment batch with individual asset results and generates an aggregate
portfolio risk snapshot in the persistent SQLite database.
""",
)
def save_assessment_batch_endpoint(
    request: AssessmentBatchCreate,
    storage: AssessmentStorage = Depends(get_assessment_storage),
) -> AssessmentBatchResponse:
    """Persist bulk assessment batch and auto-compute portfolio snapshot."""
    return storage.save_batch(request)


@router.get(
    "/history",
    response_model=List[RiskSnapshotResponse],
    status_code=status.HTTP_200_OK,
    summary="Get historical portfolio risk snapshots in chronological order",
    description="""
Returns persisted risk snapshots in chronological order (oldest to newest by default).
Supports optional `limit` (default 50) and `order` (`asc` or `desc`).
""",
)
def get_risk_history_endpoint(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of historical snapshots to return"),
    order: str = Query("asc", description="Sort order: 'asc' for chronological, 'desc' for reverse chronological"),
    storage: AssessmentStorage = Depends(get_assessment_storage),
) -> List[RiskSnapshotResponse]:
    """Retrieve historical portfolio risk snapshots in chronological order."""
    snapshots = storage.list_snapshots(limit=limit, order=order)
    return [RiskSnapshotResponse(**s) for s in snapshots]


@router.get(
    "/latest",
    response_model=RiskSnapshotResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the most recent portfolio risk snapshot",
    description="""
Returns the most recent persisted risk snapshot.
Returns HTTP 404 if no snapshots exist in the database.
""",
)
def get_latest_risk_snapshot_endpoint(
    storage: AssessmentStorage = Depends(get_assessment_storage),
) -> RiskSnapshotResponse:
    """Retrieve the newest risk snapshot or 404 if no snapshots exist."""
    snapshot = storage.get_latest_snapshot()
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk snapshots found.",
        )
    return RiskSnapshotResponse(**snapshot)


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

