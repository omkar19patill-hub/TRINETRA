"""Pydantic Schemas for the Blockchain-Backed Decision Provenance Layer (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines structured data contracts for:
1. Decision Provenance Record Submissions
2. Immutable Blockchain Receipts
3. Cryptographic Verification Results & Integrity Audits
4. Health & Ledger State Diagnostics
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProvenanceRecordRequest(BaseModel):
    """Input payload for recording a completed assessment decision to the blockchain ledger."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    assessment_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier of the cyber risk assessment (e.g. CRQ-001, ASM-2026-042)",
            examples=["CRQ-001"],
        ),
    ]
    decision_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier of the optimal decision portfolio (e.g. OPT-001, OPT-BENCHMARK-001)",
            examples=["OPT-001"],
        ),
    ]
    model_version: Annotated[
        str,
        Field(
            default="1.0",
            min_length=1,
            description="Model and pipeline version identifier used during computation",
            examples=["1.0", "TRINETRA-v1.0"],
        ),
    ]
    timestamp: Annotated[
        Optional[str],
        Field(
            default=None,
            description="ISO-8601 UTC timestamp of the assessment. If omitted, server assigns current UTC time.",
            examples=["2026-09-20T13:00:00Z"],
        ),
    ]
    data_snapshot: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="Canonical input data snapshot (risk parameters, asset metadata, budget constraints). Used to auto-compute data_snapshot_hash if not explicitly provided.",
        ),
    ]
    decision_result: Annotated[
        Optional[Dict[str, Any]],
        Field(
            default=None,
            description="Canonical decision output (risk score, EAL, Monte Carlo P90/P99, selected portfolio controls). Used to auto-compute result_hash if not explicitly provided.",
        ),
    ]
    data_snapshot_hash: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Precomputed SHA-256 hash of the input data snapshot. Auto-computed from data_snapshot if omitted.",
            examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
        ),
    ]
    result_hash: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Precomputed SHA-256 hash of the quantitative decision outcome. Auto-computed from decision_result if omitted.",
            examples=["7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"],
        ),
    ]
    metadata: Annotated[
        Dict[str, Any],
        Field(
            default_factory=dict,
            description="Non-sensitive provenance metadata (e.g. organization_id, assessor_role, pipeline_stages).",
        ),
    ]


class ProvenanceRecord(BaseModel):
    """Immutable data structure representing an on-chain provenance entry."""

    model_config = ConfigDict(
        extra="ignore",
    )

    assessment_id: str = Field(description="Unique assessment identifier")
    decision_id: str = Field(description="Unique decision portfolio identifier")
    model_version: str = Field(description="Model/algorithm version")
    timestamp: str = Field(description="ISO-8601 UTC timestamp")
    data_snapshot_hash: str = Field(description="SHA-256 digest of input parameters")
    result_hash: str = Field(description="SHA-256 digest of decision outcome")
    canonical_hash: str = Field(description="Composite SHA-256 digest of the entire canonical provenance entry")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Non-sensitive metadata")


class BlockchainReceipt(BaseModel):
    """Cryptographic transaction receipt confirming inclusion in the blockchain ledger."""

    model_config = ConfigDict(
        extra="ignore",
    )

    status: str = Field(description="Status of the recording ('RECORDED', 'ALREADY_RECORDED')")
    tx_hash: str = Field(description="Unique cryptographic transaction hash (0x...)")
    block_height: int = Field(description="Block number containing this transaction")
    block_hash: str = Field(description="Cryptographic SHA-256 hash of the containing block")
    previous_block_hash: str = Field(description="Hash of the preceding block in the immutable chain")
    timestamp: str = Field(description="Timestamp of block creation")
    assessment_id: str = Field(description="Assessment identifier recorded")
    decision_id: str = Field(description="Decision identifier recorded")
    model_version: str = Field(description="Model version recorded")
    data_snapshot_hash: str = Field(description="SHA-256 hash of data snapshot recorded")
    result_hash: str = Field(description="SHA-256 hash of decision result recorded")
    canonical_hash: str = Field(description="Canonical composite hash recorded on-chain")
    provider: str = Field(description="Underlying blockchain provider ('LocalLedger', 'EVM')")


class BlockchainVerificationResponse(BaseModel):
    """Response returned when auditing the provenance and integrity of an assessment."""

    model_config = ConfigDict(
        extra="ignore",
    )

    verified: bool = Field(description="True if current local state matches on-chain provenance, False otherwise")
    assessment_id: str = Field(description="Assessment identifier audited")
    decision_id: Optional[str] = Field(default=None, description="Decision identifier audited")
    status: str = Field(
        description="Detailed verification status ('VERIFIED', 'INTEGRITY_MISMATCH', 'NOT_FOUND_ON_CHAIN', 'NOT_FOUND_LOCALLY')"
    )
    message: str = Field(description="Human-readable explanation of verification findings")
    on_chain_result_hash: Optional[str] = Field(default=None, description="Result hash recorded on-chain")
    computed_result_hash: Optional[str] = Field(default=None, description="Result hash recomputed from current local state")
    on_chain_snapshot_hash: Optional[str] = Field(default=None, description="Snapshot hash recorded on-chain")
    computed_snapshot_hash: Optional[str] = Field(default=None, description="Snapshot hash recomputed from current local state")
    canonical_hash: Optional[str] = Field(default=None, description="Composite canonical hash")
    block_height: Optional[int] = Field(default=None, description="Block height where record is anchored")
    block_hash: Optional[str] = Field(default=None, description="Block hash anchoring the record")
    tx_hash: Optional[str] = Field(default=None, description="Transaction hash on the ledger")
    recorded_at: Optional[str] = Field(default=None, description="Timestamp recorded on-chain")
    provider: Optional[str] = Field(default=None, description="Blockchain provider used")


class BlockchainHealthResponse(BaseModel):
    """Operational health status and ledger statistics of the blockchain provenance subsystem."""

    model_config = ConfigDict(
        extra="ignore",
    )

    status: str = Field(default="ok")
    module: str = Field(default="blockchain-provenance")
    provider: str = Field(description="Active blockchain provider implementation")
    model_version: str = Field(description="Active blockchain provenance schema version")
    chain_height: int = Field(description="Current height / number of blocks in the ledger")
    total_records: int = Field(description="Total count of recorded decision assessments")
    chain_valid: bool = Field(description="Cryptographic integrity verification of the entire block chain")
    last_block_hash: Optional[str] = Field(default=None, description="Hash of the latest block in the chain")


class TamperTestRequest(BaseModel):
    """Payload to simulate unauthorized modifications to local decision results for tamper-detection testing."""

    model_config = ConfigDict(
        extra="ignore",
    )

    tamper_type: Annotated[
        str,
        Field(
            default="modify_eal",
            description="Type of tamper simulation ('modify_eal', 'modify_portfolio', 'corrupt_hash', 'modify_snapshot')",
        ),
    ]
    custom_value: Annotated[
        Optional[Any],
        Field(
            default=None,
            description="Optional custom value to inject into local state",
        ),
    ]
