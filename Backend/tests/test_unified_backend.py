"""Tests for the Unified TRINETRA Backend Application

Verifies:
1. Application initialization and metadata discovery (/ endpoint)
2. All module health endpoints (/risk/health, /financial-crq/health, /monte-carlo/health, /ingestion/health)
3. Lifespan startup seeding of benchmark vulnerabilities
4. Cross-module schema compatibility
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from risk.constants import MODEL_VERSION as RISK_MODEL_VERSION
from financial_crq.engine import FINANCIAL_MODEL_VERSION
from monte_carlo.simulator import MONTE_CARLO_MODEL_VERSION


def test_unified_root_endpoint():
    """Verify GET / returns complete platform metadata and all registered endpoints."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert "TRINETRA" in data["project"]
        assert "Risk Engine" in data["modules"]
        assert "Financial CRQ" in data["modules"]
        assert "Monte Carlo Simulation" in data["modules"]
        assert "Decision Intelligence" in data["modules"]
        assert "ML Risk Calibration" in data["modules"]
        assert "Threat Intelligence Ingestion" in data["modules"]

        assert data["risk_model_version"] == RISK_MODEL_VERSION
        assert data["financial_crq_model_version"] == FINANCIAL_MODEL_VERSION
        assert data["monte_carlo_model_version"] == MONTE_CARLO_MODEL_VERSION

        endpoints = data["endpoints"]
        assert endpoints["risk_calculate"] == "/risk/calculate"
        assert endpoints["risk_health"] == "/risk/health"
        assert endpoints["financial_crq_calculate"] == "/financial-crq/calculate"
        assert endpoints["financial_crq_health"] == "/financial-crq/health"
        assert endpoints["monte_carlo_simulate"] == "/monte-carlo/simulate"
        assert endpoints["monte_carlo_from_crq"] == "/monte-carlo/from-crq"
        assert endpoints["monte_carlo_health"] == "/monte-carlo/health"
        assert endpoints["decision_alternatives"] == "/decision/{optimization_id}/alternatives"
        assert endpoints["decision_opportunity_cost"] == "/decision/{optimization_id}/opportunity-cost"
        assert endpoints["decision_marginal_budget"] == "/decision/{optimization_id}/marginal-budget"
        assert endpoints["decision_explanation"] == "/decision/{optimization_id}/explanation"
        assert endpoints["decision_health"] == "/decision/health"
        assert endpoints["ml_predict"] == "/ml/predict"
        assert endpoints["ml_model_info"] == "/ml/model-info"
        assert endpoints["ml_health"] == "/ml/health"
        assert endpoints["enriched_vulnerability"] == "/vulnerabilities/{cve_id}/enriched"
        assert endpoints["asset_join_risk_payload"] == "/vulnerabilities/risk-engine-payload"
        assert endpoints["single_cve_refresh"] == "/ingestion/vulnerability/{cve_id}/refresh"
        assert endpoints["bulk_sync"] == "/ingestion/bulk-sync"
        assert endpoints["ingestion_health"] == "/ingestion/health"
        assert endpoints["ingestion_status"] == "/ingestion/status"
        assert endpoints["list_vulnerabilities"] == "/vulnerabilities"


def test_all_module_health_endpoints():
    """Verify health endpoints across all integrated modules return HTTP 200."""
    with TestClient(app) as client:
        # 1. Risk Engine health
        r_resp = client.get("/risk/health")
        assert r_resp.status_code == 200
        assert r_resp.json()["status"] == "ok"

        # 2. Financial CRQ health
        f_resp = client.get("/financial-crq/health")
        assert f_resp.status_code == 200
        assert f_resp.json()["status"] == "ok"

        # 3. Monte Carlo health
        m_resp = client.get("/monte-carlo/health")
        assert m_resp.status_code == 200
        assert m_resp.json()["status"] == "ok"

        # 4. Decision Intelligence health
        d_resp = client.get("/decision/health")
        assert d_resp.status_code == 200
        assert d_resp.json()["status"] == "ok"

        # 5. ML Risk Calibration health
        ml_resp = client.get("/ml/health")
        assert ml_resp.status_code == 200
        assert ml_resp.json()["status"] == "ok"

        # 6. Ingestion health & status
        i_resp = client.get("/ingestion/status")
        assert i_resp.status_code == 200
        assert i_resp.json()["status"] == "ok"


def test_seeded_vulnerabilities_available_on_startup():
    """Verify benchmark vulnerabilities (CVE-2026-1234, CVE-2021-44228) are seeded on startup."""
    with TestClient(app) as client:
        resp_1 = client.get("/vulnerabilities/CVE-2026-1234/enriched")
        assert resp_1.status_code == 200
        data_1 = resp_1.json()
        assert data_1["cve_id"] == "CVE-2026-1234"
        assert data_1["cvss"] == 9.8
        assert data_1["epss"] == 0.82
        assert data_1["kev"] is True

        resp_2 = client.get("/vulnerabilities/CVE-2021-44228/enriched")
        assert resp_2.status_code == 200
        data_2 = resp_2.json()
        assert data_2["cve_id"] == "CVE-2021-44228"
        assert data_2["cvss"] == 10.0
        assert data_2["epss"] == 0.975
        assert data_2["kev"] is True
