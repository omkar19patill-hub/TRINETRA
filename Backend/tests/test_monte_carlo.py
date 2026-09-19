"""Automated Unit and Integration Tests for Monte Carlo Cyber Risk Simulation

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Stochastic Uncertainty & Monte Carlo Simulation Layer
"""

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from monte_carlo.schemas import (
    MonteCarloInput,
    MonteCarloResult,
    HistogramBin,
    SimulateFromCRQRequest,
)
from monte_carlo.simulator import (
    run_simulation,
    compute_percentiles,
    build_histogram,
    build_monte_carlo_input_from_crq,
    MONTE_CARLO_MODEL_VERSION,
)
from financial_crq.schemas import FinancialCRQInput


@pytest.fixture
def base_mc_payload() -> dict:
    """Fixture providing a valid benchmark Monte Carlo simulation payload."""
    return {
        "asset_id": "AST-001",
        "cve_id": "CVE-001",
        "iterations": 10000,
        "seed": 42,
        "currency": "INR",
        "frequency_min": 0.20,
        "frequency_mode": 0.40,
        "frequency_max": 0.80,
        "downtime_hours_min": 4.0,
        "downtime_hours_mode": 8.0,
        "downtime_hours_max": 24.0,
        "revenue_loss_per_hour_min": 30000.0,
        "revenue_loss_per_hour_mode": 50000.0,
        "revenue_loss_per_hour_max": 75000.0,
        "incident_response_cost_min": 50000.0,
        "incident_response_cost_mode": 100000.0,
        "incident_response_cost_max": 180000.0,
        "recovery_cost_min": 100000.0,
        "recovery_cost_mode": 200000.0,
        "recovery_cost_max": 350000.0,
        "regulatory_legal_cost_min": 20000.0,
        "regulatory_legal_cost_mode": 50000.0,
        "regulatory_legal_cost_max": 120000.0,
        "customer_business_impact_min": 30000.0,
        "customer_business_impact_mode": 75000.0,
        "customer_business_impact_max": 150000.0,
    }


# ===========================================================================
# 1. Iteration Scale Tests (100, 1000, 10000)
# ===========================================================================

def test_1_simulation_100_iterations(base_mc_payload):
    """Verify simulation executes correctly with minimum 100 iterations."""
    base_mc_payload["iterations"] = 100
    result = run_simulation(base_mc_payload)
    assert result.iterations == 100
    assert result.mean_annual_loss > 0
    assert len(result.histogram) > 0


def test_2_simulation_1000_iterations(base_mc_payload):
    """Verify simulation executes correctly with 1,000 iterations."""
    base_mc_payload["iterations"] = 1000
    result = run_simulation(base_mc_payload)
    assert result.iterations == 1000
    assert result.mean_annual_loss > 0


def test_3_simulation_10000_iterations(base_mc_payload):
    """Verify simulation executes cleanly with benchmark 10,000 iterations."""
    base_mc_payload["iterations"] = 10000
    result = run_simulation(base_mc_payload)
    assert result.iterations == 10000
    assert result.mean_annual_loss > 0
    assert result.p50 > 0
    assert result.p90 > result.p50


# ===========================================================================
# 2. Input Validation Tests (Min/Mode/Max & Bounds)
# ===========================================================================

def test_4_valid_bounds_accepted(base_mc_payload):
    """Verify valid triangular parameters pass Pydantic schema validation."""
    model = MonteCarloInput(**base_mc_payload)
    assert model.frequency_mode == 0.40
    assert model.iterations == 10000


def test_5_mode_outside_min_max_rejected(base_mc_payload):
    """Verify mode < min or mode > max is rejected by validator."""
    bad_payload_1 = base_mc_payload.copy()
    bad_payload_1["downtime_hours_min"] = 10.0
    bad_payload_1["downtime_hours_mode"] = 5.0
    bad_payload_1["downtime_hours_max"] = 20.0
    with pytest.raises(ValidationError):
        MonteCarloInput(**bad_payload_1)

    bad_payload_2 = base_mc_payload.copy()
    bad_payload_2["frequency_min"] = 0.1
    bad_payload_2["frequency_mode"] = 0.9
    bad_payload_2["frequency_max"] = 0.5
    with pytest.raises(ValidationError):
        MonteCarloInput(**bad_payload_2)


def test_6_negative_costs_rejected(base_mc_payload):
    """Verify negative cost/duration parameters are rejected."""
    bad_payload = base_mc_payload.copy()
    bad_payload["incident_response_cost_min"] = -1000.0
    with pytest.raises(ValidationError):
        MonteCarloInput(**bad_payload)


def test_7_invalid_iteration_count_rejected(base_mc_payload):
    """Verify iteration counts < 100 or > 100,000 are rejected."""
    bad_low = base_mc_payload.copy()
    bad_low["iterations"] = 50
    with pytest.raises(ValidationError):
        MonteCarloInput(**bad_low)

    bad_high = base_mc_payload.copy()
    bad_high["iterations"] = 200000
    with pytest.raises(ValidationError):
        MonteCarloInput(**bad_high)


# ===========================================================================
# 3. Randomness & Statistical Properties
# ===========================================================================

