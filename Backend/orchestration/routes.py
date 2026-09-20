"""FastAPI Router for Continuous Re-Optimization Orchestration (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Exposes:
- POST /reoptimize & POST /orchestration/reoptimize: Trigger end-to-end continuous re-optimization.
- POST /recalculate/{asset_id} & POST /orchestration/recalculate/{asset_id}: Target specific asset.
- GET /orchestration/assets: List tracked enterprise assets and live states.
- GET /orchestration/health: Health check and diagnostic metrics.
- POST /orchestration/reset/{asset_id}: Reset asset state to initial benchmark.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Path, status

from . import ORCHESTRATION_MODEL_VERSION
from .schemas import (
    OrchestrationHealthResponse,
    ReoptimizeRequest,
    ReoptimizeResponse,
)
from .service import run_continuous_reoptimization
from .state import (
    get_asset_state,
    get_reoptimization_counter,
    list_asset_states,
    reset_asset_state,
)

router = APIRouter(tags=["Continuous Re-Optimization"])


@router.post(
    "/reoptimize",
    response_model=ReoptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Continuous Cyber Risk Re-Optimization",
    description="""
Executes continuous automated recalculation across:
1. **Affected Asset Identification & Threat Delta Detection**
2. **Deterministic Cyber Risk Scoring (`/risk`)**
3. **Financial CRQ & Expected Annual Loss Modeling (`/financial-crq`)**
4. **Stochastic Monte Carlo Uncertainty Simulation (`/monte-carlo`)**
5. **Cybersecurity Control Portfolio Optimization (`/decision`)**
6. **Decision Delta Analysis (Risk, P95, Controls, Costs)**
7. **Optional Immutable Decision Provenance Anchoring (`/blockchain`)**
""",
)
@router.post(
    "/orchestration/reoptimize",
    response_model=ReoptimizeResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def reoptimize_endpoint(request: ReoptimizeRequest) -> ReoptimizeResponse:
    """Run full automated re-optimization pipeline on modified risk/threat parameters."""
    return run_continuous_reoptimization(request)


@router.post(
    "/recalculate/{asset_id}",
    response_model=ReoptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Recalculate & Re-Optimize for a Specific Asset",
    description="Trigger targeted re-optimization for a specific enterprise asset.",
)
@router.post(
    "/orchestration/recalculate/{asset_id}",
    response_model=ReoptimizeResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def recalculate_asset_endpoint(
    asset_id: str = Path(..., description="Target asset identifier (e.g. AST-001)"),
    request: Optional[ReoptimizeRequest] = None,
) -> ReoptimizeResponse:
    """Trigger targeted recalculation for an asset."""
    req = request or ReoptimizeRequest(asset_id=asset_id)
    req.asset_id = asset_id
    return run_continuous_reoptimization(req)


@router.get(
    "/orchestration/assets",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List Tracked Enterprise Asset Inventory",
    description="Returns live contextual states of all enterprise assets being continuously monitored.",
)
def list_assets_endpoint() -> List[Dict[str, Any]]:
    """List tracked enterprise assets."""
    return list_asset_states()


@router.get(
    "/orchestration/health",
    response_model=OrchestrationHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check for Continuous Re-Optimization Layer",
    description="Returns operational status, model version, and total re-optimizations executed.",
)
def orchestration_health() -> OrchestrationHealthResponse:
    """Health check endpoint for continuous re-optimization."""
    assets = list_asset_states()
    return OrchestrationHealthResponse(
        status="ok",
        module="continuous-reoptimization",
        version=ORCHESTRATION_MODEL_VERSION,
        tracked_assets_count=len(assets),
        total_reoptimizations_executed=get_reoptimization_counter(),
    )


@router.post(
    "/orchestration/reset/{asset_id}",
    status_code=status.HTTP_200_OK,
    summary="Reset Asset State to Baseline",
    description="Restores an asset to its pristine initial benchmark state.",
)
def reset_asset_endpoint(asset_id: str) -> Dict[str, Any]:
    """Reset asset state back to original baseline."""
    res = reset_asset_state(asset_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found in registry.",
        )
    return {
        "status": "RESET_COMPLETE",
        "asset_id": asset_id,
        "state": res.to_dict(),
    }
