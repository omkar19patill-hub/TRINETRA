"""Unit and Integration Tests for SQLite Assessment Persistence Layer (Phase 1)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
1. Idempotent schema initialization (tables & indexes)
2. Atomic assessment batch, results, and risk snapshot insertion
3. Snapshot mathematical integrity (exposure sum, avg risk, critical/high counts)
4. Querying functions (get_batch, list_batches, get_batch_results, get_latest_snapshot, list_snapshots)
5. FastAPI endpoint POST /risk/assessment-batch
6. Non-interference with existing vulnerabilities database table
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from risk.storage import AssessmentStorage, set_assessment_storage
from risk.schemas import AssessmentBatchCreate, AssessmentResultItem
from cache.vulnerability_cache import VulnerabilityStorage
from normalization.vulnerability_normalizer import normalize_vulnerability_record
from schemas.vulnerability import RawEPSSData, RawKEVData, RawNVDData


def safe_cleanup(path: str):
    """Safely remove a temporary database file."""
    for ext in ["", "-wal", "-shm"]:
        p = f"{path}{ext}"
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Provide an isolated temporary SQLite database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    safe_cleanup(db_path)


def test_schema_initialization_idempotence(temp_db: str):
    """Test that schema initialization creates required tables and is safely idempotent."""
    storage = AssessmentStorage(db_path=temp_db)

    # Verify tables exist
    conn = storage._get_connection()
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        ]
        assert "assessment_batches" in tables
        assert "assessment_results" in tables
        assert "risk_snapshots" in tables

        # Second call to ensure idempotence
        storage._ensure_schema(conn)
    finally:
        conn.close()


def test_save_batch_and_snapshot_generation(temp_db: str):
    """Test saving an assessment batch and verify auto-generated risk snapshot metrics."""
    storage = AssessmentStorage(db_path=temp_db)

    batch_input = AssessmentBatchCreate(
        batch_id="TEST-BATCH-001",
        source="test_upload.csv",
        total_rows=3,
        successful_rows=3,
        failed_rows=0,
        status="COMPLETED",
        risk_appetite=500000.0,
        results=[
            AssessmentResultItem(
                asset_id="AST-001",
                asset_name="Core Gateway",
                cve_id="CVE-2026-1234",
                criticality="Critical",
                risk_score=89.5,  # >= 75 -> Critical
                financial_exposure=400000.0,
                assessment_data={"downtime_hours": 10.0, "risk_level": "CRITICAL"},
            ),
            AssessmentResultItem(
                asset_id="AST-002",
                asset_name="Payment API",
                cve_id="CVE-2026-5678",
                criticality="High",
                risk_score=62.0,  # 50 - 74.99 -> High
                financial_exposure=250000.0,
                assessment_data={"downtime_hours": 6.0, "risk_level": "HIGH"},
            ),
            AssessmentResultItem(
                asset_id="AST-003",
                asset_name="Internal Portal",
                cve_id="CVE-2026-9999",
                criticality="Medium",
                risk_score=35.0,  # 25 - 49.99 -> Medium
                financial_exposure=75000.0,
                assessment_data={"downtime_hours": 2.0, "risk_level": "MEDIUM"},
            ),
        ],
    )

    response = storage.save_batch(batch_input)

    assert response.batch_id == "TEST-BATCH-001"
    assert response.total_rows == 3
    assert response.successful_rows == 3
    assert response.failed_rows == 0
    assert response.status == "COMPLETED"

    # Verify snapshot math
    snapshot = response.snapshot
    assert snapshot.total_exposure == 400000.0 + 250000.0 + 75000.0  # 725000.0
    assert snapshot.average_risk == round((89.5 + 62.0 + 35.0) / 3, 2)  # 62.17
    assert snapshot.critical_assets == 1
    assert snapshot.high_risk_assets == 1
    assert snapshot.risk_appetite == 500000.0


def test_storage_query_methods(temp_db: str):
    """Test retrieval methods for batches, results, and snapshots."""
    storage = AssessmentStorage(db_path=temp_db)

    batch_input = AssessmentBatchCreate(
        batch_id="QUERY-BATCH-001",
        source="server_assets.csv",
        total_rows=1,
        successful_rows=1,
        failed_rows=0,
        results=[
            AssessmentResultItem(
                asset_id="AST-SERVER-01",
                risk_score=78.0,
                financial_exposure=150000.0,
                assessment_data={"engine": "risk-model-v1"},
            )
        ],
    )
    storage.save_batch(batch_input)

    # 1. get_batch
    batch = storage.get_batch("QUERY-BATCH-001")
    assert batch is not None
    assert batch["id"] == "QUERY-BATCH-001"
    assert batch["source"] == "server_assets.csv"

    # 2. list_batches
    batches = storage.list_batches()
    assert len(batches) == 1
    assert batches[0]["id"] == "QUERY-BATCH-001"

    # 3. get_batch_results
    results = storage.get_batch_results("QUERY-BATCH-001")
    assert len(results) == 1
    assert results[0]["asset_identifier"] == "AST-SERVER-01"
    assert results[0]["financial_exposure"] == 150000.0
    assert results[0]["assessment_data"]["engine"] == "risk-model-v1"

    # 4. get_latest_snapshot
    latest = storage.get_latest_snapshot()
    assert latest is not None
    assert latest["total_exposure"] == 150000.0
    assert latest["critical_assets"] == 1

    # 5. list_snapshots
    snapshots = storage.list_snapshots()
    assert len(snapshots) == 1


def test_api_assessment_batch_endpoint(temp_db: str):
    """Test POST /risk/assessment-batch FastAPI route with dependency override."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)

    client = TestClient(app)
    try:
        payload = {
            "source": "api_test.csv",
            "total_rows": 2,
            "successful_rows": 2,
            "failed_rows": 0,
            "status": "COMPLETED",
            "risk_appetite": 1000000.0,
            "results": [
                {
                    "asset_id": "AST-API-01",
                    "asset_name": "API Gateway",
                    "risk_score": 85.0,
                    "financial_exposure": 500000.0,
                    "cve_id": "CVE-2026-1000",
                    "criticality": "Critical",
                    "assessment_data": {"tested": True},
                },
                {
                    "asset_id": "AST-API-02",
                    "asset_name": "Auth Service",
                    "risk_score": 45.0,
                    "financial_exposure": 120000.0,
                    "cve_id": "CVE-2026-2000",
                    "criticality": "Medium",
                    "assessment_data": {"tested": True},
                },
            ],
        }

        resp = client.post("/risk/assessment-batch", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        assert data["source"] == "api_test.csv"
        assert data["total_rows"] == 2
        assert "snapshot" in data
        assert data["snapshot"]["total_exposure"] == 620000.0
        assert data["snapshot"]["critical_assets"] == 1
        assert data["snapshot"]["high_risk_assets"] == 0

        # Test validation rejection for invalid payload (extra field forbidden)
        bad_payload = {**payload, "unexpected_extra_field": "invalid"}
        bad_resp = client.post("/risk/assessment-batch", json=bad_payload)
        assert bad_resp.status_code == 422
    finally:
        set_assessment_storage(None)


def test_vulnerabilities_and_assessments_coexist(temp_db: str):
    """Ensure both VulnerabilityStorage and AssessmentStorage can write to the same database safely."""
    v_storage = VulnerabilityStorage(db_path=temp_db)
    a_storage = AssessmentStorage(db_path=temp_db)

    # Insert vulnerability
    record = normalize_vulnerability_record(
        cve_id="CVE-2026-9999",
        nvd_data=RawNVDData(cve_id="CVE-2026-9999", cvss_score=8.5, severity="HIGH"),
        epss_data=RawEPSSData(cve_id="CVE-2026-9999", epss=0.55),
        kev_data=RawKEVData(cve_id="CVE-2026-9999", is_known_exploited=False),
    )
    assert v_storage.upsert_vulnerability(record) is True

    # Insert assessment batch
    batch = a_storage.save_batch(
        AssessmentBatchCreate(
            source="coexist.csv",
            total_rows=1,
            successful_rows=1,
            failed_rows=0,
            results=[
                AssessmentResultItem(
                    asset_id="AST-COEXIST",
                    risk_score=75.0,
                    financial_exposure=200000.0,
                )
            ],
        )
    )
    assert batch.batch_id is not None

    # Verify both exist in database
    v = v_storage.get_vulnerability("CVE-2026-9999")
    assert v is not None
    assert v.cve_id == "CVE-2026-9999"

    latest_snap = a_storage.get_latest_snapshot()
    assert latest_snap is not None
    assert latest_snap["total_exposure"] == 200000.0
