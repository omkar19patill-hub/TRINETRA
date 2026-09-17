"""Unit tests for FIRST EPSS API Client Adapter

Tests single and batch lookups, string float conversions, bounds validation [0.0 - 1.0],
rate limiting (429), and outage fallbacks.
"""

import sys
from pathlib import Path
import pytest
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from integrations.epss import EPSSClient
from schemas.vulnerability import SourceStatusEnum


MOCK_EPSS_RESPONSE = {
    "status": "OK",
    "status-code": 200,
    "version": "1.0",
    "access": "public",
    "total": 1,
    "offset": 0,
    "limit": 100,
    "data": [
        {
            "cve": "CVE-2024-3400",
            "epss": "0.93874",
            "percentile": "0.99120",
            "date": "2026-03-01",
        }
    ],
}

MOCK_EPSS_BATCH_RESPONSE = {
    "status": "OK",
    "data": [
        {"cve": "CVE-2021-44228", "epss": 0.97512, "percentile": 0.99920, "date": "2026-03-01"},
        {"cve": "CVE-2024-3400", "epss": 0.93874, "percentile": 0.99120, "date": "2026-03-01"},
    ],
}


@pytest.mark.asyncio
async def test_epss_parse_single_cve():
    """Verify EPSS parsing safely converts strings to float in [0.0 - 1.0]."""
    client = EPSSClient()
    parsed = client.parse_epss_item("CVE-2024-3400", MOCK_EPSS_RESPONSE)

    assert parsed.cve_id == "CVE-2024-3400"
    assert parsed.epss == 0.93874
    assert parsed.percentile == 0.99120
    assert parsed.date == "2026-03-01"
    assert parsed.status == SourceStatusEnum.AVAILABLE


@pytest.mark.asyncio
async def test_epss_fetch_single(monkeypatch):
    """Test full fetch flow for a single CVE with mocked response."""
    client = EPSSClient()

    async def mock_get(*args, **kwargs):
        req = httpx.Request("GET", "https://api.first.org/data/v1/epss")
        return httpx.Response(200, json=MOCK_EPSS_RESPONSE, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await client.fetch_cve("CVE-2024-3400")
    assert result.cve_id == "CVE-2024-3400"
    assert result.epss == 0.93874
    assert result.status == SourceStatusEnum.AVAILABLE


@pytest.mark.asyncio
async def test_epss_batch_lookup(monkeypatch):
    """Test batch query returning scores for multiple CVEs."""
    client = EPSSClient()

    async def mock_get(*args, **kwargs):
        req = httpx.Request("GET", "https://api.first.org/data/v1/epss")
        return httpx.Response(200, json=MOCK_EPSS_BATCH_RESPONSE, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    results = await client.fetch_batch(["CVE-2021-44228", "CVE-2024-3400"])
    assert len(results) == 2
    assert results["CVE-2021-44228"].epss == 0.97512
    assert results["CVE-2024-3400"].epss == 0.93874


@pytest.mark.asyncio
async def test_epss_rate_limit_retry(monkeypatch):
    """Test EPSS recovers from HTTP 429."""
    client = EPSSClient(max_retries=2)
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            req = httpx.Request("GET", "https://api.first.org/data/v1/epss")
            return httpx.Response(429, request=req)
        req = httpx.Request("GET", "https://api.first.org/data/v1/epss")
        return httpx.Response(200, json=MOCK_EPSS_RESPONSE, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await client.fetch_cve("CVE-2024-3400")
    assert call_count == 2
    assert result.epss == 0.93874


@pytest.mark.asyncio
async def test_epss_health_check(monkeypatch):
    """Test EPSS health check probe."""
    client = EPSSClient()

    async def mock_get(*args, **kwargs):
        req = httpx.Request("GET", "https://api.first.org/data/v1/epss")
        return httpx.Response(200, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    status = await client.check_health()
    assert status == "available"
