"""Background Synchronization Scheduler (Mode B)

TRINETRA - SIH 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105
"""

import asyncio
import logging
from typing import Optional
from config import settings
from .service import IngestionService

logger = logging.getLogger("trinetra.ingestion.scheduler")


class IngestionScheduler:
    """Asynchronous background worker for periodic threat intelligence synchronization."""

    def __init__(
        self,
        service: IngestionService,
        interval_hours: Optional[float] = None,
        enabled: Optional[bool] = None,
    ):
        self.service = service
        self.interval_seconds = (
            (interval_hours or settings.SYNC_INTERVAL_HOURS) * 3600.0
        )
        self.enabled = enabled if enabled is not None else settings.ENABLE_SCHEDULER
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def start(self):
        """Start the background synchronization loop."""
        if not self.enabled:
            logger.info("[Scheduler] Bulk synchronization scheduler is disabled in config.")
            return

        if self._running:
            logger.warning("[Scheduler] Scheduler is already running.")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "[Scheduler] Background sync scheduler started (interval: %.1f hours)",
            self.interval_seconds / 3600.0,
        )

    async def _run_loop(self):
        """Periodic sync execution loop."""
        # Initial delayed warmup after startup
        await asyncio.sleep(5.0)

        while self._running:
            try:
                logger.info("[Scheduler] Triggering scheduled bulk intelligence sync...")
                await self.service.bulk_sync()
            except asyncio.CancelledError:
                logger.info("[Scheduler] Scheduler task cancelled.")
                break
            except Exception as exc:
                logger.error("[Scheduler] Error in background sync loop: %s", str(exc))

            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    def stop(self):
        """Stop the background synchronization worker gracefully."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("[Scheduler] Background sync scheduler stopped.")
