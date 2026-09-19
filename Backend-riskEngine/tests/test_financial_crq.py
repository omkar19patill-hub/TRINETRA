"""Automated Unit and Integration Tests for Financial Cyber Risk Quantification (CRQ)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
"""

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from financial_crq.schemas import (
    FinancialCRQInput,
    FinancialCRQResult,
    LossComponents,
    MonteCarloInput,
)
from financial_crq.engine import (
    calculate_downtime_loss,
    calculate_loss_magnitude,
    calculate_event_frequency,
    calculate_eal,
    calculate_financial_crq,
    generate_financial_explanation,
    generate_financial_assumptions,
    from_risk_result,
    FINANCIAL_MODEL_VERSION,
)
from risk.schemas import RiskCalculationResponse, CalculationBreakdown, ModelInfo


# ===========================================================================
# 1. Unit Tests: Downtime Loss & Loss Magnitude
# ===========================================================================

def test_1_correct_downtime_loss():
    """Verify downtime_loss = revenue_loss_per_hour * downtime_hours (50,000 * 8 = 400,000)."""
    loss = calculate_downtime_loss(revenue_loss_per_hour=50000.0, downtime_hours=8.0)
    assert loss == 400000.0


def test_2_correct_total_loss_magnitude():
    """Verify total loss magnitude sums downtime and all business impact costs."""
    components = calculate_loss_magnitude(
        downtime_loss=400000.0,
        incident_response_cost=100000.0,
        recovery_cost=200000.0,
        regulatory_legal_cost=50000.0,
        customer_business_impact=75000.0,
    )
    assert components.downtime_loss == 400000.0
    assert components.incident_response_cost == 100000.0
    assert components.recovery_cost == 200000.0
    assert components.regulatory_legal_cost == 50000.0
    assert components.customer_business_impact == 75000.0
    assert components.total_loss_magnitude == 825000.0


# ===========================================================================
# 2. Unit Tests: Event Frequency & Expected Annual Loss (EAL)
# ===========================================================================

def test_3_correct_annual_event_frequency():
    """Verify annual_event_frequency = baseline_annual_frequency * likelihood (1.0 * 0.40 = 0.40)."""
    freq = calculate_event_frequency(likelihood=0.40, baseline_annual_frequency=1.0)
    assert freq == 0.40


def test_4_correct_eal():
    """Verify Expected Annual Loss = annual_event_frequency * total_loss_magnitude (0.40 * 825,000 = 330,000)."""
    eal = calculate_eal(annual_event_frequency=0.40, total_loss_magnitude=825000.0)
    assert eal == 330000.0


def test_custom_baseline_annual_frequency():
    """Verify configurable baseline frequency scales event frequency and EAL."""
    freq = calculate_event_frequency(likelihood=0.40, baseline_annual_frequency=2.5)
    assert freq == 1.0  # 2.5 * 0.40 = 1.00
    eal = calculate_eal(annual_event_frequency=freq, total_loss_magnitude=825000.0)
    assert eal == 825000.0


# ===========================================================================
# 3. Edge Cases: Zero Downtime & Zero Optional Costs
# ===========================================================================

def test_5_zero_downtime():
    """Verify zero downtime produces 0 downtime loss while other costs remain intact."""
    dt_loss = calculate_downtime_loss(revenue_loss_per_hour=50000.0, downtime_hours=0.0)
    assert dt_loss == 0.0

    components = calculate_loss_magnitude(
        downtime_loss=dt_loss,
        incident_response_cost=100000.0,
        recovery_cost=200000.0,
        regulatory_legal_cost=50000.0,
        customer_business_impact=75000.0,
    )
    assert components.downtime_loss == 0.0
    assert components.total_loss_magnitude == 425000.0


def test_6_zero_optional_costs():
    """Verify zero optional costs results in total_loss_magnitude == downtime_loss."""
    components = calculate_loss_magnitude(
        downtime_loss=400000.0,
        incident_response_cost=0.0,
        recovery_cost=0.0,
        regulatory_legal_cost=0.0,
        customer_business_impact=0.0,
    )
    assert components.downtime_loss == 400000.0
    assert components.incident_response_cost == 0.0
    assert components.recovery_cost == 0.0
    assert components.regulatory_legal_cost == 0.0
    assert components.customer_business_impact == 0.0
    assert components.total_loss_magnitude == 400000.0


