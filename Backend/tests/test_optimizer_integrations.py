"""Integration Tests: Optimizer with Decision Intelligence and Continuous Re-Optimization

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
1. Actual optimizer result reaches Decision Intelligence.
2. Benchmark data is not used by default.
3. Explicit demo mode uses benchmark data and labels it.
4. Actual optimizer failure returns a clear error.
16. Actual optimizer result includes source metadata.
17. Dashboard-facing response contains actual selected controls and financial values.
18. Re-optimization uses the actual optimizer.
19. Blockchain records the actual optimizer result hash.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from blockchain.provider import LocalLedgerBlockchainProvider, set_blockchain_provider
from blockchain.store import seed_benchmark_assessments
from decision.store import seed_benchmark_optimizations
from orchestration.state import seed_asset_registry


@pytest.fixture(autouse=True)
def reset_all_registries():
    """Reset provider and registries before each test."""
    set_blockchain_provider(LocalLedgerBlockchainProvider())
    seed_benchmark_assessments()
    seed_benchmark_optimizations()
    seed_asset_registry()
    yield


def test_1_actual_optimizer_result_reaches_decision_intelligence():
    """Verify actual optimizer output directly feeds Decision Intelligence without benchmark substitution."""
    with TestClient(app) as client:
        # Step 1: Run real optimizer for specific asset
        run_payload = {
            "budget_limit": 1500000.0,
            "asset_id": "AST-PROD-FINANCE",
            "asset_type": "database",
            "cvss": 9.9,
            "epss": 0.88,
            "kev": True,
            "internet_exposed": False,
            "criticality": "Critical",
            "revenue_loss_per_hour": 350000.0,
            "downtime_hours": 10.0,
            "record_to_decision_store": True,
        }
        run_res = client.post("/optimization/run", json=run_payload)
        assert run_res.status_code == 200
        run_data = run_res.json()
        opt_id = run_data["optimization_id"]
        assert opt_id.startswith("OPT-RUN-")

        # Step 2: Query Alternatives using the real optimization ID
        alt_res = client.get(f"/decision/{opt_id}/alternatives")
        assert alt_res.status_code == 200
        alt_data = alt_res.json()
        assert alt_data["optimization_id"] == opt_id
        assert alt_data["budget_limit"] == 1500000.0
        assert alt_data["data_source"] == "actual_optimizer"
        assert alt_data["is_benchmark"] is False
        assert len(alt_data["alternatives"]) >= 4

        # Step 3: Query Opportunity Cost for the real optimization
        opp_res = client.get(f"/decision/{opt_id}/opportunity-cost")
        assert opp_res.status_code == 200
        opp_data = opp_res.json()
        assert opp_data["optimization_id"] == opt_id
        assert opp_data["data_source"] == "actual_optimizer"
        assert opp_data["is_benchmark"] is False
        assert len(opp_data["comparisons"]) >= 3

        # Step 4: Query Marginal Budget Sensitivity for the real optimization
        mb_res = client.get(f"/decision/{opt_id}/marginal-budget")
        assert mb_res.status_code == 200
        mb_data = mb_res.json()
        assert mb_data["optimization_id"] == opt_id
        assert mb_data["base_budget"] == 1500000.0
        assert mb_data["data_source"] == "actual_optimizer"
        assert mb_data["is_benchmark"] is False
        assert len(mb_data["evaluations"]) >= 3

        # Step 5: Query Decision Explanation for the real optimization
        exp_res = client.get(f"/decision/{opt_id}/explanation")
        assert exp_res.status_code == 200
        exp_data = exp_res.json()
        assert isinstance(exp_data, list)
        assert len(exp_data) >= 5


def test_2_benchmark_data_is_not_used_by_default():
    """Verify that querying a missing actual optimization result returns 404 and does NOT silently return benchmark data."""
    with TestClient(app) as client:
        missing_id = "OPT-RUN-NONEXISTENT-999"
        res = client.get(f"/decision/{missing_id}/alternatives")
        assert res.status_code == 404
        data = res.json()
        assert "not found" in data["detail"].lower()
        assert "actual optimization result is unavailable" in data["detail"].lower()


def test_3_explicit_demo_mode_uses_benchmark_and_labels_it():
    """Verify explicit demo_mode=true returns benchmark data and labels it is_benchmark=true, data_source='benchmark'."""
    with TestClient(app) as client:
        # Query missing optimization ID with demo_mode=true
        missing_id = "OPT-RUN-UNKNOWN-123"
        res = client.get(f"/decision/{missing_id}/alternatives?demo_mode=true")
        assert res.status_code == 200
        data = res.json()
        assert data["is_benchmark"] is True
        assert data["data_source"] == "benchmark"
        assert data["optimization_id"] == "OPT-BENCHMARK-001"

        # Also query opportunity cost with demo_mode=true
        res_oc = client.get(f"/decision/{missing_id}/opportunity-cost?demo_mode=true")
        assert res_oc.status_code == 200
        data_oc = res_oc.json()
        assert data_oc["is_benchmark"] is True
        assert data_oc["data_source"] == "benchmark"


def test_4_actual_optimizer_failure_returns_clear_error():
    """Verify that actual optimizer failure (e.g. negative budget) returns a clear validation error without fallback."""
    with TestClient(app) as client:
        bad_payload = {
            "budget_limit": -500000.0,
            "asset_id": "AST-001",
        }
        res = client.post("/optimization/run", json=bad_payload)
        assert res.status_code == 422
        err_msg = str(res.json()).lower()
        assert "greater than or equal to 0" in err_msg or "non-negative" in err_msg



def test_16_actual_optimizer_result_includes_source_metadata():
    """Verify that POST /optimization/run attaches data_source, is_benchmark, model_version, and assessment_id."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": 1800000.0,
            "asset_id": "AST-METADATA-01",
            "asset_type": "web_application",
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["data_source"] == "actual_optimizer"
        assert data["is_benchmark"] is False
        assert data["model_version"] == "OPT-DET-1.0"
        assert data["assessment_id"] == "AST-METADATA-01"
        assert data["optimization_id"].startswith("OPT-RUN-")


