"""NVD 2.0 API Client Adapter

Official API Specification: https://nvd.nist.gov/developers/vulnerabilities
Base Endpoint: https://services.nvd.nist.gov/rest/json/cves/2.0

Handles NVD API authentication (optional apiKey header), exponential backoff,
jitter, 429 rate-limiting, 5xx server errors, timeouts, and CVSS normalization.
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from config import settings
from schemas.vulnerability import RawNVDData, SourceStatusEnum
from validation.vulnerability_validator import validate_cve_id, validate_cvss_score

logger = logging.getLogger("trinetra.integrations.nvd")


class NVDClient:
    """Async client for National Vulnerability Database (NVD) 2.0 API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.NVD_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.NVD_API_KEY
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.MAX_RETRIES
        self._last_request_time = 0.0

    def _get_headers(self) -> Dict[str, str]:
        """Generate headers with apiKey if configured."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "TRINETRA-CyberRisk-Platform/1.0",
        }
        if self.api_key:
            headers["apiKey"] = self.api_key
        return headers

    async def _rate_limit_throttle(self):
        """Enforce spacing between consecutive requests to respect NVD limits."""
        # NVD without key: 5 requests per 30 seconds -> 6.0s spacing
        # NVD with key: 50 requests per 30 seconds -> 0.6s spacing
        min_interval = 0.6 if self.api_key else 6.0
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    async def _execute_with_retry(
        self, client: httpx.AsyncClient, url: str, params: Dict[str, Any]
    ) -> httpx.Response:
        """Execute HTTP request with exponential backoff, jitter, and 429/5xx handling."""
        attempt = 0
        backoff_base = settings.RETRY_BACKOFF_BASE

        while attempt <= self.max_retries:
            await self._rate_limit_throttle()
            try:
                logger.debug(
                    "[NVD] Requesting %s (params: %s, attempt: %d)",
                    url,
                    params,
                    attempt + 1,
                )
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                )

                # 429 Too Many Requests
                if response.status_code == 429:
                    attempt += 1
                    retry_after_hdr = response.headers.get("Retry-After")
                    if retry_after_hdr and retry_after_hdr.isdigit():
                        sleep_time = float(retry_after_hdr)
                    else:
                        sleep_time = (
                            (backoff_base**attempt)
                            + (6.0 if not self.api_key else 2.0)
                            + random.uniform(0.1, 0.9)
                        )
                    logger.warning(
                        "[NVD] Rate limit encountered (429). Backing off for %.2fs (attempt %d/%d)",
                        sleep_time,
                        attempt,
                        self.max_retries,
                    )
                    if attempt > self.max_retries:
                        response.raise_for_status()
                    await asyncio.sleep(sleep_time)
                    continue

                # 5xx Server Errors
                if 500 <= response.status_code < 600:
                    attempt += 1
                    sleep_time = min(
                        (backoff_base**attempt) + random.uniform(0.2, 1.0),
                        settings.RETRY_BACKOFF_MAX,
                    )
                    logger.warning(
                        "[NVD] Server error %d. Retrying in %.2fs (attempt %d/%d)",
                        response.status_code,
                        sleep_time,
                        attempt,
                        self.max_retries,
                    )
                    if attempt > self.max_retries:
                        response.raise_for_status()
                    await asyncio.sleep(sleep_time)
                    continue

                # Return response for caller validation
                return response

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
                attempt += 1
                sleep_time = min(
                    (backoff_base**attempt) + random.uniform(0.2, 0.8),
                    settings.RETRY_BACKOFF_MAX,
                )
                logger.warning(
                    "[NVD] Network error: %s. Retrying in %.2fs (attempt %d/%d)",
                    str(exc),
                    sleep_time,
                    attempt,
                    self.max_retries,
                )
                if attempt > self.max_retries:
                    raise

        raise httpx.RequestError(f"NVD request failed after {self.max_retries} retries")

    async def fetch_cve(self, cve_id: str) -> RawNVDData:
        """Fetch vulnerability intelligence for a specific CVE from NVD 2.0 API.

        Args:
            cve_id: Validated CVE identifier (e.g. 'CVE-2024-1234')

        Returns:
            RawNVDData with CVSS v3.1/v4.0/v2.0 metrics and descriptions.
        """
        canonical_cve = validate_cve_id(cve_id, source="NVD")

        async with httpx.AsyncClient() as client:
            try:
                response = await self._execute_with_retry(
                    client,
                    self.base_url,
                    params={"cveId": canonical_cve},
                )

                if response.status_code == 404:
                    logger.info("[NVD] CVE %s not found in NVD database (404)", canonical_cve)
                    return RawNVDData(
                        cve_id=canonical_cve,
                        status=SourceStatusEnum.UNAVAILABLE,
                    )

                response.raise_for_status()
                payload = response.json()
                return self.parse_cve_item(canonical_cve, payload)

            except Exception as exc:
                logger.error(
                    "[NVD] Failed to retrieve CVE %s from NVD: %s",
                    canonical_cve,
                    str(exc),
                )
                return RawNVDData(
                    cve_id=canonical_cve,
                    status=SourceStatusEnum.UNAVAILABLE,
                )

    def parse_cve_item(self, cve_id: str, payload: Dict[str, Any]) -> RawNVDData:
        """Parse raw NVD 2.0 JSON payload into structured RawNVDData."""
        vulnerabilities = payload.get("vulnerabilities", [])
        if not vulnerabilities:
            return RawNVDData(
                cve_id=cve_id,
                status=SourceStatusEnum.UNAVAILABLE,
                raw_payload=payload,
            )

        cve_item = vulnerabilities[0].get("cve", {})

        # Extract English description
        description = None
        for desc in cve_item.get("descriptions", []):
            if desc.get("lang") == "en":
                description = desc.get("value")
                break
        if not description and cve_item.get("descriptions"):
            description = cve_item["descriptions"][0].get("value")

        # Extract CVSS metrics (Priority: v3.1 -> v3.0 -> v4.0 -> v2.0)
        cvss_score, cvss_version, cvss_vector, severity = self._extract_cvss(cve_item.get("metrics", {}))

        # Extract affected products from CPE configurations
        affected_products = []
        configurations = cve_item.get("configurations", [])
        for config in configurations:
            for node in config.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    criteria = match.get("criteria")
                    if criteria and criteria not in affected_products:
                        affected_products.append(criteria)

        # Extract references
        references = [
            ref.get("url")
            for ref in cve_item.get("references", [])
            if ref.get("url")
        ]

        return RawNVDData(
            cve_id=cve_id,
            description=description,
            published_date=cve_item.get("published"),
            last_modified_date=cve_item.get("lastModified"),
            cvss_score=validate_cvss_score(cvss_score, source="NVD", cve_id=cve_id),
            cvss_version=cvss_version,
            cvss_vector=cvss_vector,
            severity=severity,
            affected_products=affected_products[:50],  # Keep reasonable top 50
            references=references[:20],
            source_identifier=cve_item.get("sourceIdentifier"),
            status=SourceStatusEnum.AVAILABLE,
            raw_payload=cve_item,
        )

    def _extract_cvss(
        self, metrics: Dict[str, Any]
    ) -> Tuple[Optional[float], Optional[str], Optional[str], Optional[str]]:
        """Extract CVSS score, version, vector, and severity prioritizing v3.1 > v3.0 > v4.0 > v2.0."""
        # 1. Try CVSS v3.1
        if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
            metric = metrics["cvssMetricV31"][0].get("cvssData", {})
            return (
                metric.get("baseScore"),
                "3.1",
                metric.get("vectorString"),
                metric.get("baseSeverity") or metrics["cvssMetricV31"][0].get("baseSeverity"),
            )

        # 2. Try CVSS v3.0
        if "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
            metric = metrics["cvssMetricV30"][0].get("cvssData", {})
            return (
                metric.get("baseScore"),
                "3.0",
                metric.get("vectorString"),
                metric.get("baseSeverity") or metrics["cvssMetricV30"][0].get("baseSeverity"),
            )

        # 3. Try CVSS v4.0
        if "cvssMetricV40" in metrics and metrics["cvssMetricV40"]:
            metric = metrics["cvssMetricV40"][0].get("cvssData", {})
            return (
                metric.get("baseScore"),
                "4.0",
                metric.get("vectorString"),
                metric.get("baseSeverity") or metrics["cvssMetricV40"][0].get("baseSeverity"),
            )

        # 4. Fallback to CVSS v2.0
        if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
            metric = metrics["cvssMetricV2"][0].get("cvssData", {})
            return (
                metric.get("baseScore"),
                "2.0",
                metric.get("vectorString"),
                metrics["cvssMetricV2"][0].get("baseSeverity"),
            )

        return None, None, None, None

    async def check_health(self) -> str:
        """Actively probe NVD API reachability."""
        async with httpx.AsyncClient() as client:
            try:
                # Lightweight probe using a known standard CVE
                response = await client.get(
                    self.base_url,
                    params={"cveId": "CVE-2021-44228"},  # Log4Shell standard reference
                    headers=self._get_headers(),
                    timeout=5.0,
                )
                if response.status_code in (200, 404):
                    return SourceStatusEnum.AVAILABLE.value
                elif response.status_code == 429:
                    return SourceStatusEnum.DEGRADED.value
                return SourceStatusEnum.UNAVAILABLE.value
            except Exception as exc:
                logger.warning("[NVD] Health check probe failed: %s", str(exc))
                return SourceStatusEnum.UNAVAILABLE.value
