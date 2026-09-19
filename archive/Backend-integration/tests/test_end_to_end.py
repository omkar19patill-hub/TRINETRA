"""End-to-End Integration Tests for TRINETRA Cyber Risk Pipeline

Verifies the complete flow:
External Official Sources (NVD + EPSS + KEV)
  ↓
Ingestion & Normalization Layer
  ↓
SQLite Storage & Cache
  ↓
Internal API & Asset Join
  ↓
Direct Ingestion by TRINETRA Risk Engine (Backend-riskEngine)
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add both Backend-integration and Backend-riskEngine to sys.path
INTEGRATION_DIR = Path(__file__).resolve().parent.parent
RISK_ENGINE_DIR = INTEGRATION_DIR.parent / "Backend-riskEngine"

if str(INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_DIR))
if str(RISK_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(RISK_ENGINE_DIR))

from api.ingestion import set_ingestion_service
from cache.vulnerability_cache import VulnerabilityStorage
from ingestion.service import IngestionService
from integrations.cisa_kev import CISAKEVClient
from integrations.epss import EPSSClient
from integrations.mitre_attack import MitreAttackEnricher
from integrations.nvd import NVDClient
from main import app
from schemas.vulnerability import RawEPSSData, RawNVDData, SourceStatusEnum

# Import Risk Engine orchestrator from Backend-riskEngine (validating zero breaking changes)
try:
    from risk.engine import calculate_risk as risk_engine_calculate
    from risk.schemas import RiskCalculationRequest
    RISK_ENGINE_AVAILABLE = True
except ImportError:
    RISK_ENGINE_AVAILABLE = False


@pytest.fixture
def e2e_environment():
    """Setup isolated test environment for full E2E testing."""
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

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_complete_e2e_pipeline_to_risk_engine(e2e_environment, monkeypatch):
    """Full End-to-End Pipeline Execution:

    1. Mock official external APIs (NVD, EPSS).
    2. Ingest & normalize CVE-2024-3400 via POST /ingestion/vulnerability/CVE-2024-3400/refresh.
    3. Query cached enriched threat intelligence via GET /vulnerabilities/CVE-2024-3400/enriched.
    4. Join asset context (AST-FW-001, Critical, Internet-facing) via POST /vulnerabilities/risk-engine-payload.
    5. Pass generated payload directly into TRINETRA Risk Engine to compute Likelihood, Impact, and Risk Score.
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

    # Step 3: Query Enriched Endpoint (Cached, Zero-External-Call)
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
    risk_input = join_resp.json()

    assert risk_input["asset_id"] == "AST-FW-001"
    assert risk_input["cve_id"] == "CVE-2024-3400"
    assert risk_input["cvss"] == 10.0
    assert risk_input["epss"] == 0.93874
    assert risk_input["kev"] is True
    assert risk_input["internet_exposed"] is True
    assert risk_input["criticality"] == "Critical"

    # Step 5: Feed directly into TRINETRA Risk Engine
    if RISK_ENGINE_AVAILABLE:
        risk_req = RiskCalculationRequest(
            asset_id=risk_input["asset_id"],
            cve_id=risk_input["cve_id"],
            cvss=risk_input["cvss"],
            epss=risk_input["epss"],
            kev=risk_input["kev"],
            internet_exposed=risk_input["internet_exposed"],
            criticality=risk_input["criticality"],
        )
        risk_output = risk_engine_calculate(risk_req)

        assert risk_output.asset_id == "AST-FW-001"
        assert risk_output.cve_id == "CVE-2024-3400"
        assert risk_output.risk_level == "CRITICAL"
        assert risk_output.risk_score > 90.0  # High composite score
        assert risk_output.impact == 1.0  # Critical asset impact
        assert "Critical CVSS" in risk_output.risk_drivers
        assert "High exploitation probability" in risk_output.risk_drivers
        assert "Known exploited vulnerability" in risk_output.risk_drivers
        assert "Internet exposed asset" in risk_output.risk_drivers
        assert "Critical business asset" in risk_output.risk_drivers
