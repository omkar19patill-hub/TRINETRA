"""Unit tests for Normalization Module

Tests normalization of disparate feeds into UnifiedVulnerabilityRecord,
preservation of source provenance, and transformation into Risk Engine contracts.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from normalization.vulnerability_normalizer import (
    normalize_vulnerability_record,
    to_enriched_response,
    to_risk_engine_payload,
)
from schemas.vulnerability import (
    CriticalityEnum,
    RawEPSSData,
    RawKEVData,
    RawNVDData,
    RiskEngineAssetJoinRequest,
    SourceStatusEnum,
)


def test_normalize_full_sources():
    """Test normalization when all three primary sources provide data."""
    nvd_data = RawNVDData(
        cve_id="CVE-2024-3400",
        cvss_score=10.0,
        cvss_version="3.1",
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        severity="CRITICAL",
        published_date="2024-04-12T17:15:49Z",
        last_modified_date="2024-04-18T18:15:08Z",
        description="Palo Alto PAN-OS command injection",
        status=SourceStatusEnum.AVAILABLE,
    )

    epss_data = RawEPSSData(
        cve_id="CVE-2024-3400",
        epss=0.93874,
        percentile=0.99120,
        date="2026-03-01",
        status=SourceStatusEnum.AVAILABLE,
    )

    kev_data = RawKEVData(
        cve_id="CVE-2024-3400",
        is_known_exploited=True,
        date_added="2024-04-12",
        known_ransomware_use=True,
        required_action="Apply vendor mitigation immediately.",
        due_date="2024-04-19",
        status=SourceStatusEnum.AVAILABLE,
    )

    record = normalize_vulnerability_record(
        cve_id="CVE-2024-3400",
        nvd_data=nvd_data,
        epss_data=epss_data,
        kev_data=kev_data,
    )

    assert record.cve_id == "CVE-2024-3400"
    assert record.nvd.cvss == 10.0
    assert record.nvd.cvss_version == "3.1"
    assert record.epss.score == 0.93874
    assert record.kev.is_known_exploited is True
    assert record.kev.known_ransomware_use is True
    assert record.metadata.cvss_source == "NVD"
    assert record.metadata.epss_source == "FIRST"
    assert record.metadata.kev_source == "CISA"
    assert "NVD" in record.metadata.sources
    assert record.data_freshness.nvd_last_modified == "2024-04-18T18:15:08Z"


def test_to_enriched_response():
    """Test conversion to internal EnrichedVulnerabilityResponse contract."""
    record = normalize_vulnerability_record(
        cve_id="CVE-2024-3400",
        nvd_data=RawNVDData(cve_id="CVE-2024-3400", cvss_score=9.8, severity="CRITICAL"),
        epss_data=RawEPSSData(cve_id="CVE-2024-3400", epss=0.82),
        kev_data=RawKEVData(cve_id="CVE-2024-3400", is_known_exploited=True),
    )

    enriched = to_enriched_response(record)
    assert enriched.cve_id == "CVE-2024-3400"
    assert enriched.cvss == 9.8
    assert enriched.epss == 0.82
    assert enriched.kev is True
    assert enriched.source_metadata.cvss_source == "NVD"


def test_to_risk_engine_payload():
    """Test Asset Join converting threat data into exact Risk Engine schema."""
    record = normalize_vulnerability_record(
        cve_id="CVE-2024-3400",
        nvd_data=RawNVDData(cve_id="CVE-2024-3400", cvss_score=9.8),
        epss_data=RawEPSSData(cve_id="CVE-2024-3400", epss=0.82),
        kev_data=RawKEVData(cve_id="CVE-2024-3400", is_known_exploited=True),
    )

    join_req = RiskEngineAssetJoinRequest(
        asset_id="AST-001",
        cve_id="CVE-2024-3400",
        internet_exposed=True,
        criticality=CriticalityEnum.CRITICAL,
    )

    payload = to_risk_engine_payload(join_req, record)
    assert payload.asset_id == "AST-001"
    assert payload.cve_id == "CVE-2024-3400"
    assert payload.cvss == 9.8
    assert payload.epss == 0.82
    assert payload.kev is True
    assert payload.internet_exposed is True
    assert payload.criticality == "Critical"
    assert payload.metadata["cvss_source"] == "NVD"
