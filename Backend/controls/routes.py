"""FastAPI Routes for Security Controls Catalog & Assessment

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Provides endpoints:
- GET /controls: Browse security controls catalog with optional filtering
- POST /controls/assess: Quantitative assessment of controls against asset context
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from .catalog import (
    get_all_controls,
    get_controls_by_category,
    get_controls_for_asset_type,
)
from .models import (
    ControlAssessRequest,
    ControlAssessResponse,
    ControlCatalogResponse,
    ControlDependencyResolveRequest,
)

from .service import assess_controls

logger = logging.getLogger("trinetra.controls")

router = APIRouter(prefix="/controls", tags=["Controls Catalog"])


@router.get(
    "",
    response_model=ControlCatalogResponse,
    summary="Retrieve Security Controls Catalog",
    description="Browse all available cybersecurity controls with cost, dependencies, and risk reduction factor models.",
)
def list_controls(
    category: Optional[str] = Query(None, description="Filter controls by category (e.g. 'Identity & Access')"),
    asset_type: Optional[str] = Query(None, description="Filter controls applicable to an asset type (e.g. 'database')"),
):
    """Retrieve catalog controls with optional category or asset type filtering."""
    try:
        if category:
            controls = get_controls_by_category(category)
        elif asset_type:
            controls = get_controls_for_asset_type(asset_type)
        else:
            controls = get_all_controls()

        categories = sorted(list(set(c.category for c in get_all_controls())))

        return ControlCatalogResponse(
            total_controls=len(controls),
            categories=categories,
            controls=controls,
        )
    except Exception as exc:
        logger.error(f"[Controls] Error listing controls: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve controls catalog: {str(exc)}",
        )


@router.post(
    "/assess",
    response_model=ControlAssessResponse,
    summary="Assess Controls Against Asset Risk Context",
    description="Evaluate controls for applicability, prerequisite dependencies, and quantitative risk/EAL reduction.",
)
def assess_controls_endpoint(request: ControlAssessRequest):
    """Assess control candidates against specific asset risk and financial parameters."""
    try:
        return assess_controls(request)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"[Controls] Error assessing controls: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess controls: {str(exc)}",
        )


@router.post(
    "/resolve-dependencies",
    response_model=list,
    summary="Validate and Resolve Control Dependencies",
    description="Recursively validates prerequisite dependencies, detects cycles, enforces asset applicability, and computes single bundle costing.",
)
def resolve_dependencies_endpoint(request: ControlDependencyResolveRequest):
    """Validate and resolve requested control dependencies recursively."""
    try:
        from .catalog import get_control_by_id
        from .resolver import CircularDependencyError, ControlDependencyResolver

        # Resolve requested control objects
        controls_to_resolve = []
        for cid in request.requested_control_ids:
            found = get_control_by_id(cid)
            if found:
                controls_to_resolve.append(found)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Requested control '{cid}' was not found in catalog.",
                )

        resolver = ControlDependencyResolver(
            asset_type=request.asset_type or "web_application",
            budget_limit=request.budget_limit,
            existing_controls=request.existing_controls,
            allow_override=request.allow_override,
        )

        return resolver.resolve_all(controls_to_resolve)

    except CircularDependencyError as circ_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Circular control dependency detected.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Controls] Error resolving dependencies: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve control dependencies: {str(exc)}",
        )

