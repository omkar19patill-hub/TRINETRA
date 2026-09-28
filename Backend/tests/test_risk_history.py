"""Unit and Integration Tests for Risk History and Latest Snapshot Endpoints (Phase 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
1. history returns persisted snapshots with all 9 required fields
2. history ordering is correct (chronological 'asc' and reverse 'desc')
3. latest returns the newest snapshot
4. latest handles empty history cleanly (404 Not Found, history returns [])
5. multiple assessment batches remain separate (batch isolation)
6. schema enforcement: extra fields are forbidden
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Generator
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from risk.storage import AssessmentStorage, set_assessment_storage
from risk.schemas import (
    AssessmentBatchCreate,
    AssessmentResultItem,
    RiskSnapshotResponse,
)


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


def test_history_returns_persisted_snapshots(temp_db: str):
    """1. Test that GET /risk/history returns persisted snapshots with all 9 required fields."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Create 2 assessment batches
        storage.save_batch(
            AssessmentBatchCreate(
                source="test_batch_1.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-001",
                        asset_name="Core DB",
                        risk_score=92.0,
                        financial_exposure=500000.0,
                    )
                ],
                risk_appetite=200000.0,
            )
        )
        time.sleep(0.02)
        storage.save_batch(
            AssessmentBatchCreate(
                source="test_batch_2.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-002",
                        asset_name="Payment Gateway",
                        risk_score=75.0,
                        financial_exposure=300000.0,
                    )
                ],
                risk_appetite=200000.0,
            )
        )

        response = client.get("/risk/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify all 9 required fields in each snapshot
        required_fields = {
            "id",
            "batch_id",
            "timestamp",
            "total_exposure",
            "average_risk",
            "critical_assets",
            "high_risk_assets",
            "risk_appetite",
            "created_at",
        }
        for item in data:
            assert required_fields.issubset(item.keys())
            # Ensure Pydantic model parses without error
            snapshot = RiskSnapshotResponse(**item)
            assert snapshot.id is not None
            assert snapshot.total_exposure > 0

    finally:
        set_assessment_storage(None)


def test_history_ordering_is_correct(temp_db: str):
    """2. Test that GET /risk/history orders snapshots chronologically (asc) and respects limit and desc."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Save 3 sequential batches with pauses to ensure distinct timestamps
        exposures = [100000.0, 200000.0, 300000.0]
        for exp in exposures:
            storage.save_batch(
                AssessmentBatchCreate(
                    source=f"batch_{exp}.csv",
                    total_rows=1,
                    successful_rows=1,
                    results=[
                        AssessmentResultItem(
                            asset_id="AST-TEST",
                            risk_score=50.0,
                            financial_exposure=exp,
                        )
                    ],
                )
            )
            time.sleep(0.03)

        # Default query (chronological: oldest first, asc)
        resp_asc = client.get("/risk/history")
        assert resp_asc.status_code == 200
        data_asc = resp_asc.json()
        assert len(data_asc) == 3
        assert [d["total_exposure"] for d in data_asc] == [100000.0, 200000.0, 300000.0]
        assert data_asc[0]["timestamp"] <= data_asc[1]["timestamp"] <= data_asc[2]["timestamp"]

        # Reverse chronological query (newest first, desc)
        resp_desc = client.get("/risk/history?order=desc")
        assert resp_desc.status_code == 200
        data_desc = resp_desc.json()
        assert len(data_desc) == 3
        assert [d["total_exposure"] for d in data_desc] == [300000.0, 200000.0, 100000.0]

        # Limit query
        resp_limit = client.get("/risk/history?limit=2&order=asc")
        assert resp_limit.status_code == 200
        data_limit = resp_limit.json()
        assert len(data_limit) == 2
        assert [d["total_exposure"] for d in data_limit] == [100000.0, 200000.0]

    finally:
        set_assessment_storage(None)


def test_latest_returns_newest_snapshot(temp_db: str):
    """3. Test that GET /risk/latest returns the most recent snapshot."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Create Batch 1
        storage.save_batch(
            AssessmentBatchCreate(
                source="old_batch.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-OLD",
                        risk_score=40.0,
                        financial_exposure=150000.0,
                    )
                ],
            )
        )
        time.sleep(0.03)

        # Create Batch 2 (newest)
        storage.save_batch(
            AssessmentBatchCreate(
                source="newest_batch.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-NEW",
                        risk_score=88.0,
                        financial_exposure=750000.0,
                    )
                ],
            )
        )

        response = client.get("/risk/latest")
        assert response.status_code == 200
        latest = response.json()

        assert latest["total_exposure"] == 750000.0
        assert latest["average_risk"] == 88.0
        assert latest["critical_assets"] == 1
        assert latest["high_risk_assets"] == 0

    finally:
        set_assessment_storage(None)


