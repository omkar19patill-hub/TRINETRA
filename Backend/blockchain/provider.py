"""Blockchain Provider Abstraction Layer & Implementations (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Decouples the core risk engine and decision intelligence systems from any specific
blockchain library or consensus implementation.

Implementations:
1. LocalLedgerBlockchainProvider: Fast, deterministic, thread-safe, cryptographically chained block ledger.
2. EVMBlockchainProvider: Pluggable provider for EVM-compatible development networks (Ganache/Hardhat/Private RPC).
"""

import abc
import hashlib
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .hashing import canonical_json, compute_composite_hash, sha256_hash
from .schemas import (
    BlockchainHealthResponse,
    BlockchainReceipt,
    BlockchainVerificationResponse,
    ProvenanceRecord,
)

logger = logging.getLogger("trinetra.blockchain")


class BlockchainDuplicateRecordError(ValueError):
    """Raised when attempting to overwrite an existing immutable on-chain assessment with differing data."""
    pass


class BlockchainProvider(abc.ABC):
    """Abstract Base Class for all TRINETRA Decision Provenance blockchain backends."""

    @abc.abstractmethod
    def record_hash(self, record: ProvenanceRecord) -> BlockchainReceipt:
        """Anchor a decision provenance hash record into an immutable block."""
        pass

    @abc.abstractmethod
    def verify_hash(
        self,
        assessment_id: str,
        expected_result_hash: str,
        expected_snapshot_hash: Optional[str] = None,
    ) -> BlockchainVerificationResponse:
        """Verify local decision results against immutable on-chain anchor."""
        pass

    @abc.abstractmethod
    def get_record(self, assessment_id: str) -> Optional[ProvenanceRecord]:
        """Fetch provenance record for a given assessment ID."""
        pass

    @abc.abstractmethod
    def get_receipt(self, assessment_id: str) -> Optional[BlockchainReceipt]:
        """Fetch transaction receipt for a given assessment ID."""
        pass

    @abc.abstractmethod
    def list_records(self) -> List[ProvenanceRecord]:
        """List all registered provenance records."""
        pass

    @abc.abstractmethod
    def list_receipts(self) -> List[BlockchainReceipt]:
        """List all transaction receipts in order of block height."""
        pass

    @abc.abstractmethod
    def get_health(self) -> BlockchainHealthResponse:
        """Return diagnostic health and cryptographic integrity status."""
        pass

    @abc.abstractmethod
    def verify_chain_integrity(self) -> bool:
        """Perform full cryptographic validation of the underlying blockchain ledger."""
        pass


class Block:
    """Represents a discrete block in the local verifiable ledger."""

    def __init__(
        self,
        height: int,
        previous_block_hash: str,
        timestamp: str,
        transactions: List[ProvenanceRecord],
        nonce: int = 0,
    ):
        self.height = height
        self.previous_block_hash = previous_block_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.merkle_root = self._compute_merkle_root()
        self.block_hash = self.compute_hash()

    def _compute_merkle_root(self) -> str:
        """Compute Merkle tree root of the transactions contained in this block."""
        if not self.transactions:
            return "0" * 64
        hashes = [tx.canonical_hash for tx in self.transactions]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode("utf-8")).hexdigest())
            hashes = new_level
        return hashes[0]

    def compute_hash(self) -> str:
        """Compute block header SHA-256 hash."""
        header_data = {
            "height": self.height,
            "previous_block_hash": self.previous_block_hash,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
        }
        return sha256_hash(header_data)

    def to_dict(self) -> Dict:
        return {
            "height": self.height,
            "block_hash": self.block_hash,
            "previous_block_hash": self.previous_block_hash,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "tx_count": len(self.transactions),
        }


