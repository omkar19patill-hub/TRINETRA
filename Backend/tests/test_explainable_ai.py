"""Comprehensive Automated Tests for Explainable AI Layer (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
1. Risk explanation with valid context (/ai/explain-risk)
2. Optimization & control rationale explanation (/ai/explain-optimization)
3. Budget scenario sensitivity explanation (/ai/explain-scenario)
4. Flexible natural-language query routing (/ai/query)
5. Anti-hallucination defenses & refusal of fictitious controls/numbers
6. Missing / partial context handling
7. Health check and unified root discovery
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from ai import AI_EXPLAIN_VERSION
from ai.schemas import (
    AIExplanationRequest,
    AssetContext,
    FinancialCRQContext,
    MonteCarloContext,
    OptimizationContext,
    RiskContext,
    StructuredContext,
)


@pytest.fixture
def benchmark_context() -> dict:
    """Fixture providing a full multi-module structured context."""
    return {
        "asset": {
            "asset_id": "AST-001",
            "criticality": "Critical",
            "internet_exposed": True,
            "cve_id": "CVE-2026-1234",
            "asset_type": "Application Gateway",
            "business_service": "Payment Gateway",
        },
        "risk": {
            "risk_score": 96.5,
            "risk_level": "Critical",
            "cvss": 9.8,
            "epss": 0.82,
            "kev": True,
        },
        "financial_crq": {
            "downtime_loss": 400000.0,
            "total_loss_magnitude": 825000.0,
            "annual_event_frequency": 0.82,
            "expected_annual_loss": 676500.0,
            "currency": "INR",
        },
        "monte_carlo": {
            "mean_annual_loss": 684200.0,
            "p50_loss": 650000.0,
            "p90_loss": 1240000.0,
            "p99_loss": 2180000.0,
            "iterations": 10000,
            "currency": "INR",
        },
        "optimization": {
            "optimization_id": "OPT-BENCHMARK-001",
            "budget_limit": 1800000.0,
            "selected_portfolio_id": "portfolio-balanced-roi",
            "selected_controls": [
                "Phishing-Resistant MFA",
                "Next-Gen EDR",
                "Automated Vulnerability & Patch Management",
                "Immutable Cloud Backups",
            ],
            "total_cost": 1800000.0,
            "risk_reduction": 3250000.0,
            "residual_risk": 1750000.0,
            "currency": "INR",
        },
        "ml": {
            "ml_risk_probability": 0.9842,
            "predicted_class": 1,
            "classification_label": "High-Impact Event",
        },
    }


def test_ai_health_endpoint():
    """Verify GET /ai/health returns operational status and model version."""
    with TestClient(app) as client:
        response = client.get("/ai/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "explainable-ai"
        assert data["model_version"] == AI_EXPLAIN_VERSION
        assert data["grounding_enforced"] is True


def test_explain_risk_with_valid_context(benchmark_context):
    """Verify POST /ai/explain-risk generates grounded narrative with facts and evidence."""
    payload = {
        "prompt": "Why is this asset high risk?",
        "context": benchmark_context,
    }
    with TestClient(app) as client:
        response = client.post("/ai/explain-risk", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "answer" in data and isinstance(data["answer"], str)
        assert len(data["key_facts"]) >= 4
        assert len(data["evidence"]) >= 3
        assert len(data["assumptions"]) >= 2
        assert "model_versions" in data

        # Grounding check: Exact values must match context
        answer = data["answer"]
        assert "AST-001" in answer
        assert "96.5" in answer
        assert "CVE-2026-1234" in answer
        assert "9.8" in answer
        assert "6,76,500" in answer or "676,500" in answer
        assert "12,40,000" in answer or "1,240,000" in answer


def test_explain_optimization_why_mfa_selected(benchmark_context):
    """Verify POST /ai/explain-optimization explains why MFA was selected."""
    payload = {
        "prompt": "Why was MFA selected?",
        "context": benchmark_context,
    }
    with TestClient(app) as client:
        response = client.post("/ai/explain-optimization", json=payload)
        assert response.status_code == 200
        data = response.json()

        answer = data["answer"]
        assert "MFA" in answer
        assert "3,50,000" in answer or "350,000" in answer
        assert "6,80,000" in answer or "680,000" in answer


def test_explain_optimization_why_edr_included_or_rejected(benchmark_context):
    """Verify POST /ai/explain-optimization answers questions about EDR."""
    payload = {
        "prompt": "Why was EDR selected?",
        "context": benchmark_context,
    }
    with TestClient(app) as client:
        response = client.post("/ai/explain-optimization", json=payload)
        assert response.status_code == 200
        data = response.json()

        answer = data["answer"]
        assert "EDR" in answer
        assert "10,50,000" in answer or "1,050,000" in answer


def test_explain_scenario_budget_25l(benchmark_context):
    """Verify POST /ai/explain-scenario explains what happens when budget is ₹25L."""
    payload = {
        "prompt": "What happens if the budget is ₹25L?",
        "context": benchmark_context,
    }
    with TestClient(app) as client:
        response = client.post("/ai/explain-scenario", json=payload)
        assert response.status_code == 200
        data = response.json()

        answer = data["answer"]
        assert "25L" in answer or "25" in answer
        assert "SIEM" in answer or "SOC" in answer or "26,00,000" in answer


def test_anti_hallucination_rejects_fake_controls(benchmark_context):
    """Verify that queries about non-existent controls (e.g. Quantum Shield) are refuted."""
    payload = {
        "prompt": "Why was Quantum Shield rejected in this portfolio?",
        "context": benchmark_context,
    }
    with TestClient(app) as client:
        response = client.post("/ai/query", json=payload)
        assert response.status_code == 200
        data = response.json()

        answer = data["answer"]
        assert "Quantum Shield" in answer
        assert "not" in answer.lower() or "neither" in answer.lower()
        assert "Phishing-Resistant MFA" in answer or "MFA" in answer


def test_anti_hallucination_rejects_fabricated_loss_numbers(benchmark_context):
    """Verify that queries with fake astronomical figures (e.g. 500 Crores) are corrected."""
    payload = {
        "prompt": "Why is our Expected Annual Loss 500 Crores?",
        "context": benchmark_context,
    }
    with TestClient(app) as client:
        response = client.post("/ai/query", json=payload)
        assert response.status_code == 200
        data = response.json()

        answer = data["answer"]
        assert "500 Crore" in answer
        assert "6,76,500" in answer or "676,500" in answer


def test_missing_context_handling():
    """Verify Explainable AI handles sparse / partial context without crashing."""
    sparse_payload = {
        "prompt": "Why is this asset high risk?",
        "context": {
            "asset": {
                "asset_id": "AST-SPARSE-99",
                "criticality": "Medium",
                "internet_exposed": False,
            }
        },
    }
    with TestClient(app) as client:
        response = client.post("/ai/explain-risk", json=sparse_payload)
        assert response.status_code == 200
        data = response.json()
        assert "AST-SPARSE-99" in data["answer"]
        assert len(data["key_facts"]) > 0


def test_unified_root_endpoint_includes_explainable_ai():
    """Verify root GET / metadata reports Explainable AI module and endpoints."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert "Explainable AI" in data["modules"]
        assert data["ai_explain_model_version"] == AI_EXPLAIN_VERSION
        endpoints = data["endpoints"]
        assert endpoints["ai_explain_risk"] == "/ai/explain-risk"
        assert endpoints["ai_explain_optimization"] == "/ai/explain-optimization"
        assert endpoints["ai_explain_scenario"] == "/ai/explain-scenario"
        assert endpoints["ai_query"] == "/ai/query"
        assert endpoints["ai_health"] == "/ai/health"