def test_8_seeded_simulation_reproducibility(base_mc_payload):
    """Verify identical random seeds produce exactly identical simulation percentiles."""
    base_mc_payload["seed"] = 12345
    result1 = run_simulation(base_mc_payload)
    result2 = run_simulation(base_mc_payload)

    assert result1.mean_annual_loss == result2.mean_annual_loss
    assert result1.p50 == result2.p50
    assert result1.p75 == result2.p75
    assert result1.p90 == result2.p90
    assert result1.p95 == result2.p95
    assert result1.p99 == result2.p99
    assert result1.min_loss == result2.min_loss
    assert result1.max_loss == result2.max_loss


def test_9_monotonic_percentiles(base_mc_payload):
    """Verify statistical ordering: min <= P50 <= P75 <= P90 <= P95 <= P99 <= max."""
    result = run_simulation(base_mc_payload)
    assert result.min_loss <= result.p50
    assert result.p50 <= result.p75
    assert result.p75 <= result.p90
    assert result.p90 <= result.p95
    assert result.p95 <= result.p99
    assert result.p99 <= result.max_loss


def test_10_all_simulated_losses_non_negative(base_mc_payload):
    """Verify mean_annual_loss and min_loss are strictly non-negative."""
    result = run_simulation(base_mc_payload)
    assert result.min_loss >= 0.0
    assert result.mean_annual_loss >= 0.0
    assert result.p50 >= 0.0


def test_11_histogram_bin_integrity(base_mc_payload):
    """Verify sum of histogram bin counts equals total iterations and percentages sum to ~100%."""
    base_mc_payload["iterations"] = 5000
    result = run_simulation(base_mc_payload)

    total_count = sum(bin_item.count for bin_item in result.histogram)
    total_pct = sum(bin_item.percentage for bin_item in result.histogram)

    assert total_count == 5000
    assert pytest.approx(total_pct, 0.5) == 100.0


# ===========================================================================
# 4. Bridge Helper & DEV 1 Integration
# ===========================================================================

def test_bridge_from_crq_input():
    """Verify build_monte_carlo_input_from_crq constructs valid MonteCarloInput from DEV 1 CRQ input."""
    crq_input = FinancialCRQInput(
        asset_id="AST-CRQ-01",
        cve_id="CVE-2026-8888",
        likelihood=0.40,
        risk_score=60.0,
        criticality="High",
        revenue_loss_per_hour=50000.0,
        downtime_hours=8.0,
        incident_response_cost=100000.0,
        recovery_cost=200000.0,
        regulatory_legal_cost=50000.0,
        customer_business_impact=75000.0,
        baseline_annual_frequency=1.0,
        currency="INR",
    )

    mc_input = build_monte_carlo_input_from_crq(
        crq_input=crq_input,
        iterations=5000,
        seed=42,
        frequency_spread_min=0.5,
        frequency_spread_max=2.0,
        cost_spread_min=0.5,
        cost_spread_max=2.0,
    )

    assert mc_input.asset_id == "AST-CRQ-01"
    assert mc_input.frequency_mode == 0.40
    assert mc_input.frequency_min == 0.20
    assert mc_input.frequency_max == 0.80
    assert mc_input.downtime_hours_mode == 8.0
    assert mc_input.downtime_hours_min == 4.0
    assert mc_input.downtime_hours_max == 16.0

    result = run_simulation(mc_input)
    assert result.iterations == 5000
    assert result.mean_annual_loss > 0


# ===========================================================================
# 5. FastAPI Endpoint Integration Tests
# ===========================================================================

def test_12_api_simulate_endpoint(base_mc_payload):
    """Verify POST /monte-carlo/simulate endpoint with test client."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.post("/monte-carlo/simulate", json=base_mc_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["asset_id"] == "AST-001"
    assert data["iterations"] == 10000
    assert "mean_annual_loss" in data
    assert "p50" in data
    assert "p75" in data
    assert "p90" in data
    assert "p95" in data
    assert "p99" in data
    assert "histogram" in data
    assert len(data["histogram"]) > 0
    assert data["model_version"] == MONTE_CARLO_MODEL_VERSION


def test_13_api_simulate_from_crq_endpoint():
    """Verify POST /monte-carlo/from-crq bridge endpoint."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    payload = {
        "crq_input": {
            "asset_id": "AST-BRIDGE-02",
            "cve_id": "CVE-2026-7777",
            "likelihood": 0.50,
            "risk_score": 75.0,
            "criticality": "Critical",
            "revenue_loss_per_hour": 60000.0,
            "downtime_hours": 10.0,
            "incident_response_cost": 80000.0,
            "recovery_cost": 150000.0,
            "regulatory_legal_cost": 40000.0,
            "customer_business_impact": 60000.0,
            "baseline_annual_frequency": 1.0,
            "currency": "INR",
        },
        "iterations": 2000,
        "seed": 99,
        "frequency_spread_min": 0.5,
        "frequency_spread_max": 2.0,
        "cost_spread_min": 0.5,
        "cost_spread_max": 2.0,
    }
    response = client.post("/monte-carlo/from-crq", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "AST-BRIDGE-02"
    assert data["iterations"] == 2000
    assert data["mean_annual_loss"] > 0


def test_14_api_simulate_validation_error(base_mc_payload):
    """Verify POST /monte-carlo/simulate returns 422 on invalid parameters."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    invalid_payload = base_mc_payload.copy()
    invalid_payload["frequency_mode"] = 1.5

    response = client.post("/monte-carlo/simulate", json=invalid_payload)
    assert response.status_code == 422


def test_15_api_monte_carlo_health():
    """Verify GET /monte-carlo/health endpoint."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/monte-carlo/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["module"] == "monte-carlo"
    assert data["model_version"] == MONTE_CARLO_MODEL_VERSION
