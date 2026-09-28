"""Unit and Integration Tests for Risk Intelligence, Risk Appetite, and Cyber Risk Debt (Phase 4)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
1. No exposure + no appetite
2. Exposure + no appetite
3. Exposure below appetite (WITHIN_APPETITE, debt = 0)
4. Exposure exactly at appetite (AT_APPETITE, debt = 0)
5. Exposure above appetite (ABOVE_APPETITE, debt = exposure - appetite)
6. Zero appetite handling (no divide by zero)
7. Negative appetite rejection (validation error)
8. Risk debt never becomes negative
9. Monetary precision rounding
10. API GET /risk/intelligence with no appetite
11. API GET /risk/intelligence with configured appetite
12. API PUT /risk/appetite configuration
13. API PUT /risk/appetite rejecting negative appetite
14. Schema strictness (extra fields forbidden)
15. Existing snapshots and history endpoints unaffected
16. Existing /risk/change endpoint unaffected
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
    RiskAppetiteRequest,
    RiskAppetiteStatus,
    RiskIntelligenceResponse,
)
from risk.risk_intelligence import calculate_risk_intelligence, get_risk_intelligence


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


# -----------------------------------------------------------------------------
# Unit Tests for calculate_risk_intelligence
# -----------------------------------------------------------------------------

def test_calculate_no_exposure_no_appetite():
    """1. Test calculation when neither exposure nor appetite exists."""
    resp = calculate_risk_intelligence(current_exposure=None, risk_appetite=None)
    assert resp.status == RiskAppetiteStatus.NOT_CONFIGURED
    assert resp.risk_debt is None
    assert resp.has_exposure is False
    assert resp.has_risk_appetite is False
    assert resp.current_exposure is None
    assert resp.risk_appetite is None


def test_calculate_exposure_no_appetite():
    """2. Test calculation when exposure is known but no appetite configured."""
    resp = calculate_risk_intelligence(current_exposure=2219942.70, risk_appetite=None)
    assert resp.status == RiskAppetiteStatus.NOT_CONFIGURED
    assert resp.risk_debt is None
    assert resp.has_exposure is True
    assert resp.has_risk_appetite is False
    assert resp.current_exposure == 2219942.70
    assert resp.risk_appetite is None


def test_calculate_no_exposure_with_appetite():
    """Test calculation when appetite configured but no snapshots exist."""
    resp = calculate_risk_intelligence(current_exposure=None, risk_appetite=3000000.0)
    assert resp.status == RiskAppetiteStatus.NOT_CONFIGURED
    assert resp.risk_debt is None
    assert resp.has_exposure is False
    assert resp.has_risk_appetite is True
    assert resp.risk_appetite == 3000000.0


def test_calculate_exposure_below_appetite():
    """3. Test exposure strictly below appetite (WITHIN_APPETITE, debt = 0)."""
    resp = calculate_risk_intelligence(current_exposure=2000000.0, risk_appetite=3000000.0)
    assert resp.status == RiskAppetiteStatus.WITHIN_APPETITE
    assert resp.risk_debt == 0.0
    assert resp.has_exposure is True
    assert resp.has_risk_appetite is True
    assert resp.current_exposure == 2000000.0
    assert resp.risk_appetite == 3000000.0


def test_calculate_exposure_exactly_at_appetite():
    """4. Test exposure exactly matching appetite (AT_APPETITE, debt = 0)."""
    resp = calculate_risk_intelligence(current_exposure=3000000.0, risk_appetite=3000000.0)
    assert resp.status == RiskAppetiteStatus.AT_APPETITE
    assert resp.risk_debt == 0.0
    assert resp.has_exposure is True
    assert resp.has_risk_appetite is True


def test_calculate_exposure_above_appetite():
    """5. Test exposure exceeding appetite (ABOVE_APPETITE, debt = exposure - appetite)."""
    resp = calculate_risk_intelligence(current_exposure=5000000.0, risk_appetite=3000000.0)
    assert resp.status == RiskAppetiteStatus.ABOVE_APPETITE
    assert resp.risk_debt == 2000000.0
    assert resp.has_exposure is True
    assert resp.has_risk_appetite is True


def test_calculate_zero_appetite():
    """6. Test zero appetite (risk_appetite = 0.0)."""
    # Exposure > 0 with appetite 0
    resp_above = calculate_risk_intelligence(current_exposure=1500000.0, risk_appetite=0.0)
    assert resp_above.status == RiskAppetiteStatus.ABOVE_APPETITE
    assert resp_above.risk_debt == 1500000.0

    # Exposure = 0 with appetite 0
    resp_zero = calculate_risk_intelligence(current_exposure=0.0, risk_appetite=0.0)
    assert resp_zero.status == RiskAppetiteStatus.AT_APPETITE
    assert resp_zero.risk_debt == 0.0


def test_risk_debt_never_negative():
    """8. Test that risk debt is strictly non-negative (max(exposure - appetite, 0))."""
    resp = calculate_risk_intelligence(current_exposure=10000.0, risk_appetite=5000000.0)
    assert resp.risk_debt == 0.0
    assert resp.risk_debt >= 0.0


def test_monetary_precision_rounding():
    """9. Test rounding to 2 decimal places for financial monetary amounts."""
    resp = calculate_risk_intelligence(
        current_exposure=1234567.891,
        risk_appetite=1000000.456,
    )
    assert resp.current_exposure == 1234567.89
    assert resp.risk_appetite == 1000000.46
    assert resp.risk_debt == 234567.43
    assert resp.status == RiskAppetiteStatus.ABOVE_APPETITE


# -----------------------------------------------------------------------------
# Integration Tests for API Endpoints
# -----------------------------------------------------------------------------

def test_api_get_intelligence_empty_database(temp_db: str):
    """10. Test GET /risk/intelligence on empty database returns NOT_CONFIGURED safely."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        response = client.get("/risk/intelligence")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NOT_CONFIGURED"
        assert data["has_exposure"] is False
        assert data["has_risk_appetite"] is False
        assert data["risk_debt"] is None
        assert data["current_exposure"] is None
        assert data["risk_appetite"] is None
    finally:
        set_assessment_storage(None)


