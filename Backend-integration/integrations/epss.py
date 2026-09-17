"""FIRST EPSS API Client Adapter

Official API Specification: https://www.first.org/epss/api
Base Endpoint: https://api.first.org/data/v1/epss

Handles FIRST EPSS public API queries, batch CVE lookups, rate-limiting,
safe numeric conversions, and bounds validation.
"""

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional

import httpx
from config import settings
from schemas.vulnerability import RawEPSSData, SourceStatusEnum
from validation.vulnerability_validator import validate_cve_id, validate_epss_score

logger = logging.getLogger("trinetra.integrations.epss")


class EPSSClient:
    """Async client for FIRST Exploit Prediction Scoring System (EPSS) API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.EPSS_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.MAX_RETRIES

    async def _execute_with_retry(
        self, client: httpx.AsyncClient, params: Dict[str, Any]
    ) -> httpx.Response:
        """Execute HTTP request with backoff, jitter, and 429 handling."""
        attempt = 0
        backoff_base = settings.RETRY_BACKOFF_BASE

        while attempt <= self.max_retries:
            try:
                logger.debug(
                    "[EPSS] Requesting %s (params: %s, attempt: %d)",
                    self.base_url,
                    params,
                    attempt + 1,
                )
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "TRINETRA-CyberRisk-Platform/1.0",
                    },
                    timeout=self.timeout,
                )

                # 429 Rate Limit
                if response.status_code == 429:
                    attempt += 1
                    sleep_time = (backoff_base**attempt) + random.uniform(1.0, 3.0)
                    logger.warning(
                        "[EPSS] Rate limit encountered (429). Sleeping %.2fs (attempt %d/%d)",
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
                        (backoff_base**attempt) + random.uniform(0.5, 1.5),
                        settings.RETRY_BACKOFF_MAX,
                    )
                    logger.warning(
                        "[EPSS] Server error %d. Retrying in %.2fs (attempt %d/%d)",
                        response.status_code,
                        sleep_time,
                        attempt,
                        self.max_retries,
                    )
                    if attempt > self.max_retries:
                        response.raise_for_status()
                    await asyncio.sleep(sleep_time)
                    continue

                return response

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
                attempt += 1
                sleep_time = min(
                    (backoff_base**attempt) + random.uniform(0.2, 0.8),
                    settings.RETRY_BACKOFF_MAX,
                )
                logger.warning(
                    "[EPSS] Network error: %s. Retrying in %.2fs (attempt %d/%d)",
                    str(exc),
                    sleep_time,
                    attempt,
                    self.max_retries,
                )
                if attempt > self.max_retries:
                    raise

        raise httpx.RequestError(f"EPSS request failed after {self.max_retries} retries")

    async def fetch_cve(self, cve_id: str) -> RawEPSSData:
        """Fetch EPSS score and percentile for a single CVE.

        Args:
            cve_id: Validated CVE identifier (e.g. 'CVE-2024-1234')

        Returns:
            RawEPSSData with validated probability [0.0 - 1.0].
        """
        canonical_cve = validate_cve_id(cve_id, source="EPSS")

        async with httpx.AsyncClient() as client:
            try:
                response = await self._execute_with_retry(
                    client, params={"cve": canonical_cve}
                )

                if response.status_code == 404:
                    return RawEPSSData(
                        cve_id=canonical_cve,
                        status=SourceStatusEnum.UNAVAILABLE,
                    )

                response.raise_for_status()
                payload = response.json()
                return self.parse_epss_item(canonical_cve, payload)

            except Exception as exc:
                logger.error(
                    "[EPSS] Failed to retrieve EPSS score for %s: %s",
                    canonical_cve,
                    str(exc),
                )
                return RawEPSSData(
                    cve_id=canonical_cve,
                    status=SourceStatusEnum.UNAVAILABLE,
                )

    async def fetch_batch(self, cve_ids: List[str]) -> Dict[str, RawEPSSData]:
        """Batch query EPSS scores for multiple CVEs in a single HTTP request."""
        if not cve_ids:
            return {}

        results: Dict[str, RawEPSSData] = {}
        # FIRST EPSS supports comma-separated list of up to ~100 CVEs
        chunk_size = 50
        for i in range(0, len(cve_ids), chunk_size):
            chunk = cve_ids[i : i + chunk_size]
            cve_param = ",".join(chunk)

            async with httpx.AsyncClient() as client:
                try:
                    response = await self._execute_with_retry(
                        client, params={"cve": cve_param}
                    )
                    response.raise_for_status()
                    payload = response.json()

                    data_list = payload.get("data", [])
                    for item in data_list:
                        cve = item.get("cve", "").upper()
                        raw_epss, raw_pct = validate_epss_score(
                            item.get("epss"),
                            item.get("percentile"),
                            source="EPSS",
                            cve_id=cve,
                        )
                        results[cve] = RawEPSSData(
                            cve_id=cve,
                            epss=raw_epss,
                            percentile=raw_pct,
                            date=item.get("date"),
                            status=SourceStatusEnum.AVAILABLE,
                            raw_payload=item,
                        )

                except Exception as exc:
                    logger.error("[EPSS] Batch fetch failed for chunk: %s", str(exc))

            # Mark any missing items as unavailable
            for cve in chunk:
                if cve not in results:
                    results[cve] = RawEPSSData(
                        cve_id=cve,
                        status=SourceStatusEnum.UNAVAILABLE,
                    )

        return results

    def parse_epss_item(self, cve_id: str, payload: Dict[str, Any]) -> RawEPSSData:
        """Parse raw EPSS JSON response into structured RawEPSSData."""
        data = payload.get("data", [])
        if not data:
            return RawEPSSData(
                cve_id=cve_id,
                status=SourceStatusEnum.UNAVAILABLE,
                raw_payload=payload,
            )

        item = data[0]
        raw_score = item.get("epss")
        raw_pct = item.get("percentile")

        epss, percentile = validate_epss_score(
            raw_score, raw_pct, source="EPSS", cve_id=cve_id
        )

        return RawEPSSData(
            cve_id=cve_id,
            epss=epss,
            percentile=percentile,
            date=item.get("date"),
            status=SourceStatusEnum.AVAILABLE,
            raw_payload=item,
        )

    async def check_health(self) -> str:
        """Actively probe FIRST EPSS API reachability."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    params={"cve": "CVE-2021-44228"},
                    headers={"Accept": "application/json"},
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return SourceStatusEnum.AVAILABLE.value
                elif response.status_code == 429:
                    return SourceStatusEnum.DEGRADED.value
                return SourceStatusEnum.UNAVAILABLE.value
            except Exception as exc:
                logger.warning("[EPSS] Health check probe failed: %s", str(exc))
                return SourceStatusEnum.UNAVAILABLE.value
