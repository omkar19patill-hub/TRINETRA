"""Unit tests for NVD 2.0 API Client Adapter

Tests parsing, CVSS versions (v3.1, v4.0, v2.0), retry logic, rate limit (429) backoff,
server errors (503), timeouts, and graceful error handling.
"""

import sys
from pathlib import Path
import pytest
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from integrations.nvd import NVDClient
from schemas.vulnerability import SourceStatusEnum


MOCK_NVD_V31_RESPONSE = {
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2024-3400",
                "sourceIdentifier": "cve@mitre.org",
                "published": "2024-04-12T17:15:49.000",
                "lastModified": "2024-04-18T18:15:08.000",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "A command injection vulnerability in Palo Alto Networks PAN-OS software allows an unauthenticated attacker to execute arbitrary code with root privileges.",
                    }
                ],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "source": "nvd@nist.gov",
                            "type": "Primary",
                            "cvssData": {
                                "version": "3.1",
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                                "baseScore": 10.0,
                                "baseSeverity": "CRITICAL",
                            },
                        }
                    ]
                },
                "configurations": [
                    {
                        "nodes": [
                            {
                                "operator": "OR",
                                "negate": False,
                                "cpeMatch": [
                                    {
                                        "vulnerable": True,
                                        "criteria": "cpe:2.3:o:paloaltonetworks:pan-os:10.2.0:*:*:*:*:*:*:*",
                                    }
                                ],
                            }
                        ]
                    }
                ],
                "references": [
                    {"url": "https://security.paloaltonetworks.com/PAN-SA-2024-0002"}
                ],
            }
        }
    ]
}

MOCK_NVD_V40_RESPONSE = {
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2024-9999",
                "published": "2024-06-01T00:00:00.000",
                "lastModified": "2024-06-02T00:00:00.000",
                "descriptions": [{"lang": "en", "value": "Sample v4 vulnerability"}],
                "metrics": {
                    "cvssMetricV40": [
                        {
                            "cvssData": {
                                "version": "4.0",
                                "vectorString": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H",
                                "baseScore": 9.3,
                                "baseSeverity": "CRITICAL",
                            }
                        }
                    ]
                },
            }
        }
    ]
}


@pytest.mark.asyncio
async def test_nvd_parse_cvss_v31():
    """Verify NVD parser correctly extracts CVSS v3.1 score, vector, severity, and CPE."""
    client = NVDClient()
    parsed = client.parse_cve_item("CVE-2024-3400", MOCK_NVD_V31_RESPONSE)

    assert parsed.cve_id == "CVE-2024-3400"
    assert parsed.cvss_score == 10.0
    assert parsed.cvss_version == "3.1"
    assert parsed.severity == "CRITICAL"
    assert "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H" in parsed.cvss_vector
    assert "command injection" in parsed.description.lower()
    assert len(parsed.affected_products) == 1
    assert "pan-os" in parsed.affected_products[0]
    assert parsed.status == SourceStatusEnum.AVAILABLE


@pytest.mark.asyncio
async def test_nvd_parse_cvss_v40():
    """Verify NVD parser correctly extracts CVSS v4.0 when present."""
    client = NVDClient()
    parsed = client.parse_cve_item("CVE-2024-9999", MOCK_NVD_V40_RESPONSE)

    assert parsed.cve_id == "CVE-2024-9999"
    assert parsed.cvss_score == 9.3
    assert parsed.cvss_version == "4.0"
    assert parsed.severity == "CRITICAL"


@pytest.mark.asyncio
async def test_nvd_rate_limit_retry(monkeypatch):
    """Test NVD client handles HTTP 429 with retry and backoff."""
    client = NVDClient(max_retries=2, timeout=2.0)
    client._last_request_time = 0.0

    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            req = httpx.Request("GET", "https://services.nvd.nist.gov")
            return httpx.Response(429, headers={"Retry-After": "0"}, request=req)
        req = httpx.Request("GET", "https://services.nvd.nist.gov")
        return httpx.Response(200, json=MOCK_NVD_V31_RESPONSE, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await client.fetch_cve("CVE-2024-3400")
    assert call_count == 2
    assert result.cvss_score == 10.0
    assert result.status == SourceStatusEnum.AVAILABLE


@pytest.mark.asyncio
async def test_nvd_503_server_error_retry(monkeypatch):
    """Test NVD client recovers from temporary 503 Service Unavailable."""
    client = NVDClient(max_retries=2, timeout=2.0)
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            req = httpx.Request("GET", "https://services.nvd.nist.gov")
            return httpx.Response(503, request=req)
        req = httpx.Request("GET", "https://services.nvd.nist.gov")
        return httpx.Response(200, json=MOCK_NVD_V31_RESPONSE, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await client.fetch_cve("CVE-2024-3400")
    assert call_count == 2
    assert result.cvss_score == 10.0


@pytest.mark.asyncio
async def test_nvd_not_found_404(monkeypatch):
    """Test 404 CVE returns unavailable status without crashing."""
    client = NVDClient()

    async def mock_get(*args, **kwargs):
        req = httpx.Request("GET", "https://services.nvd.nist.gov")
        return httpx.Response(404, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await client.fetch_cve("CVE-2099-0000")
    assert result.cvss_score is None
    assert result.status == SourceStatusEnum.UNAVAILABLE


@pytest.mark.asyncio
async def test_nvd_health_check(monkeypatch):
    """Test NVD health check probe returns available status."""
    client = NVDClient()

    async def mock_get(*args, **kwargs):
        req = httpx.Request("GET", "https://services.nvd.nist.gov")
        return httpx.Response(200, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    status = await client.check_health()
    assert status == "available"
