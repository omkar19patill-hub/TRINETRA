"""FastAPI Router for Blockchain Decision Provenance Layer (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Exposes:
1. POST /blockchain/record: Anchors a completed risk/CRQ/optimization decision into the verifiable ledger.
2. GET /blockchain/verify/{assessment_id}: Audits local state against immutable on-chain cryptographic proof.
3. GET /blockchain/records: Lists registered decision provenance records.
4. GET /blockchain/health: Diagnostic health & chain validity check.
5. GET /blockchain/tester: Temporary interactive test console for verification demo.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from . import BLOCKCHAIN_MODEL_VERSION
from .hashing import (
    compute_composite_hash,
    compute_data_snapshot_hash,
    compute_result_hash,
)
from .provider import (
    BlockchainDuplicateRecordError,
    get_blockchain_provider,
)
from .schemas import (
    BlockchainHealthResponse,
    BlockchainReceipt,
    BlockchainVerificationResponse,
    ProvenanceRecord,
    ProvenanceRecordRequest,
    TamperTestRequest,
)
from .store import (
    get_assessment,
    list_assessments,
    reset_assessment,
    save_assessment,
    tamper_assessment,
)

router = APIRouter(prefix="/blockchain", tags=["Blockchain Decision Provenance"])

TESTER_HTML_PATH = Path(__file__).resolve().parent / "tester.html"


@router.post(
    "/record",
    response_model=BlockchainReceipt,
    status_code=status.HTTP_201_CREATED,
    summary="Record Completed Decision Provenance on Blockchain Ledger",
    description="""
Generates a canonical JSON representation of the completed risk + CRQ + Monte Carlo + Optimization decision,
calculates the cryptographic SHA-256 digests, and anchors an immutable provenance record onto the blockchain ledger.

**Strict Security Enforcement:**
- Sensitive financial CSVs, credentials, and full vulnerability tables are NEVER stored on-chain.
- Only SHA-256 hashes and non-sensitive provenance metadata are included in the block transaction.
""",
)
def record_decision_provenance(request: ProvenanceRecordRequest) -> BlockchainReceipt:
    """Record a decision hash on the blockchain ledger."""
    provider = get_blockchain_provider()

    # 1. Fetch or prepare local assessment context
    local_assessment = get_assessment(request.assessment_id)
    
    # 2. Determine snapshot and result data
    snapshot_data = request.data_snapshot or (local_assessment.get("data_snapshot") if local_assessment else {})
    result_data = request.decision_result or (local_assessment.get("decision_result") if local_assessment else {})

    # 3. Compute SHA-256 hashes canonically
    data_snapshot_hash = request.data_snapshot_hash or compute_data_snapshot_hash(snapshot_data)
    result_hash = request.result_hash or compute_result_hash(result_data)

    timestamp = request.timestamp or (local_assessment.get("timestamp") if local_assessment else None) or datetime.now(timezone.utc).isoformat()
    
    canonical_hash = compute_composite_hash(
        assessment_id=request.assessment_id,
        decision_id=request.decision_id,
        model_version=request.model_version or BLOCKCHAIN_MODEL_VERSION,
        timestamp=timestamp,
        data_snapshot_hash=data_snapshot_hash,
        result_hash=result_hash,
    )

    provenance_record = ProvenanceRecord(
        assessment_id=request.assessment_id,
        decision_id=request.decision_id,
        model_version=request.model_version or BLOCKCHAIN_MODEL_VERSION,
        timestamp=timestamp,
        data_snapshot_hash=data_snapshot_hash,
        result_hash=result_hash,
        canonical_hash=canonical_hash,
        metadata=request.metadata,
    )

    # 4. Save to local store if not already present
    if not local_assessment:
        save_assessment({
            "assessment_id": request.assessment_id,
            "decision_id": request.decision_id,
            "model_version": request.model_version or BLOCKCHAIN_MODEL_VERSION,
            "timestamp": timestamp,
            "data_snapshot": snapshot_data,
            "decision_result": result_data,
            "data_snapshot_hash": data_snapshot_hash,
            "result_hash": result_hash,
            "canonical_hash": canonical_hash,
            "is_tampered": False,
        })

    # 5. Anchor on Blockchain Provider
    try:
        receipt = provider.record_hash(provenance_record)
        return receipt
    except BlockchainDuplicateRecordError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.get(
    "/verify/{assessment_id}",
    response_model=BlockchainVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Decision Provenance & Cryptographic Integrity",
    description="""
