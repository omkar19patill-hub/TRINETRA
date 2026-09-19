"""Unit tests for CISA Known Exploited Vulnerabilities (KEV) Catalog Client Adapter

Tests catalog indexing, O(1) in-memory lookup, ransomware flag detection,
and ensures absence from KEV returns kev=False without raising errors.
"""

import sys
from pathlib import Path
import pytest
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from integrations.cisa_kev import CISAKEVClient
from schemas.vulnerability import SourceStatusEnum

MOCK_KEV_FEED = {
    "title": "CISA Known Exploited Vulnerabilities Catalog",
    "catalogVersion": "2026.03.01",
    "dateReleased": "2026-03-01T00:00:00.000Z",
    "count": 2,
    "vulnerabilities": [
        {
            "cveID": "CVE-2024-3400",
            "vendorProject": "Palo Alto Networks",
            "product": "PAN-OS",
            "vulnerabilityName": "Palo Alto Networks PAN-OS OS Command Injection Vulnerability",
            "dateAdded": "2024-04-12",
            "shortDescription": "Palo Alto Networks PAN-OS contains an OS command injection vulnerability.",
            "requiredAction": "Apply mitigations per vendor instructions or discontinue use.",
            "dueDate": "2024-04-19",
            "knownRansomwareCampaignUse": "Known",
            "notes": "https://nvd.nist.gov/vuln/detail/CVE-2024-3400",
        },
        {
            "cveID": "CVE-2023-23397",
            "vendorProject": "Microsoft",
            "product": "Outlook",
            "vulnerabilityName": "Microsoft Outlook Elevation of Privilege Vulnerability",
            "dateAdded": "2023-03-14",
            "shortDescription": "Microsoft Outlook contains an elevation of privilege vulnerability.",
            "requiredAction": "Apply updates per vendor instructions.",
            "dueDate": "2023-04-04",
            "knownRansomwareCampaignUse": "Unknown",
            "notes": "",
        },
    ],
}


@pytest.mark.asyncio
async def test_cisa_kev_refresh_and_lookup(monkeypatch):
    """Test full feed download, indexing, and lookup for listed CVE."""
    client = CISAKEVClient()

    async def mock_get(*args, **kwargs):
        req = httpx.Request("GET", "https://www.cisa.gov/feeds/kev.json")
        return httpx.Response(200, json=MOCK_KEV_FEED, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    count = await client.refresh_catalog()
    assert count == 2
    assert client.catalog_size == 2

    entry = client.lookup_cve("CVE-2024-3400")
    assert entry.cve_id == "CVE-2024-3400"
    assert entry.is_known_exploited is True
    assert entry.known_ransomware_use is True
    assert entry.vendor_project == "Palo Alto Networks"
    assert entry.due_date == "2024-04-19"
    assert entry.status == SourceStatusEnum.AVAILABLE

    entry_ms = client.lookup_cve("CVE-2023-23397")
    assert entry_ms.is_known_exploited is True
    assert entry_ms.known_ransomware_use is False


def test_cisa_kev_unlisted_cve():
    """Verify that unlisted CVE returns is_known_exploited=False cleanly without error."""
    client = CISAKEVClient()
    client.load_from_dict_list(MOCK_KEV_FEED["vulnerabilities"])

    entry = client.lookup_cve("CVE-2099-1234")
    assert entry.cve_id == "CVE-2099-1234"
    assert entry.is_known_exploited is False
    assert entry.known_ransomware_use is False
    assert entry.status == SourceStatusEnum.AVAILABLE


@pytest.mark.asyncio
async def test_cisa_kev_network_failure_fallback(monkeypatch):
    """Test catalog refresh network failure gracefully preserves existing catalog."""
    client = CISAKEVClient()
    client.load_from_dict_list(MOCK_KEV_FEED["vulnerabilities"])
    assert client.catalog_size == 2

    async def mock_get(*args, **kwargs):
        raise httpx.ConnectError("CISA network timeout")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    count = await client.refresh_catalog()
    assert count == 2
    assert client.lookup_cve("CVE-2024-3400").is_known_exploited is True
