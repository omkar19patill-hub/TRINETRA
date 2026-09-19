"""End-to-End Integration Tests for Unified TRINETRA Cyber Risk Pipeline

Verifies the complete flow:
External Official Sources (NVD + EPSS + KEV + MITRE ATT&CK)
  ↓
Ingestion & Normalization Layer
  ↓
SQLite Storage & Cache
  ↓
Internal API & Asset Join (/vulnerabilities/risk-engine-payload)
  ↓
Cyber Risk Engine (/risk/calculate)
  ↓
Financial CRQ Engine (/financial-crq/calculate)
  ↓
Monte Carlo Simulation (/monte-carlo/simulate or /monte-carlo/from-crq)
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.ingestion import set_ingestion_service
from cache.vulnerability_cache import VulnerabilityStorage
from financial_crq.engine import calculate_financial_crq, from_risk_result
from ingestion.service import IngestionService
from integrations.cisa_kev import CISAKEVClient
from integrations.epss import EPSSClient
from integrations.mitre_attack import MitreAttackEnricher
from integrations.nvd import NVDClient
from main import app
from monte_carlo.simulator import build_monte_carlo_input_from_crq, run_simulation
from risk.engine import calculate_risk
from risk.schemas import RiskCalculationRequest
from schemas.vulnerability import RawEPSSData, RawNVDData, SourceStatusEnum


@pytest.fixture
def e2e_environment():
    """Setup isolated test environment for full E2E pipeline testing."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    storage = VulnerabilityStorage(db_path=db_path)
    nvd = NVDClient()
    epss = EPSSClient()
    kev = CISAKEVClient()
    mitre = MitreAttackEnricher()

    # Pre-seed KEV catalog entry for Palo Alto zero-day
    kev.load_from_dict_list(
        [
            {
                "cveID": "CVE-2024-3400",
                "vendorProject": "Palo Alto Networks",
                "product": "PAN-OS",
                "vulnerabilityName": "PAN-OS OS Command Injection",
                "dateAdded": "2024-04-12",
                "knownRansomwareCampaignUse": "Known",
                "requiredAction": "Apply vendor mitigations immediately.",
                "dueDate": "2024-04-19",
            }
        ]
    )

    service = IngestionService(
        nvd_client=nvd,
        epss_client=epss,
        kev_client=kev,
        mitre_enricher=mitre,
        storage=storage,
    )
    set_ingestion_service(service)

    client = TestClient(app)

    yield client, service

    set_ingestion_service(None)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_complete_e2e_pipeline_ingestion_to_monte_carlo(e2e_environment, monkeypatch):
    """Full End-to-End Pipeline Execution:

    1. Mock official external APIs (NVD, EPSS).
    2. Ingest & normalize CVE-2024-3400 via POST /ingestion/vulnerability/CVE-2024-3400/refresh.
    3. Query cached enriched threat intelligence via GET /vulnerabilities/CVE-2024-3400/enriched.
    4. Join asset context (AST-FW-001, Critical, Internet-facing) via POST /vulnerabilities/risk-engine-payload.
    5. Pass generated payload into Risk Engine (POST /risk/calculate).
    6. Bridge Risk Engine output into Financial CRQ (POST /financial-crq/calculate).
    7. Bridge Financial CRQ output into Monte Carlo Simulation (POST /monte-carlo/from-crq).
    """
    client, service = e2e_environment

    # Step 1: Mock external API adapters
    async def mock_nvd(cve_id):
        return RawNVDData(
            cve_id="CVE-2024-3400",
            cvss_score=10.0,
            cvss_version="3.1",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            severity="CRITICAL",
            description="Palo Alto Networks PAN-OS command injection vulnerability allowing unauthenticated root execution.",
            published_date="2024-04-12T17:15:49Z",
            last_modified_date="2024-04-18T18:15:08Z",
            status=SourceStatusEnum.AVAILABLE,
        )

    async def mock_epss(cve_id):
        return RawEPSSData(
            cve_id="CVE-2024-3400",
            epss=0.93874,
            percentile=0.99120,
            date="2026-03-01",
            status=SourceStatusEnum.AVAILABLE,
        )

    monkeypatch.setattr(service.nvd, "fetch_cve", mock_nvd)
    monkeypatch.setattr(service.epss, "fetch_cve", mock_epss)

    # Step 2: Ingest & Refresh CVE-2024-3400
    refresh_resp = client.post("/ingestion/vulnerability/CVE-2024-3400/refresh")
    assert refresh_resp.status_code == 200
    unified_data = refresh_resp.json()

    assert unified_data["cve_id"] == "CVE-2024-3400"
    assert unified_data["nvd"]["cvss"] == 10.0
    assert unified_data["epss"]["score"] == 0.93874
    assert unified_data["kev"]["is_known_exploited"] is True
    assert unified_data["kev"]["known_ransomware_use"] is True
    assert unified_data["metadata"]["cvss_source"] == "NVD"
    assert unified_data["metadata"]["epss_source"] == "FIRST"
    assert unified_data["metadata"]["kev_source"] == "CISA"

    # Step 3: Query Enriched Endpoint (Cached)
    enriched_resp = client.get("/vulnerabilities/CVE-2024-3400/enriched")
    assert enriched_resp.status_code == 200
    enriched_data = enriched_resp.json()

    assert enriched_data["cve_id"] == "CVE-2024-3400"
    assert enriched_data["cvss"] == 10.0
    assert enriched_data["epss"] == 0.93874
    assert enriched_data["kev"] is True

    # Step 4: Asset Join
    asset_join_payload = {
        "asset_id": "AST-FW-001",
        "cve_id": "CVE-2024-3400",
        "internet_exposed": True,
        "criticality": "Critical",
    }
    join_resp = client.post("/vulnerabilities/risk-engine-payload", json=asset_join_payload)
    assert join_resp.status_code == 200
    risk_payload = join_resp.json()

    assert risk_payload["asset_id"] == "AST-FW-001"
    assert risk_payload["cve_id"] == "CVE-2024-3400"
    assert risk_payload["cvss"] == 10.0
    assert risk_payload["epss"] == 0.93874
    assert risk_payload["kev"] is True
    assert risk_payload["internet_exposed"] is True
    assert risk_payload["criticality"] == "Critical"

    # Step 5: Feed into Risk Engine Endpoint
    risk_calc_resp = client.post(
        "/risk/calculate",
        json={
            "asset_id": risk_payload["asset_id"],
            "cve_id": risk_payload["cve_id"],
            "cvss": risk_payload["cvss"],
            "epss": risk_payload["epss"],
            "kev": risk_payload["kev"],
            "internet_exposed": risk_payload["internet_exposed"],
            "criticality": risk_payload["criticality"],
        },
    )
    assert risk_calc_resp.status_code == 200
    risk_result = risk_calc_resp.json()

    assert risk_result["asset_id"] == "AST-FW-001"
    assert risk_result["cve_id"] == "CVE-2024-3400"
    assert risk_result["risk_level"] == "CRITICAL"
    assert risk_result["risk_score"] > 90.0
    assert risk_result["impact"] == 1.0
    assert "Critical CVSS" in risk_result["risk_drivers"]
    assert "Known exploited vulnerability" in risk_result["risk_drivers"]

    # Step 6: Feed into Financial CRQ Endpoint
    financial_crq_payload = {
        "asset_id": risk_result["asset_id"],
        "cve_id": risk_result["cve_id"],
        "likelihood": risk_result["likelihood"],
        "risk_score": risk_result["risk_score"],
        "criticality": "Critical",
        "revenue_loss_per_hour": 100000.0,
        "downtime_hours": 12.0,
        "incident_response_cost": 150000.0,
        "recovery_cost": 250000.0,
        "regulatory_legal_cost": 100000.0,
        "customer_business_impact": 100000.0,
        "baseline_annual_frequency": 1.0,
        "currency": "INR",
    }
    crq_resp = client.post("/financial-crq/calculate", json=financial_crq_payload)
    assert crq_resp.status_code == 200
    crq_result = crq_resp.json()

    # Downtime loss = 100,000 * 12 = 1,200,000
    # Total loss magnitude = 1,200,000 + 150,000 + 250,000 + 100,000 + 100,000 = 1,800,000
    assert crq_result["downtime_loss"] == 1200000.0
    assert crq_result["total_loss_magnitude"] == 1800000.0
    assert crq_result["expected_annual_loss"] > 0
    assert "monte_carlo_input" in crq_result

    # Step 7: Feed into Monte Carlo Simulation Endpoint via /from-crq
    mc_from_crq_payload = {
        "crq_input": financial_crq_payload,
        "iterations": 5000,
        "seed": 42,
        "frequency_spread_min": 0.5,
        "frequency_spread_max": 2.0,
        "cost_spread_min": 0.5,
        "cost_spread_max": 2.0,
    }
    mc_resp = client.post("/monte-carlo/from-crq", json=mc_from_crq_payload)
    assert mc_resp.status_code == 200
    mc_result = mc_resp.json()

    assert mc_result["asset_id"] == "AST-FW-001"
    assert mc_result["iterations"] == 5000
    assert mc_result["mean_annual_loss"] > 0
    assert mc_result["min_loss"] <= mc_result["p50"] <= mc_result["p90"] <= mc_result["max_loss"]
    assert len(mc_result["histogram"]) > 0
