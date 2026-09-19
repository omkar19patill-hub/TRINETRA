"""Core Ingestion Service orchestrating official threat sources, caching, and events.

TRINETRA - SIH 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105

Coordinates NVD, EPSS, CISA KEV feeds, validates inputs, normalizes records,
upserts to the local store, and dispatches recalculation triggers to the Risk Engine.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from cache.vulnerability_cache import VulnerabilityStorage
from config import settings
from integrations.cisa_kev import CISAKEVClient
from integrations.epss import EPSSClient
from integrations.mitre_attack import MitreAttackEnricher
from integrations.nvd import NVDClient
from normalization.vulnerability_normalizer import (
    normalize_vulnerability_record,
    to_enriched_response,
    to_risk_engine_payload,
)
from schemas.vulnerability import (
    EnrichedVulnerabilityResponse,
    IngestionHealthResponse,
    IngestionStatusResponse,
    RawEPSSData,
    RawKEVData,
    RawNVDData,
    RiskEngineAssetJoinRequest,
    RiskEnginePayloadResponse,
    SourceStatusEnum,
    UnifiedVulnerabilityRecord,
)
from validation.vulnerability_validator import validate_cve_id
from .status import telemetry

logger = logging.getLogger("trinetra.ingestion.service")

# Type alias for re-calculation hook callbacks
RecalculationHook = Callable[[UnifiedVulnerabilityRecord, Optional[UnifiedVulnerabilityRecord]], Any]


class IngestionService:
    """Central orchestrator for cybersecurity threat intelligence integration."""

    def __init__(
        self,
        nvd_client: Optional[NVDClient] = None,
        epss_client: Optional[EPSSClient] = None,
        kev_client: Optional[CISAKEVClient] = None,
        mitre_enricher: Optional[MitreAttackEnricher] = None,
        storage: Optional[VulnerabilityStorage] = None,
    ):
        self.nvd = nvd_client or NVDClient()
        self.epss = epss_client or EPSSClient()
        self.kev = kev_client or CISAKEVClient()
        self.mitre = mitre_enricher or MitreAttackEnricher()
        self.storage = storage or VulnerabilityStorage()
        self._recalculation_hooks: List[RecalculationHook] = []

    def register_recalculation_hook(self, callback: RecalculationHook):
        """Register a callback function to be invoked when vulnerability intelligence changes."""
        self._recalculation_hooks.append(callback)
        logger.info("[Service] Registered recalculation hook callback: %s", callback.__name__)

    async def _notify_recalculation(
        self,
        new_record: UnifiedVulnerabilityRecord,
        old_record: Optional[UnifiedVulnerabilityRecord],
    ):
        """Dispatch event to registered recalculation hooks."""
        for hook in self._recalculation_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(new_record, old_record)
                else:
                    hook(new_record, old_record)
            except Exception as exc:
                logger.error("[Service] Recalculation hook execution error: %s", str(exc))

    async def get_or_enrich_cve(
        self, cve_id: str, force_refresh: bool = False
    ) -> UnifiedVulnerabilityRecord:
        """Retrieve unified vulnerability record from cache or perform live enrichment.

        Mode A: Single CVE Enrichment.
        """
        canonical_cve = validate_cve_id(cve_id, source="service")

        # 1. Check existing cached data if not forcing refresh
        existing_record = self.storage.get_vulnerability(canonical_cve)
        if existing_record and not force_refresh:
            logger.debug("[Service] Serving cached record for %s", canonical_cve)
            return existing_record

        logger.info(
            "[Service] Performing live intelligence enrichment for %s (force_refresh=%s)",
            canonical_cve,
            force_refresh,
        )

        try:
            # 2. Concurrently fetch NVD and EPSS data
            nvd_task = self.nvd.fetch_cve(canonical_cve)
            epss_task = self.epss.fetch_cve(canonical_cve)

            nvd_result, epss_result = await asyncio.gather(
                nvd_task, epss_task, return_exceptions=True
            )

            # Handle potential task exceptions gracefully
            if isinstance(nvd_result, Exception):
                logger.error("[Service] NVD task raised exception: %s", str(nvd_result))
                # Fallback to existing NVD if available
                if existing_record and existing_record.nvd.cvss is not None:
                    nvd_data = RawNVDData(
                        cve_id=canonical_cve,
                        cvss_score=existing_record.nvd.cvss,
                        cvss_version=existing_record.nvd.cvss_version,
                        cvss_vector=existing_record.nvd.cvss_vector,
                        severity=existing_record.nvd.severity,
                        description=existing_record.nvd.description,
                        published_date=existing_record.nvd.published,
                        last_modified_date=existing_record.nvd.last_modified,
                        status=SourceStatusEnum.STALE,
                    )
                else:
                    nvd_data = RawNVDData(
                        cve_id=canonical_cve, status=SourceStatusEnum.UNAVAILABLE
                    )
            else:
                nvd_data = nvd_result
                if nvd_data.status == SourceStatusEnum.AVAILABLE:
                    telemetry.update_sync_time("nvd")

            if isinstance(epss_result, Exception):
                logger.error("[Service] EPSS task raised exception: %s", str(epss_result))
                if existing_record and existing_record.epss.score is not None:
                    epss_data = RawEPSSData(
                        cve_id=canonical_cve,
                        epss=existing_record.epss.score,
                        percentile=existing_record.epss.percentile,
                        date=existing_record.epss.date,
                        status=SourceStatusEnum.STALE,
                    )
                else:
                    epss_data = RawEPSSData(
                        cve_id=canonical_cve, status=SourceStatusEnum.UNAVAILABLE
                    )
            else:
                epss_data = epss_result
                if epss_data.status == SourceStatusEnum.AVAILABLE:
                    telemetry.update_sync_time("epss")

            # 3. Lookup CISA KEV from in-memory catalog
            kev_data = self.kev.lookup_cve(canonical_cve)

            # 4. Optional MITRE ATT&CK context
            mitre_data = self.mitre.enrich(
                cve_id=canonical_cve,
                description=nvd_data.description,
                is_kev=kev_data.is_known_exploited,
                known_ransomware=kev_data.known_ransomware_use,
            )

            # 5. Normalize into Unified Record
            unified_record = normalize_vulnerability_record(
                cve_id=canonical_cve,
                nvd_data=nvd_data,
                epss_data=epss_data,
                kev_data=kev_data,
                mitre_data=mitre_data,
            )

            # 6. Check if data changed significantly to trigger recalculation
            data_changed = False
            if existing_record is None:
                data_changed = True
            else:
                if (
                    existing_record.nvd.cvss != unified_record.nvd.cvss
                    or existing_record.epss.score != unified_record.epss.score
                    or existing_record.kev.is_known_exploited
                    != unified_record.kev.is_known_exploited
                ):
                    data_changed = True

            # 7. Upsert to multi-tier storage
            self.storage.upsert_vulnerability(unified_record)
            telemetry.record_success(is_update=bool(existing_record))

            # 8. Dispatch recalculation event if changed
            if data_changed:
                logger.info(
                    "[Service] Threat intelligence changed for %s -> firing recalculation hooks",
                    canonical_cve,
                )
                await self._notify_recalculation(unified_record, existing_record)

            return unified_record

        except Exception as exc:
            telemetry.record_failure()
            logger.error(
                "[Service] Enrichment failed for %s: %s", canonical_cve, str(exc)
            )
            # If we had existing record, return it with degraded indicator
            if existing_record:
                return existing_record
            raise

    async def get_enriched_response(
        self, cve_id: str
    ) -> EnrichedVulnerabilityResponse:
        """Internal endpoint method returning standard enriched vulnerability response."""
        record = await self.get_or_enrich_cve(cve_id, force_refresh=False)
        return to_enriched_response(record)

    async def join_asset_and_build_payload(
        self, request: RiskEngineAssetJoinRequest
    ) -> RiskEnginePayloadResponse:
        """Combine asset context with vulnerability intelligence to construct Risk Engine payload."""
        canonical_cve = validate_cve_id(request.cve_id, source="asset_join")
        record = await self.get_or_enrich_cve(canonical_cve, force_refresh=False)
        return to_risk_engine_payload(request, record)

    async def bulk_sync(
        self, cve_watchlist: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Perform Mode B bulk synchronization across official feeds."""
        logger.info("[Service] Starting bulk synchronization cycle...")
        start_ts = datetime.now(timezone.utc)

        # 1. Refresh CISA KEV catalog feed
        kev_count = await self.kev.refresh_catalog()
        telemetry.update_sync_time("cisa_kev")

        # 2. Enrich watchlist or recent high-priority CVEs
        watchlist = cve_watchlist or [
            "CVE-2024-3400",  # Palo Alto PAN-OS Command Injection (KEV, High EPSS)
            "CVE-2023-34362",  # MOVEit Transfer SQLi (KEV, High EPSS)
            "CVE-2021-44228",  # Log4Shell RCE (KEV, High EPSS)
            "CVE-2023-23397",  # Microsoft Outlook Privilege Escalation
            "CVE-2024-21413",  # Microsoft Outlook RCE (MonikerLink)
            "CVE-2024-1709",   # ConnectWise ScreenConnect Auth Bypass
            "CVE-2023-4966",   # Citrix Bleed Information Disclosure
            "CVE-2023-2868",   # Barracuda Email Security Gateway RCE
        ]

        synced_count = 0
        for cve in watchlist:
            try:
                await self.get_or_enrich_cve(cve, force_refresh=True)
                synced_count += 1
            except Exception as exc:
                logger.warning("[Service] Watchlist sync failed for %s: %s", cve, str(exc))

        telemetry.update_sync_time("bulk_sync")
        logger.info(
            "[Service] Bulk sync completed. KEV catalog: %d CVEs, Watchlist processed: %d",
            kev_count,
            synced_count,
        )

        return {
            "cisa_kev_catalog_size": kev_count,
            "watchlist_synced": synced_count,
            "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    async def check_health(self) -> IngestionHealthResponse:
        """Actively probe reachability of all external feeds and local database."""
        nvd_health_task = self.nvd.check_health()
        epss_health_task = self.epss.check_health()
        kev_health_task = self.kev.check_health()

        nvd_status, epss_status, kev_status = await asyncio.gather(
            nvd_health_task, epss_health_task, kev_health_task, return_exceptions=True
        )

        db_status = self.storage.check_health()

        sources = {
            "nvd": nvd_status if isinstance(nvd_status, str) else "unavailable",
            "epss": epss_status if isinstance(epss_status, str) else "unavailable",
            "cisa_kev": (
                kev_status if isinstance(kev_status, str) else "unavailable"
            ),
            "database": db_status,
        }

        # Overall status is ok if database and at least 2 external sources are available
        available_count = sum(1 for v in sources.values() if v == "available")
        if sources["database"] == "available" and available_count >= 3:
            overall = "ok"
        elif sources["database"] == "available":
            overall = "degraded"
        else:
            overall = "unavailable"

        return IngestionHealthResponse(
            status=overall,
            sources=sources,
            checked_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def get_status(self) -> IngestionStatusResponse:
        """Return operational telemetry, sync times, and storage metrics."""
        metrics = telemetry.get_metrics()
        cache_stats = self.storage.get_stats()

        return IngestionStatusResponse(
            status="ok",
            last_sync=metrics["last_sync"],
            records=metrics["records"],
            cache_stats=cache_stats,
            uptime_seconds=metrics["uptime_seconds"],
        )
