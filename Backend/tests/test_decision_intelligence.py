"""Comprehensive Automated Tests for Decision Intelligence Layer (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
1. Alternative Portfolios Generation (/decision/{optimization_id}/alternatives)
2. Opportunity Cost Quantification & Neutral Language (/decision/{optimization_id}/opportunity-cost)
3. Marginal Value of Additional Budget (+₹5L, +₹10L, +₹25L) (/decision/{optimization_id}/marginal-budget)
4. Zero Additional Budget (+₹0) Edge Case Handling
5. Unavailable / Non-Existent Optimization ID Handling (HTTP 404)
6. Explainable Evidence Structures (Control, Selected, Reasons)
7. Custom Optimization Registration & Evaluation
8. Decision Health Endpoint & Root Integration
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from decision import DECISION_MODEL_VERSION
from decision.schemas import (
    CandidateControl,
    OptimizationResult,
    AlternativesResponse,
    OpportunityCostResponse,
    MarginalBudgetResponse,
)
from decision.store import seed_benchmark_optimizations, get_optimization, save_optimization


@pytest.fixture(autouse=True)
def reset_store():
    """Ensure benchmark optimizations are seeded before each test run."""
    seed_benchmark_optimizations()


def test_decision_health_endpoint():
    """Verify GET /decision/health returns operational status and model version."""
    with TestClient(app) as client:
        response = client.get("/decision/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "decision-intelligence"
        assert data["model_version"] == DECISION_MODEL_VERSION
        assert data["seeded_optimizations"] >= 1


def test_alternatives_endpoint_structure():
    """Verify GET /decision/{optimization_id}/alternatives returns all required structured fields."""
    with TestClient(app) as client:
        response = client.get("/decision/OPT-BENCHMARK-001/alternatives")
        assert response.status_code == 200
        data = response.json()

        assert data["optimization_id"] == "OPT-BENCHMARK-001"
        assert data["baseline_risk"] == 5000000.0
        assert data["budget_limit"] == 1800000.0
        assert data["currency"] == "INR"
        assert data["selected_portfolio_id"] == "portfolio-balanced-roi"
        assert len(data["alternatives"]) >= 4

        for alt in data["alternatives"]:
            assert "portfolio_id" in alt and isinstance(alt["portfolio_id"], str)
            assert "objective" in alt and isinstance(alt["objective"], str)
            assert "total_cost" in alt and isinstance(alt["total_cost"], (int, float))
            assert "risk_reduction" in alt and isinstance(alt["risk_reduction"], (int, float))
            assert "residual_risk" in alt and isinstance(alt["residual_risk"], (int, float))
            assert "workforce_hours" in alt and isinstance(alt["workforce_hours"], (int, float))
            assert "implementation_days" in alt and isinstance(alt["implementation_days"], int)
            assert "selected_controls" in alt and isinstance(alt["selected_controls"], list)
            assert len(alt["selected_controls"]) > 0
            
            assert round(alt["residual_risk"] + alt["risk_reduction"]) == round(data["baseline_risk"])


def test_opportunity_cost_endpoint_and_neutral_language():
    """Verify GET /decision/{optimization_id}/opportunity-cost calculates tradeoffs in strictly neutral language."""
    with TestClient(app) as client:
        response = client.get("/decision/OPT-BENCHMARK-001/opportunity-cost")
        assert response.status_code == 200
        data = response.json()

        assert data["optimization_id"] == "OPT-BENCHMARK-001"
        assert data["selected_portfolio_id"] == "portfolio-balanced-roi"
        assert data["selected_risk_reduction"] > 0
        assert data["selected_total_cost"] > 0
        assert len(data["comparisons"]) >= 3

        forbidden_words = ["bad", "terrible", "inferior", "poor", "worthless", "stupid", "wrong"]

        for comp in data["comparisons"]:
            assert "compared_portfolio_id" in comp
            assert "compared_objective" in comp
            assert "risk_reduction_difference" in comp
            assert "cost_difference" in comp
            assert "workforce_hours_difference" in comp
            assert "implementation_days_difference" in comp
            assert "tradeoff_narrative" in comp
            assert "controls_gained" in comp
            assert "controls_sacrificed" in comp

            narrative = comp["tradeoff_narrative"].lower()
            for bad_word in forbidden_words:
                assert bad_word not in narrative, f"Found non-neutral word '{bad_word}' in narrative: {comp['tradeoff_narrative']}"

            assert "under the same constraints" in narrative
            assert ("less modeled reduction" in narrative) or ("more modeled reduction" in narrative) or ("equivalent modeled reduction" in narrative)


def test_marginal_budget_endpoint_standard_tiers():
    """Verify GET /decision/{optimization_id}/marginal-budget evaluates +₹5L, +₹10L, and +₹25L."""
    with TestClient(app) as client:
        response = client.get("/decision/OPT-BENCHMARK-001/marginal-budget")
        assert response.status_code == 200
        data = response.json()

        assert data["optimization_id"] == "OPT-BENCHMARK-001"
        assert data["base_budget"] == 1800000.0
        assert data["base_risk_reduction"] > 0
        assert len(data["evaluations"]) == 3

        budgets_evaluated = [e["additional_budget"] for e in data["evaluations"]]
        assert budgets_evaluated == [500000.0, 1000000.0, 2500000.0]

        for eval_item in data["evaluations"]:
            assert "additional_budget" in eval_item
            assert "additional_risk_reduction" in eval_item
            assert "marginal_reduction_per_rupee" in eval_item
            assert eval_item["additional_budget"] > 0
            assert eval_item["total_budget"] == data["base_budget"] + eval_item["additional_budget"]
            assert eval_item["marginal_reduction_per_rupee"] == round(
                eval_item["additional_risk_reduction"] / eval_item["additional_budget"], 4
            )


def test_marginal_budget_zero_additional_budget():
    """Verify marginal budget handles +₹0 additional budget edge case without division by zero."""
    with TestClient(app) as client:
        response = client.get("/decision/OPT-BENCHMARK-001/marginal-budget?increments=0")
        assert response.status_code == 200
        data = response.json()

        assert len(data["evaluations"]) == 1
        eval_0 = data["evaluations"][0]
        assert eval_0["additional_budget"] == 0.0
        assert eval_0["additional_risk_reduction"] == 0.0
        assert eval_0["marginal_reduction_per_rupee"] == 0.0
        assert eval_0["total_budget"] == data["base_budget"]
        assert eval_0["total_risk_reduction"] == data["base_risk_reduction"]
        assert eval_0["additional_controls_selected"] == []
        assert "Baseline Budget" in eval_0["efficiency_assessment"]


def test_unavailable_optimization_id_returns_404():
    """Verify that querying non-existent optimization IDs returns HTTP 404 across all endpoints."""
    non_existent_id = "NON-EXISTENT-OPT-999"
    with TestClient(app) as client:
        resp_alt = client.get(f"/decision/{non_existent_id}/alternatives")
        assert resp_alt.status_code == 404
        assert "not found" in resp_alt.json()["detail"].lower()

        resp_oc = client.get(f"/decision/{non_existent_id}/opportunity-cost")
        assert resp_oc.status_code == 404
        assert "not found" in resp_oc.json()["detail"].lower()

        resp_mb = client.get(f"/decision/{non_existent_id}/marginal-budget")
        assert resp_mb.status_code == 404
        assert "not found" in resp_mb.json()["detail"].lower()

        resp_exp = client.get(f"/decision/{non_existent_id}/explanation")
        assert resp_exp.status_code == 404
        assert "not found" in resp_exp.json()["detail"].lower()


def test_explainable_evidence_structure():
    """Verify structured explainability evidence format matches required schema."""
    with TestClient(app) as client:
        response = client.get("/decision/OPT-BENCHMARK-001/explanation")
        assert response.status_code == 200
        explanations = response.json()

        assert isinstance(explanations, list)
        assert len(explanations) == 10

        mfa_item = next((e for e in explanations if "MFA" in e["control"]), None)
        assert mfa_item is not None
        assert mfa_item["selected"] is True
        assert isinstance(mfa_item["reasons"], list)
        assert len(mfa_item["reasons"]) >= 2

        rejected = [e for e in explanations if not e["selected"]]
        assert len(rejected) > 0
        for rej in rejected:
            assert rej["selected"] is False
            assert len(rej["reasons"]) > 0


def test_custom_optimization_registration():
    """Verify registering a custom optimization scenario and querying its decision intelligence."""
    custom_opt = {
        "optimization_id": "OPT-CUSTOM-TEST-001",
        "title": "Cloud Native SaaS Infrastructure Optimization",
        "baseline_risk": 3000000.0,
        "budget_limit": 1000000.0,
        "currency": "INR",
        "selected_portfolio_id": "portfolio-balanced-roi",
        "candidate_controls": [
            {
                "control_id": "CTRL-1",
                "name": "Cloud IAM Governance",
                "cost": 300000.0,
                "risk_reduction": 700000.0,
                "workforce_hours": 40.0,
                "implementation_days": 10,
                "applicable_assets": ["AST-101", "AST-102"],
                "critical_assets_covered": 2,
                "category": "Identity",
            },
            {
                "control_id": "CTRL-2",
                "name": "Container Runtime Security",
                "cost": 500000.0,
                "risk_reduction": 900000.0,
                "workforce_hours": 60.0,
                "implementation_days": 15,
                "applicable_assets": ["AST-101", "AST-103"],
                "critical_assets_covered": 2,
                "category": "Cloud Security",
            },
            {
                "control_id": "CTRL-3",
                "name": "API Security Shield",
                "cost": 400000.0,
                "risk_reduction": 500000.0,
                "workforce_hours": 50.0,
                "implementation_days": 12,
                "applicable_assets": ["AST-102"],
                "critical_assets_covered": 1,
                "category": "Application Security",
            },
        ],
    }

    with TestClient(app) as client:
        reg_resp = client.post("/decision/register", json=custom_opt)
        assert reg_resp.status_code == 201

        alt_resp = client.get("/decision/OPT-CUSTOM-TEST-001/alternatives")
        assert alt_resp.status_code == 200

        oc_resp = client.get("/decision/OPT-CUSTOM-TEST-001/opportunity-cost")
        assert oc_resp.status_code == 200

        mb_resp = client.get("/decision/OPT-CUSTOM-TEST-001/marginal-budget?increments=200000,500000")
        assert mb_resp.status_code == 200