def test_api_get_intelligence_with_exposure_no_appetite(temp_db: str):
    """Test GET /risk/intelligence when snapshot exists but appetite is unconfigured."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Seed an assessment batch
        storage.save_batch(
            AssessmentBatchCreate(
                source="test.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=60.0,
                        financial_exposure=2219942.70,
                    )
                ],
            )
        )

        response = client.get("/risk/intelligence")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NOT_CONFIGURED"
        assert data["has_exposure"] is True
        assert data["has_risk_appetite"] is False
        assert data["current_exposure"] == 2219942.70
        assert data["risk_appetite"] is None
        assert data["risk_debt"] is None
    finally:
        set_assessment_storage(None)


def test_api_put_and_get_intelligence_configured(temp_db: str):
    """11 & 12. Test PUT /risk/appetite and subsequent GET /risk/intelligence."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Seed an assessment batch (exposure = 2.22M)
        storage.save_batch(
            AssessmentBatchCreate(
                source="test.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=60.0,
                        financial_exposure=2219942.70,
                    )
                ],
            )
        )

        # 1. PUT /risk/appetite = 3,000,000.0 (appetite > exposure -> WITHIN_APPETITE)
        put_resp = client.put("/risk/appetite", json={"risk_appetite": 3000000.0})
        assert put_resp.status_code == 200
        put_data = put_resp.json()
        assert put_data["status"] == "WITHIN_APPETITE"
        assert put_data["risk_appetite"] == 3000000.0
        assert put_data["current_exposure"] == 2219942.70
        assert put_data["risk_debt"] == 0.0
        assert put_data["has_risk_appetite"] is True
        assert put_data["has_exposure"] is True

        # 2. GET /risk/intelligence reflects the configured state
        get_resp = client.get("/risk/intelligence")
        assert get_resp.status_code == 200
        assert get_resp.json() == put_data

        # 3. PUT /risk/appetite = 1,500,000.0 (appetite < exposure -> ABOVE_APPETITE)
        put_lower = client.put("/risk/appetite", json={"risk_appetite": 1500000.0})
        assert put_lower.status_code == 200
        lower_data = put_lower.json()
        assert lower_data["status"] == "ABOVE_APPETITE"
        assert lower_data["risk_appetite"] == 1500000.0
        assert lower_data["risk_debt"] == round(2219942.70 - 1500000.0, 2)

    finally:
        set_assessment_storage(None)


def test_api_put_rejects_negative_appetite(temp_db: str):
    """7 & 13. Test that negative risk appetite is rejected with HTTP 422."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        response = client.put("/risk/appetite", json={"risk_appetite": -50000.0})
        assert response.status_code == 422
    finally:
        set_assessment_storage(None)


def test_schema_extra_fields_forbidden():
    """14. Test that RiskAppetiteRequest and RiskIntelligenceResponse forbid extra fields."""
    with pytest.raises(ValidationError):
        RiskAppetiteRequest(risk_appetite=1000000.0, unauthorized_field="disallowed")

    with pytest.raises(ValidationError):
        RiskIntelligenceResponse(
            current_exposure=1000.0,
            risk_appetite=2000.0,
            risk_debt=0.0,
            status=RiskAppetiteStatus.WITHIN_APPETITE,
            has_exposure=True,
            has_risk_appetite=True,
            extra_field="invalid",
        )


def test_existing_snapshots_and_change_unaffected(temp_db: str):
    """15 & 16. Verify /risk/latest, /risk/history, and /risk/change remain fully operational."""
    storage = AssessmentStorage(db_path=temp_db)
    set_assessment_storage(storage)
    client = TestClient(app)

    try:
        # Create Batch 1
        storage.save_batch(
            AssessmentBatchCreate(
                source="batch1.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=70.0,
                        financial_exposure=1000000.0,
                    )
                ],
            )
        )
        time.sleep(0.03)

        # Create Batch 2
        storage.save_batch(
            AssessmentBatchCreate(
                source="batch2.csv",
                total_rows=1,
                successful_rows=1,
                results=[
                    AssessmentResultItem(
                        asset_id="AST-01",
                        risk_score=85.0,
                        financial_exposure=1800000.0,
                    )
                ],
            )
        )

        # Set appetite
        client.put("/risk/appetite", json={"risk_appetite": 1500000.0})

        # Verify /risk/latest
        latest = client.get("/risk/latest")
        assert latest.status_code == 200
        assert latest.json()["total_exposure"] == 1800000.0

        # Verify /risk/history
        history = client.get("/risk/history")
        assert history.status_code == 200
        assert len(history.json()) == 2

        # Verify /risk/change
        change = client.get("/risk/change")
        assert change.status_code == 200
        change_data = change.json()
        assert change_data["has_baseline"] is True
        assert change_data["current_exposure"] == 1800000.0
        assert change_data["previous_exposure"] == 1000000.0
        assert change_data["absolute_change"] == 800000.0
        assert change_data["percentage_change"] == 80.0

        # Verify /risk/intelligence
        intel = client.get("/risk/intelligence")
        assert intel.status_code == 200
        intel_data = intel.json()
        assert intel_data["status"] == "ABOVE_APPETITE"
        assert intel_data["risk_debt"] == 300000.0

    finally:
        set_assessment_storage(None)
