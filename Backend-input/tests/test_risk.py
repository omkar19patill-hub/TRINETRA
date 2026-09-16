"""Unit and Integration Tests for Risk Input Validation and Routing

TRINETRA - SIH 2026
Person 1: Automated test suite for schemas and routes.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from main import app
from risk.schemas import RiskInput, RiskResult

client = TestClient(app)

DATA_PATH = Path(__file__).resolve().parent.parent / "risk" / "risk_test_data.json"


# =====================================================================
# 1. Successful Validation & Route Tests
# =====================================================================


def test_valid_critical_asset():
    """Test 1: Valid Critical asset payload returns HTTP 200 and expected structure."""
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "cvss": 9.8,
        "epss": 0.82,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Critical",
    }
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "AST-001"
    assert data["cve_id"] == "CVE-001"
    assert data["likelihood"] is None
    assert data["impact"] is None
    assert data["risk_score"] is None
    assert data["risk_level"] is None
    assert data["risk_drivers"] == []


def test_valid_medium_asset():
    """Test 2: Valid Medium asset payload returns HTTP 200."""
    payload = {
        "asset_id": "AST-002",
        "cve_id": "CVE-002",
        "cvss": 5.4,
        "epss": 0.12,
        "kev": False,
        "internet_exposed": False,
        "criticality": "Medium",
    }
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "AST-002"
    assert data["cve_id"] == "CVE-002"


def test_valid_high_and_low_assets():
    """Test: Valid High and Low criticality assets return HTTP 200."""
    for crit in ["High", "Low"]:
        payload = {
            "asset_id": f"AST-{crit}",
            "cve_id": "CVE-2024-9999",
            "cvss": 7.0,
            "epss": 0.5,
            "kev": False,
            "internet_exposed": True,
            "criticality": crit,
        }
        response = client.post("/risk/calculate", json=payload)
        assert response.status_code == 200
        assert response.json()["asset_id"] == f"AST-{crit}"


def test_synthetic_dataset_records():
    """Test: All records from risk_test_data.json pass schema validation and API ingestion."""
    assert DATA_PATH.exists(), f"Missing dataset file at {DATA_PATH}"
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) == 5, f"Expected 5 records, got {len(records)}"

    for idx, record in enumerate(records, start=1):
        # Validate Pydantic model directly
        validated = RiskInput(**record)
        assert validated.asset_id == record["asset_id"]

        # Validate through API endpoint
        response = client.post("/risk/calculate", json=record)
        assert response.status_code == 200, f"Record #{idx} failed: {response.text}"
        data = response.json()
        assert data["asset_id"] == record["asset_id"]
        assert data["cve_id"] == record["cve_id"]


# =====================================================================
# 2. Boundary & Invalid Input Validation Tests (HTTP 422)
# =====================================================================


def test_cvss_greater_than_10_rejected():
    """Test 3: CVSS > 10 is rejected with HTTP 422."""
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "cvss": 10.1,
        "epss": 0.5,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Critical",
    }
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 422


def test_cvss_less_than_0_rejected():
    """Test: CVSS < 0 is rejected with HTTP 422."""
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "cvss": -0.1,
        "epss": 0.5,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Critical",
    }
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 422


def test_epss_greater_than_1_rejected():
    """Test 4: EPSS > 1 is rejected with HTTP 422."""
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "cvss": 5.0,
        "epss": 1.05,
        "kev": False,
        "internet_exposed": False,
        "criticality": "Low",
    }
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 422


def test_epss_less_than_0_rejected():
    """Test: EPSS < 0 is rejected with HTTP 422."""
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "cvss": 5.0,
        "epss": -0.01,
        "kev": False,
        "internet_exposed": False,
        "criticality": "Low",
    }
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 422


def test_invalid_criticality_rejected():
    """Test 5: Invalid criticality values are rejected with HTTP 422 without silent conversion."""
    invalid_criticalities = ["Extreme", "Severe", "critical", "HIGH", "medium", "unknown", ""]
    for val in invalid_criticalities:
        payload = {
            "asset_id": "AST-001",
            "cve_id": "CVE-001",
            "cvss": 5.0,
            "epss": 0.5,
            "kev": False,
            "internet_exposed": False,
            "criticality": val,
        }
        response = client.post("/risk/calculate", json=payload)
        assert response.status_code == 422, f"Expected 422 for criticality '{val}', got {response.status_code}"


@pytest.mark.parametrize(
    "missing_field",
    [
        "asset_id",
        "cve_id",
        "cvss",
        "epss",
        "kev",
        "internet_exposed",
        "criticality",
    ],
)
def test_missing_required_fields_rejected(missing_field):
    """Test: Missing any required field returns HTTP 422."""
    valid_payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "cvss": 9.8,
        "epss": 0.82,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Critical",
    }
    payload = {k: v for k, v in valid_payload.items() if k != missing_field}
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 422


def test_invalid_boolean_values_rejected():
    """Test: Non-boolean types for kev / internet_exposed return HTTP 422."""
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "cvss": 5.0,
        "epss": 0.5,
        "kev": "invalid_bool",
        "internet_exposed": False,
        "criticality": "Medium",
    }
    response = client.post("/risk/calculate", json=payload)
    assert response.status_code == 422


def test_root_endpoint():
    """Test: Root metadata endpoint is accessible."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "risk_calculate_endpoint" in data
    assert data["risk_calculate_endpoint"] == "/risk/calculate"
