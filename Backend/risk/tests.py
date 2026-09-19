"""Unit and Integration Tests for the TRINETRA Risk Engine

TRINETRA - SIH 2026

Tests cover:
- Benchmark Test 1: Very high risk asset-vulnerability pair
- Benchmark Test 2: High exposure, moderate vulnerability
- Benchmark Test 3: Moderate vulnerability, internal asset
- Benchmark Test 4: Low severity, internal low-criticality asset
- Benchmark Test 5: High technical severity vs. Low business criticality
- Edge Cases: Zero values, Maximum values, Score boundary clamping [0, 100]
- Validation Failures: Out-of-bounds CVSS/EPSS, invalid criticality enum
- API Endpoint Tests: /risk/calculate and /risk/health via TestClient
"""

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Ensure parent directory is in sys.path for direct execution
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from risk.schemas import RiskCalculationRequest, CriticalityEnum
from risk.scoring import (
    normalize_cvss,
    calculate_likelihood,
    calculate_impact,
    calculate_risk_score,
    get_risk_level,
)
from risk.drivers import generate_risk_drivers
from risk.engine import calculate_risk
from risk.constants import (
    CVSS_WEIGHT,
    EPSS_WEIGHT,
    KEV_WEIGHT,
    EXPOSURE_WEIGHT,
    CRITICALITY_IMPACT,
    MODEL_VERSION,
)


# ===========================================================================
# 1. Benchmark Test Cases (From Specification)
# ===========================================================================

def test_benchmark_1_very_high_risk():
    """Test 1 — Very high risk scenario (Prompt Benchmark)."""
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-TEST-001",
        "cvss": 9.8,
        "epss": 0.82,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Critical",
    }
    result = calculate_risk(payload)

    # Normalized CVSS
    assert result.calculation.cvss_normalized == 0.98

    # Individual contributions
    assert result.calculation.cvss_contribution == round(0.25 * 0.98, 4)  # 0.245
    assert result.calculation.epss_contribution == round(0.40 * 0.82, 4)  # 0.328
    assert result.calculation.kev_contribution == 0.20
    assert result.calculation.exposure_contribution == 0.15

    # Composite likelihood = 0.245 + 0.328 + 0.20 + 0.15 = 0.923
    assert result.likelihood == 0.923
    assert result.impact == 1.00
    # Risk Score = 0.923 * 1.00 * 100 = 92.3
    assert result.risk_score == 92.30
    assert result.risk_level == "CRITICAL"

    # All 5 risk drivers should trigger
    expected_drivers = [
        "Critical CVSS",
        "High exploitation probability",
        "Known exploited vulnerability",
        "Internet exposed asset",
        "Critical business asset",
    ]
    for driver in expected_drivers:
        assert driver in result.risk_drivers
    assert len(result.risk_drivers) == 5

    # Governance metadata
    assert result.model.version == MODEL_VERSION
    assert result.model.type == "deterministic"


def test_benchmark_2_high_exposure_moderate_vuln():
    """Test 2 — High exposure, moderate vulnerability."""
    payload = {
        "asset_id": "AST-002",
        "cve_id": "CVE-TEST-002",
        "cvss": 7.5,
        "epss": 0.50,
        "kev": False,
        "internet_exposed": True,
        "criticality": "High",
    }
    result = calculate_risk(payload)

    # 0.25 * 0.75 = 0.1875
    # 0.40 * 0.50 = 0.20
    # 0.20 * 0    = 0.00
    # 0.15 * 1    = 0.15
    # Likelihood = 0.1875 + 0.20 + 0 + 0.15 = 0.5375
    assert result.likelihood == 0.5375
    assert result.impact == 0.75
    # Risk Score = 0.5375 * 0.75 * 100 = 40.3125 -> 40.31
    assert result.risk_score == 40.31
    assert result.risk_level == "MEDIUM"

    # Only internet exposure triggered (CVSS < 9, EPSS < 0.7, KEV False, Criticality High)
    assert result.risk_drivers == ["Internet exposed asset"]