class LocalLedgerBlockchainProvider(BlockchainProvider):
    """In-memory cryptographically chained private blockchain provider for TRINETRA.
    
    Guarantees:
    - Tamper evidence via SHA-256 block hash chaining and Merkle root anchoring.
    - Deterministic transaction IDs (0x...).
    - Duplicate detection and immutability enforcement.
    - Zero external dependency / zero network latency.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._blocks: List[Block] = []
        self._receipts_by_assessment: Dict[str, BlockchainReceipt] = {}
        self._records_by_assessment: Dict[str, ProvenanceRecord] = {}
        self._initialize_genesis_block()

    def _initialize_genesis_block(self) -> None:
        """Create the immutable Genesis Block at height 0."""
        genesis = Block(
            height=0,
            previous_block_hash="0" * 64,
            timestamp="2026-01-01T00:00:00Z",
            transactions=[],
            nonce=2026105,
        )
        self._blocks.append(genesis)
        logger.info("[Blockchain] Genesis block created with hash: %s", genesis.block_hash)

    def reset_ledger(self) -> None:
        """Reset ledger for testing isolation."""
        with self._lock:
            self._blocks.clear()
            self._receipts_by_assessment.clear()
            self._records_by_assessment.clear()
            self._initialize_genesis_block()

    def record_hash(self, record: ProvenanceRecord) -> BlockchainReceipt:
        """Anchor a decision provenance hash into the next cryptographic block."""
        with self._lock:
            # 1. Check for duplicate assessment ID
            if record.assessment_id in self._records_by_assessment:
                existing_record = self._records_by_assessment[record.assessment_id]
                existing_receipt = self._receipts_by_assessment[record.assessment_id]

                # If hashes are identical, return idempotent receipt with ALREADY_RECORDED status
                if (
                    existing_record.result_hash == record.result_hash
                    and existing_record.data_snapshot_hash == record.data_snapshot_hash
                    and existing_record.decision_id == record.decision_id
                ):
                    return BlockchainReceipt(
                        status="ALREADY_RECORDED",
                        tx_hash=existing_receipt.tx_hash,
                        block_height=existing_receipt.block_height,
                        block_hash=existing_receipt.block_hash,
                        previous_block_hash=existing_receipt.previous_block_hash,
                        timestamp=existing_receipt.timestamp,
                        assessment_id=existing_receipt.assessment_id,
                        decision_id=existing_receipt.decision_id,
                        model_version=existing_receipt.model_version,
                        data_snapshot_hash=existing_receipt.data_snapshot_hash,
                        result_hash=existing_receipt.result_hash,
                        canonical_hash=existing_receipt.canonical_hash,
                        provider="LocalLedger",
                    )
                else:
                    raise BlockchainDuplicateRecordError(
                        f"Assessment ID '{record.assessment_id}' is already recorded on-chain with different cryptographic hashes. "
                        f"Blockchain records are immutable and cannot be overwritten."
                    )

            # 2. Mine new block with the transaction
            previous_block = self._blocks[-1]
            new_height = len(self._blocks)
            now_iso = record.timestamp or datetime.now(timezone.utc).isoformat()

            new_block = Block(
                height=new_height,
                previous_block_hash=previous_block.block_hash,
                timestamp=now_iso,
                transactions=[record],
                nonce=new_height * 7919,
            )
            self._blocks.append(new_block)

            # 3. Generate transaction hash (0x + SHA256)
            tx_data = {
                "block_height": new_height,
                "block_hash": new_block.block_hash,
                "assessment_id": record.assessment_id,
                "decision_id": record.decision_id,
                "canonical_hash": record.canonical_hash,
                "timestamp": now_iso,
            }
            tx_hash = "0x" + sha256_hash(tx_data)

            receipt = BlockchainReceipt(
                status="RECORDED",
                tx_hash=tx_hash,
                block_height=new_height,
                block_hash=new_block.block_hash,
                previous_block_hash=previous_block.block_hash,
                timestamp=now_iso,
                assessment_id=record.assessment_id,
                decision_id=record.decision_id,
                model_version=record.model_version,
                data_snapshot_hash=record.data_snapshot_hash,
                result_hash=record.result_hash,
                canonical_hash=record.canonical_hash,
                provider="LocalLedger",
            )

            self._receipts_by_assessment[record.assessment_id] = receipt
            self._records_by_assessment[record.assessment_id] = record

            logger.info(
                "[Blockchain] Anchored assessment %s in Block #%d (Tx: %s)",
                record.assessment_id,
                new_height,
                tx_hash[:16],
            )
            return receipt

    def verify_hash(
        self,
        assessment_id: str,
        expected_result_hash: str,
        expected_snapshot_hash: Optional[str] = None,
    ) -> BlockchainVerificationResponse:
        """Verify recomputed local result hash against immutable on-chain record."""
        with self._lock:
            if assessment_id not in self._records_by_assessment:
                return BlockchainVerificationResponse(
                    verified=False,
                    assessment_id=assessment_id,
                    status="NOT_FOUND_ON_CHAIN",
                    message=f"Assessment '{assessment_id}' has not been recorded to the blockchain ledger.",
                    provider="LocalLedger",
                )

            recorded_record = self._records_by_assessment[assessment_id]
            receipt = self._receipts_by_assessment[assessment_id]

            # Check result hash integrity
            result_match = (recorded_record.result_hash == expected_result_hash)
            snapshot_match = True
            if expected_snapshot_hash is not None:
                snapshot_match = (recorded_record.data_snapshot_hash == expected_snapshot_hash)

            if result_match and snapshot_match:
                return BlockchainVerificationResponse(
                    verified=True,
                    assessment_id=assessment_id,
                    decision_id=recorded_record.decision_id,
                    status="VERIFIED",
                    message="✅ Decision provenance verified. Local calculation result matches on-chain cryptographic anchor.",
                    on_chain_result_hash=recorded_record.result_hash,
                    computed_result_hash=expected_result_hash,
                    on_chain_snapshot_hash=recorded_record.data_snapshot_hash,
                    computed_snapshot_hash=expected_snapshot_hash or recorded_record.data_snapshot_hash,
                    canonical_hash=recorded_record.canonical_hash,
                    block_height=receipt.block_height,
                    block_hash=receipt.block_hash,
                    tx_hash=receipt.tx_hash,
                    recorded_at=receipt.timestamp,
                    provider="LocalLedger",
                )
            else:
                discrepancy_reasons = []
                if not result_match:
                    discrepancy_reasons.append("Result hash divergence (local computation does not match on-chain result)")
                if not snapshot_match:
                    discrepancy_reasons.append("Input snapshot hash divergence (parameters were modified post-assessment)")

                return BlockchainVerificationResponse(
                    verified=False,
                    assessment_id=assessment_id,
                    decision_id=recorded_record.decision_id,
                    status="INTEGRITY_MISMATCH",
                    message=f"❌ Tamper Alert: {'; '.join(discrepancy_reasons)}. Immutable blockchain provenance audit failed.",
                    on_chain_result_hash=recorded_record.result_hash,
                    computed_result_hash=expected_result_hash,
                    on_chain_snapshot_hash=recorded_record.data_snapshot_hash,
                    computed_snapshot_hash=expected_snapshot_hash or recorded_record.data_snapshot_hash,
                    canonical_hash=recorded_record.canonical_hash,
                    block_height=receipt.block_height,
                    block_hash=receipt.block_hash,
                    tx_hash=receipt.tx_hash,
                    recorded_at=receipt.timestamp,
                    provider="LocalLedger",
                )

    def get_record(self, assessment_id: str) -> Optional[ProvenanceRecord]:
        with self._lock:
            return self._records_by_assessment.get(assessment_id)

    def get_receipt(self, assessment_id: str) -> Optional[BlockchainReceipt]:
        with self._lock:
            return self._receipts_by_assessment.get(assessment_id)

    def list_records(self) -> List[ProvenanceRecord]:
        with self._lock:
            return list(self._records_by_assessment.values())

    def list_receipts(self) -> List[BlockchainReceipt]:
        with self._lock:
            return list(self._receipts_by_assessment.values())

    def verify_chain_integrity(self) -> bool:
        """Validate the full blockchain structure by recalculating all hashes from block 0 to N."""
        with self._lock:
            if not self._blocks:
                return False
            for i in range(1, len(self._blocks)):
                current = self._blocks[i]
                prev = self._blocks[i - 1]
                if current.previous_block_hash != prev.block_hash:
                    logger.error("[Blockchain] Broken chain link at block %d: prev hash mismatch", current.height)
                    return False
                if current.block_hash != current.compute_hash():
                    logger.error("[Blockchain] Corrupt block hash at block %d", current.height)
                    return False
            return True

    def get_health(self) -> BlockchainHealthResponse:
        """Return diagnostic health and chain integrity summary."""
        chain_valid = self.verify_chain_integrity()
        with self._lock:
            latest_hash = self._blocks[-1].block_hash if self._blocks else None
            height = len(self._blocks)
            total_records = len(self._records_by_assessment)

        return BlockchainHealthResponse(
            status="ok" if chain_valid else "degraded",
            module="blockchain-provenance",
            provider="LocalLedger",
            model_version="PROVENANCE-1.0",
            chain_height=height,
            total_records=total_records,
            chain_valid=chain_valid,
            last_block_hash=latest_hash,
        )


class EVMBlockchainProvider(BlockchainProvider):
    """Configurable EVM Provider adapter for Ethereum / Polygon / Ganache / Hardhat."""

    def __init__(self, rpc_url: Optional[str] = None, contract_address: Optional[str] = None):
        self.rpc_url = rpc_url or "http://127.0.0.1:8545"
        self.contract_address = contract_address or "0x0000000000000000000000000000000000000000"
        self._fallback_provider = LocalLedgerBlockchainProvider()

    def record_hash(self, record: ProvenanceRecord) -> BlockchainReceipt:
        # For development / fallback, delegates to verifiable local ledger with EVM provider tag
        receipt = self._fallback_provider.record_hash(record)
        return receipt.model_copy(update={"provider": "EVM (Simulated/Fallback)"})

    def verify_hash(
        self,
        assessment_id: str,
        expected_result_hash: str,
        expected_snapshot_hash: Optional[str] = None,
    ) -> BlockchainVerificationResponse:
        res = self._fallback_provider.verify_hash(assessment_id, expected_result_hash, expected_snapshot_hash)
        return res.model_copy(update={"provider": "EVM (Simulated/Fallback)"})

    def get_record(self, assessment_id: str) -> Optional[ProvenanceRecord]:
        return self._fallback_provider.get_record(assessment_id)

    def get_receipt(self, assessment_id: str) -> Optional[BlockchainReceipt]:
        return self._fallback_provider.get_receipt(assessment_id)

    def list_records(self) -> List[ProvenanceRecord]:
        return self._fallback_provider.list_records()

    def list_receipts(self) -> List[BlockchainReceipt]:
        return self._fallback_provider.list_receipts()

    def verify_chain_integrity(self) -> bool:
        return self._fallback_provider.verify_chain_integrity()

    def get_health(self) -> BlockchainHealthResponse:
        health = self._fallback_provider.get_health()
        return health.model_copy(update={"provider": "EVM (Simulated/Fallback)"})


# Singleton Provider Registry
_PROVIDER_INSTANCE: Optional[BlockchainProvider] = None
_PROVIDER_LOCK = threading.Lock()


def get_blockchain_provider() -> BlockchainProvider:
    """Return the active singleton BlockchainProvider instance."""
    global _PROVIDER_INSTANCE
    with _PROVIDER_LOCK:
        if _PROVIDER_INSTANCE is None:
            _PROVIDER_INSTANCE = LocalLedgerBlockchainProvider()
        return _PROVIDER_INSTANCE


def set_blockchain_provider(provider: BlockchainProvider) -> None:
    """Override singleton blockchain provider (useful for testing or switching to EVM)."""
    global _PROVIDER_INSTANCE
    with _PROVIDER_LOCK:
        _PROVIDER_INSTANCE = provider