# ===========================================================================
# 4. Input Validation Failures
# ===========================================================================

def test_7_invalid_negative_monetary_values_rejected():
    """Verify negative revenue loss, recovery cost, or legal cost trigger validation errors."""
    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=0.40,
            risk_score=60.0,
            criticality="High",
            revenue_loss_per_hour=-50000.0,
            downtime_hours=8.0,
        )

    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=0.40,
            risk_score=60.0,
            criticality="High",
            revenue_loss_per_hour=50000.0,
            downtime_hours=8.0,
            recovery_cost=-200000.0,
        )


def test_8_invalid_likelihood_rejected():
    """Verify likelihood < 0 or > 1 is rejected."""
    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=-0.1,
            risk_score=60.0,
            criticality="High",
            revenue_loss_per_hour=50000.0,
            downtime_hours=8.0,
        )

    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=1.5,
            risk_score=60.0,
            criticality="High",
            revenue_loss_per_hour=50000.0,
            downtime_hours=8.0,
        )


def test_9_invalid_risk_score_rejected():
    """Verify risk score < 0 or > 100 is rejected."""
    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=0.40,
            risk_score=-5.0,
            criticality="High",
            revenue_loss_per_hour=50000.0,
            downtime_hours=8.0,
        )

    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=0.40,
            risk_score=105.0,
            criticality="High",
            revenue_loss_per_hour=50000.0,
            downtime_hours=8.0,
        )


def test_10_invalid_criticality_rejected():
    """Verify non-standard criticality values (e.g. 'Extreme') are rejected."""
    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=0.40,
            risk_score=60.0,
            criticality="Extreme",
            revenue_loss_per_hour=50000.0,
            downtime_hours=8.0,
        )


def test_11_negative_downtime_hours_rejected():
    """Verify negative downtime hours are rejected."""
    with pytest.raises(ValidationError):
        FinancialCRQInput(
            asset_id="AST-001",
            likelihood=0.40,
            risk_score=60.0,
            criticality="High",
            revenue_loss_per_hour=50000.0,
            downtime_hours=-8.0,
        )


# ===========================================================================
# 5. Full Pipeline & DEV 2 Contract Tests
# ===========================================================================

def test_full_financial_crq_pipeline():
    """Verify complete end-to-end Financial CRQ orchestrator calculation."""
    input_data = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "likelihood": 0.40,
        "risk_score": 60.0,
        "criticality": "High",
        "revenue_loss_per_hour": 50000.0,
        "downtime_hours": 8.0,
        "incident_response_cost": 100000.0,
        "recovery_cost": 200000.0,
        "regulatory_legal_cost": 50000.0,
        "customer_business_impact": 75000.0,
        "baseline_annual_frequency": 1.0,
        "currency": "INR",
    }
    result = calculate_financial_crq(input_data)

    assert result.asset_id == "AST-001"
    assert result.cve_id == "CVE-001"
    assert result.likelihood == 0.40
    assert result.baseline_annual_frequency == 1.0
    assert result.annual_event_frequency == 0.40
    assert result.downtime_loss == 400000.0
    assert result.incident_response_cost == 100000.0
    assert result.recovery_cost == 200000.0
    assert result.regulatory_legal_cost == 50000.0
    assert result.customer_business_impact == 75000.0
    assert result.total_loss_magnitude == 825000.0
    assert result.expected_annual_loss == 330000.0
    assert result.currency == "INR"
    assert result.model_version == FINANCIAL_MODEL_VERSION
    assert len(result.assumptions) >= 4
    assert len(result.explanation) >= 5

    mc = result.monte_carlo_input
    assert isinstance(mc, MonteCarloInput)
    assert mc.asset_id == "AST-001"
    assert mc.cve_id == "CVE-001"
    assert mc.annual_frequency_assumption == 0.40
    assert mc.downtime_hours == 8.0
    assert mc.revenue_loss_per_hour == 50000.0
    assert mc.incident_response_cost == 100000.0
    assert mc.recovery_cost == 200000.0
    assert mc.regulatory_legal_cost == 50000.0
    assert mc.customer_business_impact == 75000.0
    assert mc.loss_magnitude == 825000.0
    assert mc.likelihood == 0.40


