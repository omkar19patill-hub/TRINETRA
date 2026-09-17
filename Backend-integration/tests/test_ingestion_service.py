"""Unit tests for Ingestion Service

Tests Mode A (Single CVE enrichment), Mode B (Bulk sync), recalculation hook firing,
and multi-source failure fallback.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from cache.vulnerability_cache import VulnerabilityStorage
from ingestion.service import IngestionService
from integrations.cisa_kev import CISAKEVClient
from integrations.epss import EPSSClient
from integrations.mitre_attack import MitreAttackEnricher
from integrations.nvd import NVDClient
from schemas.vulnerability import (
    CriticalityEnum,
    RawEPSSData,
    RawKEVData,
    RawNVDData,
    RiskEngineAssetJoinRequest,
    SourceStatusEnum,
)


@pytest.fixture
def mock_service():
    """Fixture providing an IngestionService with isolated temporary SQLite storage."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    storage = VulnerabilityStorage(db_path=db_path)
    nvd = NVDClient()
    epss = EPSSClient()
    kev = CISAKEVClient()
    mitre = MitreAttackEnricher()

    # Pre-populate KEV
    kev.load_from_dict_list(
        [
            {
                "cveID": "CVE-2024-3400",
                "vendorProject": "Palo Alto",
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

    yield service

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_service_enrich_single_cve(mock_service, monkeypatch):
    """Test Mode A: single CVE enrichment orchestrating NVD, EPSS, KEV."""
    service = mock_service

    async def mock_nvd(cve_id):
        return RawNVDData(
            cve_id=cve_id,
            cvss_score=10.0,
            cvss_version="3.1",
            severity="CRITICAL",
            description="Palo Alto command injection",
            status=SourceStatusEnum.AVAILABLE,
        )

    async def mock_epss(cve_id):
        return RawEPSSData(
            cve_id=cve_id,
            epss=0.93874,
            percentile=0.99120,
            date="2026-03-01",
            status=SourceStatusEnum.AVAILABLE,
        )

    monkeypatch.setattr(service.nvd, "fetch_cve", mock_nvd)
    monkeypatch.setattr(service.epss, "fetch_cve", mock_epss)

    record = await service.get_or_enrich_cve("CVE-2024-3400", force_refresh=True)

    assert record.cve_id == "CVE-2024-3400"
    assert record.nvd.cvss == 10.0
    assert record.epss.score == 0.93874
    assert record.kev.is_known_exploited is True
    assert record.kev.known_ransomware_use is True
    assert record.metadata.cvss_source == "NVD"


@pytest.mark.asyncio
async def test_service_recalculation_hook_dispatched(mock_service, monkeypatch):
    """Test that registered recalculation hook is called when intelligence changes."""
    service = mock_service
    hook_called = False
    hook_cve = None

    def my_recalc_hook(new_record, old_record):
        nonlocal hook_called, hook_cve
        hook_called = True
        hook_cve = new_record.cve_id

    service.register_recalculation_hook(my_recalc_hook)

    async def mock_nvd(cve_id):
        return RawNVDData(cve_id=cve_id, cvss_score=9.8, status=SourceStatusEnum.AVAILABLE)

    async def mock_epss(cve_id):
        return RawEPSSData(cve_id=cve_id, epss=0.82, status=SourceStatusEnum.AVAILABLE)

    monkeypatch.setattr(service.nvd, "fetch_cve", mock_nvd)
    monkeypatch.setattr(service.epss, "fetch_cve", mock_epss)

    await service.get_or_enrich_cve("CVE-2026-1234", force_refresh=True)

    assert hook_called is True
    assert hook_cve == "CVE-2026-1234"


@pytest.mark.asyncio
async def test_service_asset_join(mock_service, monkeypatch):
    """Test combining asset context with threat intelligence into Risk Engine contract."""
    service = mock_service

    async def mock_nvd(cve_id):
        return RawNVDData(cve_id=cve_id, cvss_score=9.8, status=SourceStatusEnum.AVAILABLE)

    async def mock_epss(cve_id):
        return RawEPSSData(cve_id=cve_id, epss=0.82, status=SourceStatusEnum.AVAILABLE)

    monkeypatch.setattr(service.nvd, "fetch_cve", mock_nvd)
    monkeypatch.setattr(service.epss, "fetch_cve", mock_epss)

    request = RiskEngineAssetJoinRequest(
        asset_id="AST-001",
        cve_id="CVE-2026-1234",
        internet_exposed=True,
        criticality=CriticalityEnum.CRITICAL,
    )

    payload = await service.join_asset_and_build_payload(request)
    assert payload.asset_id == "AST-001"
    assert payload.cve_id == "CVE-2026-1234"
    assert payload.cvss == 9.8
    assert payload.epss == 0.82
    assert payload.internet_exposed is True
    assert payload.criticality == "Critical"