def test_17_dashboard_facing_response_contains_actual_values():
    """Verify that dashboard-facing API returns all 14 required fields with genuine quantitative metrics."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": 2000000.0,
            "asset_id": "AST-DASHBOARD-TEST",
            "asset_type": "cloud_server",
            "cvss": 9.8,
            "epss": 0.85,
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 200
        data = res.json()

        # Check all 14 dashboard requirements
        assert "selected_controls" in data and len(data["selected_controls"]) > 0
        assert "rejected_controls" in data
        assert "total_cost" in data and data["total_cost"] > 0
        assert "remaining_budget" in data and data["remaining_budget"] >= 0
        assert "baseline_risk" in data and data["baseline_risk"] > 0
        assert "residual_risk" in data and data["residual_risk"] < data["baseline_risk"]
        assert "risk_reduction" in data and data["risk_reduction"] > 0
        assert "baseline_eal" in data and data["baseline_eal"] > 0
        assert "residual_eal" in data and data["residual_eal"] < data["baseline_eal"]
        assert "financial_loss_avoided" in data and data["financial_loss_avoided"] > 0
        assert "selection_reasons" in data and len(data["selection_reasons"]) > 0
        assert "rejection_reasons" in data
        assert data["model_version"] == "OPT-DET-1.0"
        assert data["data_source"] == "actual_optimizer"
        assert "dependency_resolution" in data and len(data["dependency_resolution"]) > 0


def test_18_19_reoptimization_uses_actual_optimizer_and_blockchain_hash():
    """Verify continuous re-optimization executes actual optimizer (both baseline and post) and anchors hash."""
    with TestClient(app) as client:
        payload = {
            "asset_id": "AST-001",
            "cvss": 9.9,
            "epss": 0.95,
            "budget_limit": 2200000.0,
            "record_provenance": True,
        }
        res = client.post("/reoptimize", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "REOPTIMIZATION_COMPLETE"
        assert data["asset_id"] == "AST-001"
        assert data["new_optimization_id"].startswith("OPT-AST-001-")
        assert len(data["new_portfolio"]["selected_controls"]) > 0

        # Verify baseline portfolio was computed by real optimizer, not fake benchmark
        assert data["previous_portfolio"]["total_cost"] > 0
        assert len(data["previous_portfolio"]["selected_controls"]) > 0

        # Verify portfolio delta computed
        delta = data["portfolio_delta"]
        assert delta["new_cost"] > 0
        assert delta["new_risk_reduction"] > 0

        # Verify blockchain anchoring of actual result
        assert data["provenance_recorded"] is True
        assert data["blockchain_receipt"] is not None
        assert data["blockchain_receipt"]["status"] == "RECORDED"
        assert len(data["blockchain_receipt"]["canonical_hash"]) == 64