def test_benchmark_3_internal_moderate():
    """Test 3 — Internal moderate asset and vulnerability."""
    payload = {
        "asset_id": "AST-003",
        "cve_id": "CVE-TEST-003",
        "cvss": 5.0,
        "epss": 0.10,
        "kev": False,
        "internet_exposed": False,
        "criticality": "Medium",
    }
    result = calculate_risk(payload)

    # 0.25 * 0.50 = 0.125
    # 0.40 * 0.10 = 0.04
    # Likelihood = 0.165
    assert result.likelihood == 0.165
    assert result.impact == 0.50
    # Risk Score = 0.165 * 0.50 * 100 = 8.25
    assert result.risk_score == 8.25
    assert result.risk_level == "LOW"
    assert result.risk_drivers == []


def test_benchmark_4_low_severity_internal():
    """Test 4 — Low severity on internal low-criticality asset."""
    payload = {
        "asset_id": "AST-004",
        "cve_id": "CVE-TEST-004",
        "cvss": 2.5,
        "epss": 0.02,
        "kev": False,
        "internet_exposed": False,
        "criticality": "Low",
    }
    result = calculate_risk(payload)

    # 0.25 * 0.25 = 0.0625
    # 0.40 * 0.02 = 0.008
    # Likelihood = 0.0705
    assert result.likelihood == 0.0705
    assert result.impact == 0.25
    # Risk Score = 0.0705 * 0.25 * 100 = 1.7625 -> 1.76
    assert result.risk_score == 1.76
    assert result.risk_level == "LOW"
    assert result.risk_drivers == []


def test_benchmark_5_technical_severity_vs_business_criticality():
    """Test 5 — Technical severity is high, but lower business criticality reduces final risk."""
    payload = {
        "asset_id": "AST-005",
        "cve_id": "CVE-TEST-005",
        "cvss": 9.8,
        "epss": 0.90,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Low",
    }
    result = calculate_risk(payload)

    # Technical Likelihood is very high:
    # 0.25 * 0.98 = 0.245
    # 0.40 * 0.90 = 0.360
    # 0.20 * 1.00 = 0.200
    # 0.15 * 1.00 = 0.150
    # Likelihood = 0.955
    assert result.likelihood == 0.955

    # Business impact is Low (0.25)
    assert result.impact == 0.25

    # Risk Score = 0.955 * 0.25 * 100 = 23.875 -> 23.88
    # Low business criticality brings the overall score down to LOW tier
    assert result.risk_score == 23.88
    assert result.risk_level == "LOW"

    # Drivers correctly reflect high technical factors despite lower final score
    assert "Critical CVSS" in result.risk_drivers
    assert "High exploitation probability" in result.risk_drivers
    assert "Known exploited vulnerability" in result.risk_drivers
    assert "Internet exposed asset" in result.risk_drivers
    assert "Critical business asset" not in result.risk_drivers


# ===========================================================================
# 2. Mathematical Edge Cases & Boundary Clamping
# ===========================================================================

def test_absolute_minimum_boundary():
    """Test zero-value inputs clamp gracefully to 0.0."""
    payload = {
        "asset_id": "AST-MIN",
        "cve_id": "CVE-MIN",
        "cvss": 0.0,
        "epss": 0.0,
        "kev": False,
        "internet_exposed": False,
        "criticality": "Low",
    }
    result = calculate_risk(payload)
    assert result.likelihood == 0.0
    assert result.impact == 0.25
    assert result.risk_score == 0.0
    assert result.risk_level == "LOW"
    assert result.risk_drivers == []


def test_absolute_maximum_boundary():
    """Test maximum possible inputs clamp gracefully to 100.0."""
    payload = {
        "asset_id": "AST-MAX",
        "cve_id": "CVE-MAX",
        "cvss": 10.0,
        "epss": 1.0,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Critical",
    }
    result = calculate_risk(payload)
    assert result.likelihood == 1.0
    assert result.impact == 1.00
    assert result.risk_score == 100.0
    assert result.risk_level == "CRITICAL"
    assert len(result.risk_drivers) == 5


def test_cvss_normalization():
    """Verify CVSS normalization across range."""
    assert normalize_cvss(0.0) == 0.0
    assert normalize_cvss(5.0) == 0.5
    assert normalize_cvss(9.8) == 0.98
    assert normalize_cvss(10.0) == 1.0