Audits the integrity of a decision assessment by:
1. Loading the current local record and decision result.
2. Recomputing the canonical SHA-256 result hash and snapshot hash.
3. Comparing against the immutable on-chain record in the blockchain ledger.
4. Returning **`verified = true`** if intact or **`verified = false`** if tampered.
""",
)
def verify_decision_provenance(assessment_id: str) -> BlockchainVerificationResponse:
    """Verify local assessment result against the blockchain ledger."""
    provider = get_blockchain_provider()

    local_assessment = get_assessment(assessment_id)
    if not local_assessment:
        # Check if record exists on-chain even if local file is missing
        on_chain_rec = provider.get_record(assessment_id)
        if on_chain_rec:
            return BlockchainVerificationResponse(
                verified=False,
                assessment_id=assessment_id,
                decision_id=on_chain_rec.decision_id,
                status="NOT_FOUND_LOCALLY",
                message=f"Assessment '{assessment_id}' exists on-chain but was not found in the local decision store.",
                on_chain_result_hash=on_chain_rec.result_hash,
                on_chain_snapshot_hash=on_chain_rec.data_snapshot_hash,
                provider="LocalLedger",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment with ID '{assessment_id}' was not found locally or on-chain.",
        )

    # Recompute hashes from current local state
    if "decision_result" in local_assessment and local_assessment["decision_result"]:
        computed_result_hash = compute_result_hash(local_assessment["decision_result"])
    else:
        computed_result_hash = local_assessment.get("result_hash", "")

    if "data_snapshot" in local_assessment and local_assessment["data_snapshot"]:
        computed_snapshot_hash = compute_data_snapshot_hash(local_assessment["data_snapshot"])
    else:
        computed_snapshot_hash = local_assessment.get("data_snapshot_hash", "")

    # Perform verification on provider
    verification = provider.verify_hash(
        assessment_id=assessment_id,
        expected_result_hash=computed_result_hash,
        expected_snapshot_hash=computed_snapshot_hash,
    )

    return verification


@router.get(
    "/records",
    response_model=List[ProvenanceRecord],
    status_code=status.HTTP_200_OK,
    summary="List All Registered On-Chain Provenance Records",
    description="Returns all decision provenance records currently anchored in the blockchain ledger.",
)
def list_provenance_records() -> List[ProvenanceRecord]:
    """List all blockchain provenance records."""
    provider = get_blockchain_provider()
    return provider.list_records()


@router.get(
    "/receipts",
    response_model=List[BlockchainReceipt],
    status_code=status.HTTP_200_OK,
    summary="List All Transaction Receipts",
    description="Returns all cryptographic block transaction receipts generated by the blockchain provider.",
)
def list_blockchain_receipts() -> List[BlockchainReceipt]:
    """List all blockchain transaction receipts."""
    provider = get_blockchain_provider()
    return provider.list_receipts()


@router.get(
    "/health",
    response_model=BlockchainHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health & Cryptographic Chain Validation",
    description="Validates blockchain ledger continuity, block hashes, and total anchored assessments.",
)
def blockchain_health() -> BlockchainHealthResponse:
    """Return health status and ledger verification summary."""
    provider = get_blockchain_provider()
    return provider.get_health()


@router.post(
    "/tamper-test/{assessment_id}",
    status_code=status.HTTP_200_OK,
    summary="Tamper Simulation Test Utility",
    description="Simulates unauthorized modification of local decision data to verify that the blockchain layer detects integrity failure.",
)
def simulate_tamper_endpoint(
    assessment_id: str,
    request: Optional[TamperTestRequest] = None,
) -> Dict[str, Any]:
    """Simulate tampering on local assessment data for verification testing."""
    tamper_type = request.tamper_type if request else "modify_eal"
    custom_val = request.custom_value if request else None

    try:
        updated = tamper_assessment(assessment_id, tamper_type=tamper_type, custom_value=custom_val)
        return {
            "status": "TAMPERED_FOR_TESTING",
            "assessment_id": assessment_id,
            "tamper_type": tamper_type,
            "message": "Local decision record modified. Running GET /blockchain/verify will now detect an integrity mismatch.",
            "record": updated,
        }
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )


@router.post(
    "/reset-test/{assessment_id}",
    status_code=status.HTTP_200_OK,
    summary="Reset Tampered Test Assessment",
    description="Restores a tampered local assessment back to its original untampered state.",
)
def reset_tamper_endpoint(assessment_id: str) -> Dict[str, Any]:
    """Reset assessment back to original state."""
    restored = reset_assessment(assessment_id)
    if not restored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment '{assessment_id}' could not be restored.",
        )
    return {
        "status": "RESTORED",
        "assessment_id": assessment_id,
        "message": "Assessment restored to pristine original state.",
    }


@router.get(
    "/tester",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Temporary Decision Provenance Tester UI",
    description="Interactive single-page tester to record and verify decisions.",
)
def serve_tester_ui() -> HTMLResponse:
    """Serve the interactive HTML temporary tester."""
    if TESTER_HTML_PATH.exists():
        content = TESTER_HTML_PATH.read_text(encoding="utf-8")
        return HTMLResponse(content=content)
    return HTMLResponse(
        content="<h3>TRINETRA Decision Provenance Tester HTML not found.</h3>",
        status_code=status.HTTP_404_NOT_FOUND,
    )
