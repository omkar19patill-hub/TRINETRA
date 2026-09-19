"""Unit tests for Multi-Tier Storage and Cache

Tests SQLite schema initialization, atomic upserts on cve_id, in-memory LRU caching,
query filtering, and audit response retrieval.
"""

import os
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from cache.vulnerability_cache import VulnerabilityStorage
from normalization.vulnerability_normalizer import normalize_vulnerability_record
from schemas.vulnerability import RawEPSSData, RawKEVData, RawNVDData


def safe_cleanup(path: str):
    """Safely remove a temporary database file."""
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def test_storage_insert_and_get():
    """Test inserting a record and retrieving it from storage."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    try:
        storage = VulnerabilityStorage(db_path=db_path, max_memory_entries=10)
        record = normalize_vulnerability_record(
            cve_id="CVE-2024-3400",
            nvd_data=RawNVDData(cve_id="CVE-2024-3400", cvss_score=10.0, severity="CRITICAL"),
            epss_data=RawEPSSData(cve_id="CVE-2024-3400", epss=0.938),
            kev_data=RawKEVData(cve_id="CVE-2024-3400", is_known_exploited=True),
        )

        assert storage.upsert_vulnerability(record) is True

        cached = storage.get_vulnerability("CVE-2024-3400")
        assert cached is not None
        assert cached.cve_id == "CVE-2024-3400"
        assert cached.nvd.cvss == 10.0
        assert cached.epss.score == 0.938
        assert cached.kev.is_known_exploited is True

    finally:
        safe_cleanup(db_path)


def test_storage_upsert_update():
    """Test that upserting an existing CVE updates fields instead of duplicating."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    try:
        storage = VulnerabilityStorage(db_path=db_path)

        record_v1 = normalize_vulnerability_record(
            cve_id="CVE-2024-1234",
            nvd_data=RawNVDData(cve_id="CVE-2024-1234", cvss_score=7.5),
            epss_data=RawEPSSData(cve_id="CVE-2024-1234", epss=0.50),
        )
        storage.upsert_vulnerability(record_v1)

        record_v2 = normalize_vulnerability_record(
            cve_id="CVE-2024-1234",
            nvd_data=RawNVDData(cve_id="CVE-2024-1234", cvss_score=7.5),
            epss_data=RawEPSSData(cve_id="CVE-2024-1234", epss=0.85),
            kev_data=RawKEVData(cve_id="CVE-2024-1234", is_known_exploited=True),
        )
        storage.upsert_vulnerability(record_v2)

        storage._mem_cache.clear()

        fetched = storage.get_vulnerability("CVE-2024-1234")
        assert fetched is not None
        assert fetched.epss.score == 0.85
        assert fetched.kev.is_known_exploited is True

        stats = storage.get_stats()
        assert stats["db_total_count"] == 1

    finally:
        safe_cleanup(db_path)


def test_storage_list_filtering():
    """Test filtering vulnerabilities by KEV presence and minimum CVSS score."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    try:
        storage = VulnerabilityStorage(db_path=db_path)

        r1 = normalize_vulnerability_record(
            cve_id="CVE-2024-0001",
            nvd_data=RawNVDData(cve_id="CVE-2024-0001", cvss_score=9.8),
            kev_data=RawKEVData(cve_id="CVE-2024-0001", is_known_exploited=True),
        )
        r2 = normalize_vulnerability_record(
            cve_id="CVE-2024-0002",
            nvd_data=RawNVDData(cve_id="CVE-2024-0002", cvss_score=5.0),
            kev_data=RawKEVData(cve_id="CVE-2024-0002", is_known_exploited=False),
        )
        storage.upsert_vulnerability(r1)
        storage.upsert_vulnerability(r2)

        items_kev, count_kev = storage.list_vulnerabilities(kev_only=True)
        assert count_kev == 1
        assert items_kev[0].cve_id == "CVE-2024-0001"

        items_high, count_high = storage.list_vulnerabilities(min_cvss=9.0)
        assert count_high == 1
        assert items_high[0].cve_id == "CVE-2024-0001"

    finally:
        safe_cleanup(db_path)