def test_risk_level_threshold_boundaries():
    """Verify threshold boundary conditions."""
    assert get_risk_level(0.0) == "LOW"
    assert get_risk_level(24.99) == "LOW"
    assert get_risk_level(25.0) == "MEDIUM"
    assert get_risk_level(49.99) == "MEDIUM"
    assert get_risk_level(50.0) == "HIGH"
    assert get_risk_level(74.99) == "HIGH"
    assert get_risk_level(75.0) == "CRITICAL"
    assert get_risk_level(100.0) == "CRITICAL"


# ===========================================================================
# 3. Input Validation Failure Cases
# ===========================================================================

def test_negative_cvss_rejected():
    with pytest.raises(ValidationError):
        RiskCalculationRequest(
            asset_id="AST-1",
            cve_id="CVE-1",
            cvss=-1.0,
            epss=0.5,
            kev=False,
            internet_exposed=False,
            criticality=CriticalityEnum.LOW,
        )


def test_cvss_above_10_rejected():
    with pytest.raises(ValidationError):
        RiskCalculationRequest(
            asset_id="AST-1",
            cve_id="CVE-1",
            cvss=10.1,
            epss=0.5,
            kev=False,
            internet_exposed=False,
            criticality=CriticalityEnum.LOW,
        )


def test_negative_epss_rejected():
    with pytest.raises(ValidationError):
        RiskCalculationRequest(
            asset_id="AST-1",
            cve_id="CVE-1",
            cvss=5.0,
            epss=-0.01,
            kev=False,
            internet_exposed=False,
            criticality=CriticalityEnum.LOW,
        )


def test_epss_above_1_rejected():
    with pytest.raises(ValidationError):
        RiskCalculationRequest(
            asset_id="AST-1",
            cve_id="CVE-1",
            cvss=5.0,
            epss=1.05,
            kev=False,
            internet_exposed=False,
            criticality=CriticalityEnum.LOW,
        )


def test_invalid_criticality_rejected():
    with pytest.raises(ValidationError):
        RiskCalculationRequest(
            asset_id="AST-1",
            cve_id="CVE-1",
            cvss=5.0,
            epss=0.5,
            kev=False,
            internet_exposed=False,
            criticality="Extreme",  # type: ignore
        )


def test_empty_asset_or_cve_id_rejected():
    with pytest.raises(ValidationError):
        RiskCalculationRequest(
            asset_id="",
            cve_id="CVE-1",
            cvss=5.0,
            epss=0.5,
            kev=False,
            internet_exposed=False,
            criticality=CriticalityEnum.LOW,
        )


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        RiskCalculationRequest(
            asset_id="AST-1",
            cve_id="CVE-1",
            cvss=5.0,
            epss=0.5,
            kev=False,
            internet_exposed=False,
            criticality=CriticalityEnum.LOW,
            unexpected_field="injection",  # type: ignore
        )


# ===========================================================================
# 4. FastAPI Endpoint Integration Tests
# ===========================================================================

def test_api_health_endpoint():
    """Verify GET /risk/health endpoint."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/risk/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["module"] == "risk-engine"
    assert data["model_version"] == MODEL_VERSION


def test_api_calculate_endpoint_success():
    """Verify POST /risk/calculate endpoint with valid payload."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-2026-1234",
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
    assert data["cve_id"] == "CVE-2026-1234"
    assert data["likelihood"] == 0.923
    assert data["impact"] == 1.0
    assert data["risk_score"] == 92.3
    assert data["risk_level"] == "CRITICAL"
    assert len(data["risk_drivers"]) == 5
    assert "calculation" in data
    assert "model" in data


def test_api_calculate_endpoint_validation_error():
    """Verify POST /risk/calculate returns 422 Unprocessable Entity on bad payload."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    invalid_payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-2026-1234",
        "cvss": 12.5,  # Out of range!
        "epss": 0.82,
        "kev": True,
        "internet_exposed": True,
        "criticality": "SuperCritical",  # Invalid enum!
    }
    response = client.post("/risk/calculate", json=invalid_payload)
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
