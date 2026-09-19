"""CISA Known Exploited Vulnerabilities (KEV) Catalog Client Adapter

Official JSON Feed: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json

Loads and indexes the CISA KEV catalog for O(1) in-memory lookup. Handles
ransomware flags, date added, required actions, and graceful fallback.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from config import settings
from schemas.vulnerability import RawKEVData, SourceStatusEnum
from validation.vulnerability_validator import validate_cve_id

logger = logging.getLogger("trinetra.integrations.cisa_kev")


class CISAKEVClient:
    """Client for CISA Known Exploited Vulnerabilities catalog feed."""

    def __init__(
        self,
        feed_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.feed_url = feed_url or settings.CISA_KEV_FEED_URL
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
        self._catalog: Dict[str, RawKEVData] = {}
        self._last_refreshed: Optional[str] = None
        self._lock = asyncio.Lock()

    @property
    def catalog_size(self) -> int:
        """Total number of vulnerabilities in the current KEV catalog."""
        return len(self._catalog)

    @property
    def last_refreshed(self) -> Optional[str]:
        """Timestamp of last successful catalog refresh."""
        return self._last_refreshed

    async def refresh_catalog(self) -> int:
        """Download and index the full CISA KEV JSON catalog feed.

        Returns:
            Number of indexed KEV entries.
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info("[CISA KEV] Refreshing KEV catalog feed from %s", self.feed_url)
                response = await client.get(
                    self.feed_url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "TRINETRA-CyberRisk-Platform/1.0",
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                payload = response.json()
                vulnerabilities = payload.get("vulnerabilities", [])

                new_catalog: Dict[str, RawKEVData] = {}
                for item in vulnerabilities:
                    cve_raw = item.get("cveID", "")
                    if not cve_raw:
                        continue
                    try:
                        canonical_cve = validate_cve_id(cve_raw, source="CISA_KEV")
                    except Exception:
                        continue

                    # Known ransomware campaign use
                    ransomware_raw = item.get("knownRansomwareCampaignUse", "")
                    is_ransomware = (
                        ransomware_raw.strip().lower() == "known"
                        if isinstance(ransomware_raw, str)
                        else bool(ransomware_raw)
                    )

                    new_catalog[canonical_cve] = RawKEVData(
                        cve_id=canonical_cve,
                        is_known_exploited=True,
                        vendor_project=item.get("vendorProject"),
                        product=item.get("product"),
                        vulnerability_name=item.get("vulnerabilityName"),
                        date_added=item.get("dateAdded"),
                        short_description=item.get("shortDescription"),
                        required_action=item.get("requiredAction"),
                        due_date=item.get("dueDate"),
                        known_ransomware_use=is_ransomware,
                        notes=item.get("notes"),
                        status=SourceStatusEnum.AVAILABLE,
                        raw_payload=item,
                    )

                async with self._lock:
                    self._catalog = new_catalog
                    self._last_refreshed = (
                        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    )

                logger.info(
                    "[CISA KEV] Catalog successfully updated with %d active exploited CVEs",
                    len(new_catalog),
                )
                return len(new_catalog)

            except Exception as exc:
                logger.error(
                    "[CISA KEV] Failed to download KEV catalog feed: %s. Preserving existing catalog.",
                    str(exc),
                )
                if not self._catalog:
                    logger.warning("[CISA KEV] Catalog is currently empty!")
                return len(self._catalog)

    def load_from_dict_list(self, items: List[Dict[str, Any]]) -> int:
        """Populate catalog directly from a list of items (useful for testing or local cache seeding)."""
        new_catalog: Dict[str, RawKEVData] = {}
        for item in items:
            cve_raw = item.get("cveID") or item.get("cve_id", "")
            if not cve_raw:
                continue
            canonical_cve = cve_raw.strip().upper()
            ransomware_raw = item.get("knownRansomwareCampaignUse", "")
            is_ransomware = (
                ransomware_raw.strip().lower() == "known"
                if isinstance(ransomware_raw, str)
                else bool(ransomware_raw)
            )

            new_catalog[canonical_cve] = RawKEVData(
                cve_id=canonical_cve,
                is_known_exploited=True,
                vendor_project=item.get("vendorProject") or item.get("vendor_project"),
                product=item.get("product"),
                vulnerability_name=item.get("vulnerabilityName") or item.get("vulnerability_name"),
                date_added=item.get("dateAdded") or item.get("date_added"),
                short_description=item.get("shortDescription") or item.get("short_description"),
                required_action=item.get("requiredAction") or item.get("required_action"),
                due_date=item.get("dueDate") or item.get("due_date"),
                known_ransomware_use=is_ransomware,
                notes=item.get("notes"),
                status=SourceStatusEnum.AVAILABLE,
                raw_payload=item,
            )

        self._catalog = new_catalog
        self._last_refreshed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return len(new_catalog)

    def lookup_cve(self, cve_id: str) -> RawKEVData:
        """Perform fast O(1) in-memory lookup for a CVE in the KEV catalog.

        Args:
            cve_id: Target CVE identifier

        Returns:
            RawKEVData with is_known_exploited=True if present, or is_known_exploited=False if absent.
        """
        canonical_cve = validate_cve_id(cve_id, source="CISA_KEV")

        if canonical_cve in self._catalog:
            return self._catalog[canonical_cve]

        # Absence from KEV is a valid state (not known exploited), NOT an API failure
        return RawKEVData(
            cve_id=canonical_cve,
            is_known_exploited=False,
            status=SourceStatusEnum.AVAILABLE,
        )

    async def check_health(self) -> str:
        """Probe CISA KEV feed reachability or check loaded catalog status."""
        if self._catalog:
            return SourceStatusEnum.AVAILABLE.value

        # If empty, attempt a HEAD or lightweight GET request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.head(
                    self.feed_url,
                    headers={"User-Agent": "TRINETRA-CyberRisk-Platform/1.0"},
                    timeout=5.0,
                )
                if response.status_code in (200, 302):
                    return SourceStatusEnum.AVAILABLE.value
                return SourceStatusEnum.DEGRADED.value
            except Exception as exc:
                logger.warning("[CISA KEV] Health probe failed: %s", str(exc))
                return SourceStatusEnum.UNAVAILABLE.value
