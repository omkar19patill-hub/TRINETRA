"""Integration tests for FastAPI REST Endpoints

Tests API routes using FastAPI TestClient:
- GET /vulnerabilities/{cve_id}/enriched
- POST /vulnerabilities/risk-engine-payload (Asset Join)
- POST /ingestion/vulnerability/{cve_id}/refresh
- GET /ingestion/health
- GET /ingestion/status
- GET /vulnerabilities
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
from ingestion.service import IngestionService
from integrations.cisa_kev import CISAKEVClient
from integrations.epss import EPSSClient
from integrations.mitre_attack import MitreAttackEnricher
from integrations.nvd import NVDClient
from main import app, seed_benchmark_vulnerabilities
from schemas.vulnerability import RawEPSSData, RawNVDData, SourceStatusEnum


@pytest.fixture
def client_and_service():
    """Create a TestClient with a fresh temporary database."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    storage = VulnerabilityStorage(db_path=db_path)
    nvd = NVDClient()
    epss = EPSSClient()
    kev = CISAKEVClient()
    mitre = MitreAttackEnricher()

    # Pre-seed KEV
    kev.load_from_dict_list(
        [
            {
                "cveID": "CVE-2024-3400",
                "vendorProject": "Palo Alto Networks",
                "product": "PAN-OS",
                "dateAdded": "2024-04-12",
                "knownRansomwareCampaignUse": "Known",
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

    seed_benchmark_vulnerabilities(service)
    set_ingestion_service(service)

    test_client = TestClient(app)

    yield test_client, service

    set_ingestion_service(None)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


def test_api_get_enriched_benchmark_cve(client_and_service):
    """Test GET /vulnerabilities/{cve_id}/enriched retrieves seeded benchmark CVE."""
    client, _ = client_and_service

    response = client.get("/vulnerabilities/CVE-2026-1234/enriched")
    assert response.status_code == 200
    data = response.json()

    assert data["cve_id"] == "CVE-2026-1234"
    assert data["cvss"] == 9.8
    assert data["epss"] == 0.82
    assert data["kev"] is True
    assert data["source_metadata"]["cvss_source"] == "NVD"
    assert data["source_metadata"]["epss_source"] == "FIRST"
    assert data["source_metadata"]["kev_source"] == "CISA"


def test_api_asset_join_risk_payload(client_and_service):
    """Test POST /vulnerabilities/risk-engine-payload joins asset and returns Risk Engine schema."""
    client, _ = client_and_service

    payload = {
        "asset_id": "AST-001",
        "cve_id": "CVE-2026-1234",
        "internet_exposed": True,
        "criticality": "Critical",
    }

    response = client.post("/vulnerabilities/risk-engine-payload", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["asset_id"] == "AST-001"
    assert data["cve_id"] == "CVE-2026-1234"
    assert data["cvss"] == 9.8
    assert data["epss"] == 0.82
    assert data["kev"] is True
    assert data["internet_exposed"] is True
    assert data["criticality"] == "Critical"
    assert "metadata" in data


def test_api_refresh_single_cve(client_and_service, monkeypatch):
    """Test POST /ingestion/vulnerability/{cve_id}/refresh performs live sync."""
    client, service = client_and_service

    async def mock_nvd(cve_id):
        return RawNVDData(cve_id=cve_id, cvss_score=10.0, severity="CRITICAL", status=SourceStatusEnum.AVAILABLE)

    async def mock_epss(cve_id):
        return RawEPSSData(cve_id=cve_id, epss=0.95, percentile=0.99, status=SourceStatusEnum.AVAILABLE)

    monkeypatch.setattr(service.nvd, "fetch_cve", mock_nvd)
    monkeypatch.setattr(service.epss, "fetch_cve", mock_epss)

    response = client.post("/ingestion/vulnerability/CVE-2024-3400/refresh")
    assert response.status_code == 200
    data = response.json()

    assert data["cve_id"] == "CVE-2024-3400"
    assert data["nvd"]["cvss"] == 10.0
    assert data["epss"]["score"] == 0.95
    assert data["kev"]["is_known_exploited"] is True


def test_api_health_check(client_and_service, monkeypatch):
    """Test GET /ingestion/health returns active source statuses."""
    client, service = client_and_service

    async def mock_health():
        return "available"

    monkeypatch.setattr(service.nvd, "check_health", mock_health)
    monkeypatch.setattr(service.epss, "check_health", mock_health)
    monkeypatch.setattr(service.kev, "check_health", mock_health)

    response = client.get("/ingestion/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["sources"]["nvd"] == "available"
    assert data["sources"]["epss"] == "available"
    assert data["sources"]["cisa_kev"] == "available"
    assert data["sources"]["database"] == "available"


def test_api_status_telemetry(client_and_service):
    """Test GET /ingestion/status returns counts and sync times."""
    client, _ = client_and_service

    response = client.get("/ingestion/status")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "records" in data
    assert "cache_stats" in data
    assert "uptime_seconds" in data


def test_api_list_vulnerabilities(client_and_service):
    """Test GET /vulnerabilities lists cached entries."""
    client, _ = client_and_service

    response = client.get("/vulnerabilities?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 2
    assert len(data["vulnerabilities"]) >= 2


def test_api_invalid_cve_format(client_and_service):
    """Test that invalid CVE formats return 400 Bad Request."""
    client, _ = client_and_service

    response = client.get("/vulnerabilities/INVALID-CVE/enriched")
    assert response.status_code == 400
    assert "INVALID_CVE_FORMAT" in response.text