def test_deterministic_explanation_content():
    """Verify explainability statements format numbers and formulas accurately."""
    components = LossComponents(
        downtime_loss=400000.0,
        incident_response_cost=100000.0,
        recovery_cost=200000.0,
        regulatory_legal_cost=50000.0,
        customer_business_impact=75000.0,
        total_loss_magnitude=825000.0,
    )
    explanations = generate_financial_explanation(
        likelihood=0.40,
        baseline_annual_frequency=1.0,
        annual_event_frequency=0.40,
        loss_components=components,
        eal=330000.0,
        currency="INR",
        downtime_hours=8.0,
        revenue_loss_per_hour=50000.0,
    )
    combined = "\n".join(explanations)
    assert "0.40 events/year" in combined
    assert "₹400,000.00" in combined
    assert "₹825,000.00" in combined
    assert "₹330,000.00" in combined


def test_bridge_from_risk_result():
    """Verify helper bridge from_risk_result seamlessly integrates Cyber Risk Engine output."""
    risk_output = RiskCalculationResponse(
        asset_id="AST-BRIDGE-01",
        cve_id="CVE-2026-9999",
        likelihood=0.75,
        impact=1.0,
        risk_score=75.0,
        risk_level="CRITICAL",
        risk_drivers=["Critical CVSS"],
        calculation=CalculationBreakdown(
            cvss_normalized=0.98,
            epss=0.82,
            kev_signal=1,
            exposure_signal=1,
            cvss_contribution=0.245,
            epss_contribution=0.328,
            kev_contribution=0.20,
            exposure_contribution=0.15,
        ),
        model=ModelInfo(version="risk-model-v1", type="deterministic"),
    )

    financial_params = {
        "criticality": "Critical",
        "revenue_loss_per_hour": 100000.0,
        "downtime_hours": 4.0,
        "incident_response_cost": 50000.0,
        "recovery_cost": 150000.0,
        "regulatory_legal_cost": 25000.0,
        "customer_business_impact": 50000.0,
    }

    crq_input = from_risk_result(risk_output, financial_params)
    assert crq_input.asset_id == "AST-BRIDGE-01"
    assert crq_input.cve_id == "CVE-2026-9999"
    assert crq_input.likelihood == 0.75
    assert crq_input.risk_score == 75.0
    assert crq_input.downtime_hours == 4.0

    result = calculate_financial_crq(crq_input)
    assert result.downtime_loss == 400000.0
    assert result.total_loss_magnitude == 675000.0
    assert result.annual_event_frequency == 0.75
    assert result.expected_annual_loss == 506250.0


# ===========================================================================
# 6. FastAPI API Endpoint Tests
# ===========================================================================

def test_api_financial_crq_calculate_endpoint():
    """Verify POST /financial-crq/calculate endpoint with test client."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "likelihood": 0.40,
        "risk_score": 60.0,
        "criticality": "High",
        "revenue_loss_per_hour": 50000.0,
        "downtime_hours": 8.0,
        "incident_response_cost": 100000.0,
        "recovery_cost": 200000.0,
        "regulatory_legal_cost": 50000.0,
        "customer_business_impact": 75000.0,
        "baseline_annual_frequency": 1.0,
        "currency": "INR",
    }
    response = client.post("/financial-crq/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "AST-001"
    assert data["cve_id"] == "CVE-001"
    assert data["downtime_loss"] == 400000.0
    assert data["total_loss_magnitude"] == 825000.0
    assert data["annual_event_frequency"] == 0.40
    assert data["expected_annual_loss"] == 330000.0
    assert data["currency"] == "INR"
    assert "monte_carlo_input" in data
    assert data["monte_carlo_input"]["loss_magnitude"] == 825000.0


def test_api_financial_crq_calculate_validation_error():
    """Verify POST /financial-crq/calculate returns 422 on invalid negative input."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    invalid_payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "likelihood": 0.40,
        "risk_score": 60.0,
        "criticality": "High",
        "revenue_loss_per_hour": -50000.0,  # Negative!
        "downtime_hours": 8.0,
    }
    response = client.post("/financial-crq/calculate", json=invalid_payload)
    assert response.status_code == 422


def test_api_financial_crq_health():
    """Verify GET /financial-crq/health endpoint."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/financial-crq/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["module"] == "financial-crq"
    assert data["model_version"] == FINANCIAL_MODEL_VERSION
