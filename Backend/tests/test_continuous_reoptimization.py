"""Comprehensive Automated Test Suite for Continuous Re-Optimization Orchestration (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Covers all 5 core simulation triggers & verification requirements:
1. Simulation 1: New KEV vulnerability cataloging -> Re-calculates risk, CRQ, Monte Carlo, and re-optimizes
2. Simulation 2: EPSS exploitation score change -> Detects delta, elevates likelihood and P95
3. Simulation 3: Asset perimeter exposure change -> Multiplies exposure factor and updates portfolio
4. Simulation 4: Patch applied / remediation -> Neutralizes vulnerability and lowers risk & loss
5. Simulation 5: Investment budget modification -> Re-runs optimization packing additional controls
6. Blockchain decision provenance preservation -> Confirms append-only ledger without overwriting history
7. Health & asset inventory endpoints
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from blockchain.provider import LocalLedgerBlockchainProvider, set_blockchain_provider, get_blockchain_provider
from blockchain.store import seed_benchmark_assessments
from decision.store import seed_benchmark_optimizations
from orchestration import ORCHESTRATION_MODEL_VERSION
from orchestration.state import seed_asset_registry, get_asset_state


@pytest.fixture(autouse=True)
def reset_all_stores():
    """Reset blockchain, decision, and asset registries before each test."""
    fresh_provider = LocalLedgerBlockchainProvider()
    set_blockchain_provider(fresh_provider)
    seed_benchmark_assessments()
    seed_benchmark_optimizations()
    seed_asset_registry()
    yield


def test_orchestration_health_and_assets_endpoint():
    """Verify GET /orchestration/health and /orchestration/assets return valid state."""
    with TestClient(app) as client:
        health_res = client.get("/orchestration/health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] == "ok"
        assert health_data["module"] == "continuous-reoptimization"
        assert health_data["version"] == ORCHESTRATION_MODEL_VERSION
        assert health_data["tracked_assets_count"] >= 4

        assets_res = client.get("/orchestration/assets")
        assert assets_res.status_code == 200
        assets = assets_res.json()
        assert len(assets) >= 4
        asset_ids = [a["asset_id"] for a in assets]
        assert "AST-001" in asset_ids
        assert "AST-002" in asset_ids


def test_simulation_1_new_kev_vulnerability():
    """Simulate Trigger 1: Vulnerability added to CISA KEV catalog."""
    with TestClient(app) as client:
        # Asset AST-001 initially has kev=False
        payload = {
            "asset_id": "AST-001",
            "cve_id": "CVE-2026-1234",
            "kev": True,
            "record_provenance": True,
        }

        response = client.post("/reoptimize", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "REOPTIMIZATION_COMPLETE"
        assert data["asset_id"] == "AST-001"
        assert data["cve_id"] == "CVE-2026-1234"

        # 1. Verify change reasons detected accurately
        assert any("CISA KEV" in r for r in data["change_reasons"])
        assert any("actively exploited" in r for r in data["change_reasons"])

        # 2. Verify deterministic risk recalculated upwards
        assert data["new_risk"]["score"] > data["previous_risk"]["score"]
        assert data["new_risk"]["likelihood"] > data["previous_risk"]["likelihood"]
        assert data["risk_delta"] > 0

        # 3. Verify Financial CRQ EAL recalculated upwards
        assert data["new_crq_eal"] > data["previous_crq_eal"]
        assert data["crq_eal_delta"] > 0

        # 4. Verify Monte Carlo P95 recalculated upwards
        assert data["new_p95"] > data["previous_p95"]
        assert data["p95_delta"] > 0

        # 5. Verify new optimization ID registered
        assert data["new_optimization_id"].startswith("OPT-")
        assert len(data["new_portfolio"]["selected_controls"]) > 0

        # 6. Verify blockchain provenance recorded
        assert data["provenance_recorded"] is True
        assert data["blockchain_receipt"] is not None
        assert data["blockchain_receipt"]["status"] == "RECORDED"
        assert data["blockchain_receipt"]["block_height"] >= 1


def test_simulation_2_epss_score_change():
    """Simulate Trigger 2: EPSS exploitation probability score updated from 0.45 to 0.92."""
    with TestClient(app) as client:
        payload = {
            "asset_id": "AST-001",
            "epss": 0.92,
            "record_provenance": True,
        }

        response = client.post("/reoptimize", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Check concrete change reasons
        assert any("EPSS exploitation probability changed" in r for r in data["change_reasons"])
        assert any("0.450" in r and "0.920" in r for r in data["change_reasons"])

        # Check risk and loss recalculation
        assert data["new_risk"]["score"] > data["previous_risk"]["score"]
        assert data["new_risk"]["likelihood"] > data["previous_risk"]["likelihood"]
        assert data["new_crq_eal"] > data["previous_crq_eal"]
        assert data["new_p95"] > data["previous_p95"]


def test_simulation_3_asset_exposure_change():
    """Simulate Trigger 3: Internal asset AST-002 becomes internet exposed."""
    with TestClient(app) as client:
        # Target AST-002 (baseline internet_exposed=False)
        payload = {
            "asset_id": "AST-002",
            "internet_exposed": True,
            "record_provenance": True,
        }

        response = client.post("/recalculate/AST-002", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Verify change reason
        assert any("became public internet-facing" in r for r in data["change_reasons"])

        # Risk score must increase due to exposure multiplier
        assert data["new_risk"]["score"] > data["previous_risk"]["score"]
        assert data["risk_delta"] > 0
        assert data["new_crq_eal"] > data["previous_crq_eal"]


def test_simulation_4_patch_applied():
    """Simulate Trigger 4: Critical vulnerability patched on AST-001."""
    with TestClient(app) as client:
        payload = {
            "asset_id": "AST-001",
            "is_patched": True,
            "record_provenance": True,
        }

        response = client.post("/reoptimize", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Verify change reason
        assert any("Patch deployed" in r and "mitigated" in r for r in data["change_reasons"])

        # Risk score and losses must drop sharply
        assert data["new_risk"]["score"] < data["previous_risk"]["score"]
        assert data["risk_delta"] < 0
        assert data["new_crq_eal"] < data["previous_crq_eal"]
        assert data["crq_eal_delta"] < 0
        assert data["new_p95"] < data["previous_p95"]


def test_simulation_5_budget_change():
    """Simulate Trigger 5: Cybersecurity investment budget increased from ₹1.8M to ₹2.5M."""
    with TestClient(app) as client:
        payload = {
            "asset_id": "AST-001",
            "budget_limit": 2500000.0,
            "record_provenance": True,
        }

        response = client.post("/reoptimize", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Verify change reason
        assert any("budget limit changed" in r for r in data["change_reasons"])
        assert any("2,500,000" in r for r in data["change_reasons"])

        # Control portfolio delta analysis
        delta = data["portfolio_delta"]
        assert delta["new_cost"] >= delta["previous_cost"] or delta["new_risk_reduction"] >= delta["previous_risk_reduction"]


def test_blockchain_provenance_preservation():
    """Verify continuous re-optimizations append to blockchain without overwriting history."""
    provider = get_blockchain_provider()

    with TestClient(app) as client:
        # Run 1: KEV trigger
        res1 = client.post("/reoptimize", json={"asset_id": "AST-001", "kev": True, "record_provenance": True})
        assert res1.status_code == 200
        data1 = res1.json()
        tx1 = data1["blockchain_receipt"]["tx_hash"]
        b1 = data1["blockchain_receipt"]["block_height"]

        # Run 2: EPSS trigger
        res2 = client.post("/reoptimize", json={"asset_id": "AST-001", "epss": 0.95, "record_provenance": True})
        assert res2.status_code == 200
        data2 = res2.json()
        tx2 = data2["blockchain_receipt"]["tx_hash"]
        b2 = data2["blockchain_receipt"]["block_height"]

        # Both records must be preserved in distinct blocks
        assert b2 > b1
        assert tx1 != tx2

        # Verify full blockchain integrity
        assert provider.verify_chain_integrity() is True
        assert len(provider.list_records()) >= 2


def test_root_endpoint_includes_reoptimization_metadata():
    """Verify root / info includes Continuous Re-Optimization metadata."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Continuous Re-Optimization" in data["modules"]
        assert "orchestration_model_version" in data
        assert data["orchestration_model_version"] == ORCHESTRATION_MODEL_VERSION
        assert data["endpoints"]["reoptimize"] == "/reoptimize"
        assert data["endpoints"]["recalculate_asset"] == "/recalculate/{asset_id}"
        assert data["endpoints"]["orchestration_health"] == "/orchestration/health"
