"""FastAPI Routes for Cybersecurity Data Ingestion and Enrichment

TRINETRA - SIH 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from schemas.vulnerability import (
    EnrichedVulnerabilityResponse,
    IngestionHealthResponse,
    IngestionStatusResponse,
    RiskEngineAssetJoinRequest,
    RiskEnginePayloadResponse,
    UnifiedVulnerabilityRecord,
    VulnerabilityListResponse,
)
from validation.vulnerability_validator import (
    InvalidCVEFormatError,
    InvalidMetricBoundsError,
    validate_cve_id,
)

logger = logging.getLogger("trinetra.api.ingestion")

router = APIRouter(tags=["Vulnerability Intelligence & Ingestion"])

# Global service instance placeholder (injected via dependency or lifespan)
_service_instance = None


def get_ingestion_service():
    """Dependency provider for IngestionService."""
    global _service_instance
    if _service_instance is None:
        from ingestion.service import IngestionService
        _service_instance = IngestionService()
    return _service_instance


def set_ingestion_service(service):
    """Set global service instance (used by main app and tests)."""
    global _service_instance
    _service_instance = service


# =====================================================================
# 1. INTERNAL ENRICHED CONTRACT FOR RISK ENGINE
# =====================================================================

@router.get(
    "/vulnerabilities/{cve_id}/enriched",
    response_model=EnrichedVulnerabilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Enriched Vulnerability Intelligence for Risk Engine",
    description="""
Retrieves normalized cybersecurity intelligence (CVSS, EPSS probability, CISA KEV status)
for a given CVE. Serves from local high-performance cache without calling external APIs on every request.
""",
)
async def get_enriched_vulnerability(
    cve_id: str,
    service=Depends(get_ingestion_service),
) -> EnrichedVulnerabilityResponse:
    """Retrieve normalized threat intelligence from cache/storage."""
    try:
        canonical_cve = validate_cve_id(cve_id, source="api")
        return await service.get_enriched_response(canonical_cve)
    except InvalidCVEFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_CVE_FORMAT", "message": str(exc)},
        )
    except Exception as exc:
        logger.error("[API] Error fetching enriched CVE %s: %s", cve_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ENRICHMENT_FAILED", "message": str(exc)},
        )


# =====================================================================
# 2. ASSET JOIN -> RISK ENGINE PAYLOAD CONSTRUCTOR
# =====================================================================

@router.post(
    "/vulnerabilities/risk-engine-payload",
    response_model=RiskEnginePayloadResponse,
    status_code=status.HTTP_200_OK,
    summary="Join Asset Context with Vulnerability Intelligence for Risk Engine",
    description="""
Combines asset operational context (asset_id, internet exposure, business criticality)
with cached/normalized threat intelligence (CVSS, EPSS, KEV) to construct the exact
input payload expected by the TRINETRA Risk Engine (POST /risk/calculate).
""",
)
async def construct_risk_engine_payload(
    request: RiskEngineAssetJoinRequest,
    service=Depends(get_ingestion_service),
) -> RiskEnginePayloadResponse:
    """Combine asset metadata with vulnerability threat intelligence."""
    try:
        return await service.join_asset_and_build_payload(request)
    except InvalidCVEFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_CVE_FORMAT", "message": str(exc)},
        )
    except Exception as exc:
        logger.error("[API] Asset join failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ASSET_JOIN_FAILED", "message": str(exc)},
        )


# =====================================================================
# 3. SINGLE CVE LIVE REFRESH (MODE A)
# =====================================================================

@router.post(
    "/ingestion/vulnerability/{cve_id}/refresh",
    response_model=UnifiedVulnerabilityRecord,
    status_code=status.HTTP_200_OK,
    summary="Force Live Refresh and Ingestion for a Single CVE",
    description="""
Forces a live query across official external sources (NVD 2.0, FIRST EPSS, CISA KEV),
validates the response, normalizes the unified record, updates local cache/storage,
and triggers downstream risk recalculation hooks if intelligence changed.
""",
)
async def refresh_single_vulnerability(
    cve_id: str,
    service=Depends(get_ingestion_service),
) -> UnifiedVulnerabilityRecord:
    """Mode A: Force live synchronization for a specific CVE."""
    try:
        canonical_cve = validate_cve_id(cve_id, source="api")
        return await service.get_or_enrich_cve(canonical_cve, force_refresh=True)
    except InvalidCVEFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_CVE_FORMAT", "message": str(exc)},
        )
    except Exception as exc:
        logger.error("[API] Live refresh failed for %s: %s", cve_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REFRESH_FAILED", "message": str(exc)},
        )


# =====================================================================
# 4. BULK SYNCHRONIZATION TRIGGER (MODE B)
# =====================================================================

@router.post(
    "/ingestion/bulk-sync",
    status_code=status.HTTP_200_OK,
    summary="Trigger On-Demand Bulk Synchronization",
    description="Refreshes the full CISA KEV catalog feed and synchronizes watchlist vulnerabilities.",
)
async def trigger_bulk_sync(
    service=Depends(get_ingestion_service),
):
    """Mode B: On-demand bulk synchronization trigger."""
    try:
        return await service.bulk_sync()
    except Exception as exc:
        logger.error("[API] Bulk sync failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "BULK_SYNC_FAILED", "message": str(exc)},
        )


# =====================================================================
# 5. HEALTH AND OBSERVABILITY STATUS
# =====================================================================

@router.get(
    "/ingestion/health",
    response_model=IngestionHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Active Health Check for All Upstream Intelligence Feeds",
    description="""
Actively probes network connectivity and reachability for NVD 2.0 API,
FIRST EPSS API, CISA KEV feed, and the local database storage.
""",
)
async def get_ingestion_health(
    service=Depends(get_ingestion_service),
) -> IngestionHealthResponse:
    """Active health probe for data integration adapters."""
    return await service.check_health()


@router.get(
    "/ingestion/status",
    response_model=IngestionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Ingestion Telemetry and Telemetry Statistics",
    description="Returns synchronization timestamps, processed/updated/failed counts, cache metrics, and uptime.",
)
def get_ingestion_status(
    service=Depends(get_ingestion_service),
) -> IngestionStatusResponse:
    """Telemetry report endpoint."""
    return service.get_status()


# =====================================================================
# 6. VULNERABILITY CATALOG QUERY / LISTING
# =====================================================================

@router.get(
    "/vulnerabilities",
    response_model=VulnerabilityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Stored Vulnerabilities",
    description="Paginated search and filter endpoint for cached vulnerability records.",
)
def list_vulnerabilities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    kev_only: bool = Query(False, description="Filter for CISA KEV listed vulnerabilities"),
    min_cvss: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum CVSS base score"),
    min_epss: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum EPSS probability"),
    search: Optional[str] = Query(None, description="Search term for CVE ID or description"),
    service=Depends(get_ingestion_service),
) -> VulnerabilityListResponse:
    """Query cached vulnerabilities."""
    summaries, total = service.storage.list_vulnerabilities(
        page=page,
        page_size=page_size,
        kev_only=kev_only,
        min_cvss=min_cvss,
        min_epss=min_epss,
        search=search,
    )
    return VulnerabilityListResponse(
        total=total,
        page=page,
        page_size=page_size,
        vulnerabilities=summaries,
    )
