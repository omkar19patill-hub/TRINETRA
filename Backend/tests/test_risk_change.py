"""Unit and Integration Tests for Risk Change Intelligence (Phase 3)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
1. Increased exposure
2. Decreased exposure
3. Unchanged exposure
4. Zero previous exposure (division-by-zero avoidance)
5. Zero current exposure
6. Identical snapshots
7. No history (0 snapshots)
8. No previous snapshot (1 snapshot)
9. Multiple batches and correct immediate-previous comparison
10. Average risk changes, critical asset changes, high-risk asset changes
11. FastAPI endpoint GET /risk/change integration & schema strictness
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
    RiskChangeResponse,
    RiskSnapshotResponse,
)
from risk.change_detector import compute_risk_change, detect_latest_risk_change


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


def make_snapshot(
    snap_id: str,
    batch_id: str,
    exposure: float,
    avg_risk: float,
    crit: int,
    high: int,
    timestamp: str = "2026-09-29T02:00:00Z",
) -> RiskSnapshotResponse:
    """Helper to construct a valid RiskSnapshotResponse."""
    return RiskSnapshotResponse(
        id=snap_id,
        batch_id=batch_id,
        timestamp=timestamp,
        total_exposure=exposure,
        average_risk=avg_risk,
        critical_assets=crit,
        high_risk_assets=high,
        risk_appetite=None,
        created_at=timestamp,
    )


# -----------------------------------------------------------------------------
# Unit Tests for compute_risk_change
# -----------------------------------------------------------------------------

def test_compute_risk_change_no_history():
    """Test change calculation when no snapshots exist at all."""
    result = compute_risk_change(current=None, previous=None)
    assert isinstance(result, RiskChangeResponse)
    assert result.has_history is False
    assert result.has_baseline is False
    assert result.current_snapshot is None
    assert result.previous_snapshot is None
    assert result.current_exposure is None
    assert result.previous_exposure is None
    assert result.absolute_change is None
    assert result.percentage_change is None


def test_compute_risk_change_no_previous():
    """Test change calculation when only a current snapshot exists (no baseline yet)."""
    curr = make_snapshot("SNAP-1", "BATCH-1", 500000.0, 65.0, 2, 3)
    result = compute_risk_change(current=curr, previous=None)

    assert result.has_history is True
    assert result.has_baseline is False
    assert result.current_snapshot is not None
    assert result.current_snapshot.id == "SNAP-1"
    assert result.previous_snapshot is None
    assert result.current_exposure == 500000.0
    assert result.previous_exposure is None
    assert result.absolute_change is None
    assert result.percentage_change is None
    assert result.current_average_risk == 65.0
    assert result.previous_average_risk is None
    assert result.average_risk_change is None
    assert result.current_critical_assets == 2
    assert result.critical_assets_change is None


def test_compute_risk_change_exposure_increased():
    """Test change calculation when financial exposure increases."""
    prev = make_snapshot("SNAP-1", "BATCH-1", 100000.0, 50.0, 1, 2)
    curr = make_snapshot("SNAP-2", "BATCH-2", 150000.0, 65.0, 3, 4)
    result = compute_risk_change(current=curr, previous=prev)

    assert result.has_history is True
    assert result.has_baseline is True
    assert result.previous_exposure == 100000.0
    assert result.current_exposure == 150000.0
    assert result.absolute_change == 50000.0
    assert result.percentage_change == 50.0
    assert result.average_risk_change == 15.0
    assert result.critical_assets_change == 2
    assert result.high_risk_assets_change == 2


def test_compute_risk_change_exposure_decreased():
    """Test change calculation when financial exposure decreases."""
    prev = make_snapshot("SNAP-1", "BATCH-1", 200000.0, 70.0, 3, 5)
    curr = make_snapshot("SNAP-2", "BATCH-2", 150000.0, 55.0, 1, 3)
    result = compute_risk_change(current=curr, previous=prev)

    assert result.has_history is True
    assert result.has_baseline is True
    assert result.previous_exposure == 200000.0
    assert result.current_exposure == 150000.0
    assert result.absolute_change == -50000.0
    assert result.percentage_change == -25.0
    assert result.average_risk_change == -15.0
    assert result.critical_assets_change == -2
    assert result.high_risk_assets_change == -2


def test_compute_risk_change_exposure_unchanged():
    """Test change calculation when exposure is identical between runs."""
    prev = make_snapshot("SNAP-1", "BATCH-1", 100000.0, 50.0, 1, 2)
    curr = make_snapshot("SNAP-2", "BATCH-2", 100000.0, 50.0, 1, 2)
    result = compute_risk_change(current=curr, previous=prev)

    assert result.has_history is True
    assert result.has_baseline is True
    assert result.absolute_change == 0.0
    assert result.percentage_change == 0.0
    assert result.average_risk_change == 0.0
    assert result.critical_assets_change == 0
    assert result.high_risk_assets_change == 0


def test_compute_risk_change_zero_previous_exposure():
    """Test division-by-zero avoidance when previous exposure is 0.0."""
    prev = make_snapshot("SNAP-1", "BATCH-1", 0.0, 0.0, 0, 0)
    curr = make_snapshot("SNAP-2", "BATCH-2", 75000.0, 45.0, 1, 1)
    result = compute_risk_change(current=curr, previous=prev)

    assert result.previous_exposure == 0.0
    assert result.current_exposure == 75000.0
    assert result.absolute_change == 75000.0
    assert result.percentage_change is None  # Must NOT divide by zero or fabricate a percentage


def test_compute_risk_change_zero_current_exposure():
    """Test calculation when current exposure drops to 0.0."""
    prev = make_snapshot("SNAP-1", "BATCH-1", 100000.0, 60.0, 2, 2)
    curr = make_snapshot("SNAP-2", "BATCH-2", 0.0, 0.0, 0, 0)
    result = compute_risk_change(current=curr, previous=prev)

    assert result.previous_exposure == 100000.0
    assert result.current_exposure == 0.0
    assert result.absolute_change == -100000.0
    assert result.percentage_change == -100.0


# -----------------------------------------------------------------------------
# Integration Tests for GET /risk/change endpoint
# -----------------------------------------------------------------------------

def test_api_risk_change_empty_database(temp_db: str):
    """Test GET /risk/change against an empty assessment database."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        response = client.get("/risk/change")
        assert response.status_code == 200
        data = response.json()
        assert data["has_history"] is False
        assert data["has_baseline"] is False
        assert data["current_snapshot"] is None
        assert data["previous_snapshot"] is None
        assert data["absolute_change"] is None
        assert data["percentage_change"] is None
    finally:
        set_assessment_storage(None)