def test_latest_handles_empty_history(temp_db: str):
    """4. Test that GET /risk/latest returns 404 when no snapshots exist, and /history returns []."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # GET /risk/latest on empty database
        resp_latest = client.get("/risk/latest")
        assert resp_latest.status_code == 404
        error_detail = resp_latest.json()
        assert "detail" in error_detail
        assert "No risk snapshots found" in error_detail["detail"]

        # GET /risk/history on empty database
        resp_history = client.get("/risk/history")
        assert resp_history.status_code == 200
        assert resp_history.json() == []

    finally:
        set_assessment_storage(None)


def test_multiple_assessment_batches_remain_separate(temp_db: str):
    """5. Test that multiple assessment batches remain isolated and independent."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Batch Alpha: 2 assets
        batch_a = storage.save_batch(
            AssessmentBatchCreate(
                source="batch_alpha.csv",
                total_rows=2,
                successful_rows=2,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-A1",
                        risk_score=95.0,
                        financial_exposure=500000.0,
                    ),
                    AssessmentResultItem(
                        asset_id="AST-A2",
                        risk_score=72.0,
                        financial_exposure=200000.0,
                    ),
                ],
            )
        )
        time.sleep(0.03)

        # Batch Beta: 3 assets
        batch_b = storage.save_batch(
            AssessmentBatchCreate(
                source="batch_beta.csv",
                total_rows=3,
                successful_rows=3,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-B1",
                        risk_score=50.0,
                        financial_exposure=100000.0,
                    ),
                    AssessmentResultItem(
                        asset_id="AST-B2",
                        risk_score=45.0,
                        financial_exposure=80000.0,
                    ),
                    AssessmentResultItem(
                        asset_id="AST-B3",
                        risk_score=90.0,
                        financial_exposure=400000.0,
                    ),
                ],
            )
        )

        # Verify results isolation directly in storage
        results_a = storage.get_batch_results(batch_a.batch_id)
        results_b = storage.get_batch_results(batch_b.batch_id)
        assert len(results_a) == 2
        assert len(results_b) == 3
        asset_ids_a = {r["asset_identifier"] for r in results_a}
        asset_ids_b = {r["asset_identifier"] for r in results_b}
        assert asset_ids_a == {"AST-A1", "AST-A2"}
        assert asset_ids_b == {"AST-B1", "AST-B2", "AST-B3"}
        assert asset_ids_a.isdisjoint(asset_ids_b)

        # Verify history endpoint reflects both discrete snapshots
        history = client.get("/risk/history").json()
        assert len(history) == 2
        snap_a = next(s for s in history if s["batch_id"] == batch_a.batch_id)
        snap_b = next(s for s in history if s["batch_id"] == batch_b.batch_id)

        assert snap_a["total_exposure"] == 700000.0
        assert snap_a["critical_assets"] == 1
        assert snap_a["high_risk_assets"] == 1

        assert snap_b["total_exposure"] == 580000.0
        assert snap_b["critical_assets"] == 1
        assert snap_b["high_risk_assets"] == 1

    finally:
        set_assessment_storage(None)



def test_schema_forbids_extra_fields():
    """6. Test that RiskSnapshotResponse strictly forbids extraneous fields."""
    valid_data = {
        "id": "SNAP-12345678",
        "batch_id": "BATCH-12345678",
        "timestamp": "2026-09-29T02:00:00Z",
        "total_exposure": 100000.0,
        "average_risk": 55.0,
        "critical_assets": 1,
        "high_risk_assets": 0,
        "risk_appetite": 50000.0,
        "created_at": "2026-09-29T02:00:00Z",
    }
    # Valid data passes
    snapshot = RiskSnapshotResponse(**valid_data)
    assert snapshot.id == "SNAP-12345678"

    # Extra field raises ValidationError
    invalid_data = {**valid_data, "unauthorized_extra_field": "disallowed"}
    with pytest.raises(ValidationError):
        RiskSnapshotResponse(**invalid_data)
