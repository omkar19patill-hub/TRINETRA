"""Comprehensive Automated Test Suite for Blockchain Decision Provenance (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Covers:
1. Decision Provenance Record Creation & Blockchain Receipt Verification
2. Tamper-Evident Verification (Untampered -> Verified = True)
3. Modified Decision Result Detection (Tampered -> Verified = False & INTEGRITY_MISMATCH)
4. Duplicate Assessment Handling (Idempotent replay vs conflicting overwrite rejection)
5. Sensitive Data Exclusion (Guarantee no raw CSVs/secrets on-chain)
6. Cryptographic Chain & Block Header Verification
7. Tester UI Endpoint Delivery
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from blockchain import BLOCKCHAIN_MODEL_VERSION
from blockchain.provider import (
    BlockchainDuplicateRecordError,
    LocalLedgerBlockchainProvider,
    get_blockchain_provider,
    set_blockchain_provider,
)
from blockchain.store import (
    get_assessment,
    reset_assessment,
    save_assessment,
    seed_benchmark_assessments,
    tamper_assessment,
)
from blockchain.hashing import (
    canonical_json,
    compute_composite_hash,
    compute_data_snapshot_hash,
    compute_result_hash,
    sanitize_data,
    sha256_hash,
)


@pytest.fixture(autouse=True)
def reset_blockchain_state():
    """Reset blockchain ledger and local assessment store before each test."""
    fresh_provider = LocalLedgerBlockchainProvider()
    set_blockchain_provider(fresh_provider)
    seed_benchmark_assessments()
    yield


def test_blockchain_health_endpoint():
    """Verify GET /blockchain/health returns operational status, model version, and valid chain state."""
    with TestClient(app) as client:
        response = client.get("/blockchain/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "blockchain-provenance"
        assert data["provider"] == "LocalLedger"
        assert data["model_version"] == BLOCKCHAIN_MODEL_VERSION
        assert data["chain_height"] >= 1  # Genesis block
        assert data["chain_valid"] is True
        assert data["total_records"] == 0


def test_record_decision_provenance():
    """Verify POST /blockchain/record creates a valid block transaction receipt."""
    with TestClient(app) as client:
        payload = {
            "assessment_id": "CRQ-001",
            "decision_id": "OPT-001",
            "model_version": "1.0",
        }
        response = client.post("/blockchain/record", json=payload)
        assert response.status_code == 201
        receipt = response.json()

        assert receipt["status"] == "RECORDED"
        assert receipt["assessment_id"] == "CRQ-001"
        assert receipt["decision_id"] == "OPT-001"
        assert receipt["block_height"] == 1
        assert receipt["tx_hash"].startswith("0x")
        assert len(receipt["block_hash"]) == 64
        assert len(receipt["previous_block_hash"]) == 64
        assert len(receipt["result_hash"]) == 64
        assert len(receipt["data_snapshot_hash"]) == 64
        assert len(receipt["canonical_hash"]) == 64
        assert receipt["provider"] == "LocalLedger"


def test_verify_untampered_decision():
    """Verify GET /blockchain/verify/{assessment_id} returns verified=True for intact assessment."""
    with TestClient(app) as client:
        # 1. Record decision
        record_res = client.post("/blockchain/record", json={"assessment_id": "CRQ-001", "decision_id": "OPT-001"})
        assert record_res.status_code == 201
        receipt = record_res.json()

        # 2. Verify decision
        verify_res = client.get("/blockchain/verify/CRQ-001")
        assert verify_res.status_code == 200
        audit = verify_res.json()

        assert audit["verified"] is True
        assert audit["status"] == "VERIFIED"
        assert audit["assessment_id"] == "CRQ-001"
        assert audit["decision_id"] == "OPT-001"
        assert audit["on_chain_result_hash"] == receipt["result_hash"]
        assert audit["computed_result_hash"] == receipt["result_hash"]
        assert audit["block_height"] == receipt["block_height"]
        assert audit["tx_hash"] == receipt["tx_hash"]
        assert "verified" in audit["message"].lower()


def test_modified_result_causes_verification_failure():
    """Verify that tampering with local quantitative results causes immediate verification failure."""
    with TestClient(app) as client:
        # 1. Record baseline CRQ-001
        rec_res = client.post("/blockchain/record", json={"assessment_id": "CRQ-001", "decision_id": "OPT-001"})
        assert rec_res.status_code == 201

        # 2. Verify initially intact
        v1 = client.get("/blockchain/verify/CRQ-001").json()
        assert v1["verified"] is True

        # 3. Tamper local result (e.g. change Expected Annual Loss to a fraudulent value)
        tamper_res = client.post(
            "/blockchain/tamper-test/CRQ-001",
            json={"tamper_type": "modify_eal", "custom_value": 12345.0},
        )
        assert tamper_res.status_code == 200

        # 4. Verify again -> MUST FAIL
        v2 = client.get("/blockchain/verify/CRQ-001").json()
        assert v2["verified"] is False
        assert v2["status"] == "INTEGRITY_MISMATCH"
        assert v2["computed_result_hash"] != v2["on_chain_result_hash"]
        assert "Tamper Alert" in v2["message"]

        # 5. Restore original state and verify it passes again
        reset_res = client.post("/blockchain/reset-test/CRQ-001")
        assert reset_res.status_code == 200

        v3 = client.get("/blockchain/verify/CRQ-001").json()
        assert v3["verified"] is True
        assert v3["status"] == "VERIFIED"


def test_duplicate_assessment_identical_idempotent():
    """Verify duplicate submission of identical assessment returns existing receipt without forking."""
    with TestClient(app) as client:
        payload = {"assessment_id": "CRQ-001", "decision_id": "OPT-001"}

        # First recording
        res1 = client.post("/blockchain/record", json=payload)
        assert res1.status_code == 201
        receipt1 = res1.json()

        # Second recording with exact same data
        res2 = client.post("/blockchain/record", json=payload)
        assert res2.status_code in (200, 201)
        receipt2 = res2.json()

        assert receipt2["status"] == "ALREADY_RECORDED"
        assert receipt2["tx_hash"] == receipt1["tx_hash"]
        assert receipt2["block_height"] == receipt1["block_height"]
        assert receipt2["canonical_hash"] == receipt1["canonical_hash"]


def test_duplicate_assessment_conflicting_hash_rejection():
    """Verify attempting to overwrite an existing assessment with conflicting data is rejected (409 Conflict)."""
    with TestClient(app) as client:
        # First recording with standard CRQ-001
        res1 = client.post("/blockchain/record", json={"assessment_id": "CRQ-001", "decision_id": "OPT-001"})
        assert res1.status_code == 201

        # Attempt to record conflicting result under same assessment_id
        conflicting_payload = {
            "assessment_id": "CRQ-001",
            "decision_id": "OPT-001",
            "result_hash": "a" * 64,  # Conflicting forged result hash
            "data_snapshot_hash": "b" * 64,
        }
        res2 = client.post("/blockchain/record", json=conflicting_payload)
        assert res2.status_code == 409
        assert "immutable" in res2.json()["detail"].lower()


def test_security_sensitive_data_sanitization():
    """Verify that company financial CSVs, secrets, and raw DB records are never included in canonical hashes."""
    sensitive_data = {
        "assessment_id": "SEC-TEST-001",
        "company_csv": "id,revenue,payroll,secret_tax_id\n1,100000000,5000000,SECRET-999",
        "api_key": "sk-live-super-secret-key-12345",
        "password": "ProductionAdminPassword!123",
        "budget_limit": 5000000.0,
        "criticality": "Critical",
    }

    sanitized = sanitize_data(sensitive_data)
    assert sanitized["company_csv"] == "[REDACTED_SENSITIVE_DATA]"
    assert sanitized["api_key"] == "[REDACTED_SENSITIVE_DATA]"
    assert sanitized["password"] == "[REDACTED_SENSITIVE_DATA]"
    assert sanitized["budget_limit"] == 5000000.0
    assert sanitized["criticality"] == "Critical"

    # Compute hash of sanitized structure
    h = compute_data_snapshot_hash(sensitive_data)
    assert len(h) == 64
    assert isinstance(h, str)


def test_cryptographic_chain_integrity():
    """Verify the local private ledger maintains valid cryptographic links between all blocks."""
    provider = get_blockchain_provider()

    with TestClient(app) as client:
        # Record 2 different benchmark scenarios
        client.post("/blockchain/record", json={"assessment_id": "CRQ-001", "decision_id": "OPT-001"})
        client.post(
            "/blockchain/record",
            json={"assessment_id": "CRQ-ENTERPRISE-001", "decision_id": "OPT-ENTERPRISE-001"},
        )

        assert provider.verify_chain_integrity() is True

        health = provider.get_health()
        assert health.chain_valid is True
        assert health.chain_height == 3  # Genesis + Block 1 + Block 2
        assert health.total_records == 2


def test_tester_ui_served():
    """Verify GET /blockchain/tester delivers the interactive HTML testing console."""
    with TestClient(app) as client:
        response = client.get("/blockchain/tester")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        html = response.text
        assert "TRINETRA Decision Provenance" in html
        assert "Record Decision" in html
        assert "Verify Decision" in html
        assert "Verified" in html
        assert "Integrity mismatch" in html


def test_root_endpoint_includes_blockchain_metadata():
    """Verify root GET / metadata includes blockchain provenance module and endpoints."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Blockchain Decision Provenance" in data["modules"]
        assert "blockchain_model_version" in data
        assert data["blockchain_model_version"] == BLOCKCHAIN_MODEL_VERSION
        assert data["endpoints"]["blockchain_record"] == "/blockchain/record"
        assert data["endpoints"]["blockchain_verify"] == "/blockchain/verify/{assessment_id}"
        assert data["endpoints"]["blockchain_health"] == "/blockchain/health"
        assert data["endpoints"]["blockchain_tester"] == "/blockchain/tester"