def test_api_risk_change_single_batch(temp_db: str):
    """Test GET /risk/change when only 1 assessment batch has been persisted."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        storage.save_batch(
            AssessmentBatchCreate(
                source="single.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=80.0,
                        financial_exposure=250000.0,
                    )
                ],
            )
        )

        response = client.get("/risk/change")
        assert response.status_code == 200
        data = response.json()
        assert data["has_history"] is True
        assert data["has_baseline"] is False
        assert data["current_snapshot"] is not None
        assert data["previous_snapshot"] is None
        assert data["current_exposure"] == 250000.0
        assert data["previous_exposure"] is None
        assert data["absolute_change"] is None
        assert data["percentage_change"] is None
        assert data["current_critical_assets"] == 1
    finally:
        set_assessment_storage(None)


def test_api_risk_change_multiple_batches_immediate_previous_comparison(temp_db: str):
    """Test that GET /risk/change compares Batch N against Batch N-1, NOT Batch 1."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Batch 1 (oldest)
        b1 = storage.save_batch(
            AssessmentBatchCreate(
                source="batch_1.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=30.0,
                        financial_exposure=1000000.0,
                    )
                ],
            )
        )
        time.sleep(0.03)

        # Batch 2 (middle)
        b2 = storage.save_batch(
            AssessmentBatchCreate(
                source="batch_2.csv",
                total_rows=2,
                successful_rows=2,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=80.0,  # Critical
                        financial_exposure=1200000.0,
                    ),
                    AssessmentResultItem(
                        asset_id="AST-02",
                        risk_score=70.0,  # High
                        financial_exposure=800000.0,
                    ),
                ],
            )
        )
        time.sleep(0.03)

        # Batch 3 (newest)
        b3 = storage.save_batch(
            AssessmentBatchCreate(
                source="batch_3.csv",
                total_rows=2,
                successful_rows=2,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=60.0,  # High
                        financial_exposure=900000.0,
                    ),
                    AssessmentResultItem(
                        asset_id="AST-02",
                        risk_score=60.0,  # High
                        financial_exposure=600000.0,
                    ),
                ],
            )
        )

        response = client.get("/risk/change")
        assert response.status_code == 200
        data = response.json()

        assert data["has_history"] is True
        assert data["has_baseline"] is True

        # Crucial check: current is Batch 3, previous is Batch 2 (NOT Batch 1)
        assert data["current_snapshot"]["batch_id"] == b3.batch_id
        assert data["previous_snapshot"]["batch_id"] == b2.batch_id

        # Exposure comparison: Batch 3 (1.5M) vs Batch 2 (2.0M)
        assert data["current_exposure"] == 1500000.0
        assert data["previous_exposure"] == 2000000.0
        assert data["absolute_change"] == -500000.0
        assert data["percentage_change"] == -25.0

        # Average risk comparison: Batch 3 (60.0) vs Batch 2 (75.0)
        assert data["current_average_risk"] == 60.0
        assert data["previous_average_risk"] == 75.0
        assert data["average_risk_change"] == -15.0

        # Critical assets comparison: Batch 3 (0) vs Batch 2 (1)
        assert data["current_critical_assets"] == 0
        assert data["previous_critical_assets"] == 1
        assert data["critical_assets_change"] == -1

        # High risk assets comparison: Batch 3 (2) vs Batch 2 (1)
        assert data["current_high_risk_assets"] == 2
        assert data["previous_high_risk_assets"] == 1
        assert data["high_risk_assets_change"] == 1

    finally:
        set_assessment_storage(None)


def test_risk_change_schema_strictness():
    """Test that RiskChangeResponse strictly forbids extra fields."""
    valid_data = {
        "has_history": True,
        "has_baseline": True,
        "current_snapshot": None,
        "previous_snapshot": None,
        "previous_exposure": 100000.0,
        "current_exposure": 150000.0,
        "absolute_change": 50000.0,
        "percentage_change": 50.0,
        "previous_average_risk": 50.0,
        "current_average_risk": 60.0,
        "average_risk_change": 10.0,
        "previous_critical_assets": 1,
        "current_critical_assets": 2,
        "critical_assets_change": 1,
        "previous_high_risk_assets": 2,
        "current_high_risk_assets": 3,
        "high_risk_assets_change": 1,
    }
    # Valid data passes
    resp = RiskChangeResponse(**valid_data)
    assert resp.has_baseline is True

    # Extra fields rejected with ValidationError
    invalid_data = {**valid_data, "unauthorized_metadata": "disallowed"}
    with pytest.raises(ValidationError):
        RiskChangeResponse(**invalid_data)
