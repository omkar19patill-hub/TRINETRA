"""Telemetry and observability tracker for vulnerability ingestion.

TRINETRA - SIH 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105
"""

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class TelemetryTracker:
    """Thread-safe metric counter and synchronization status tracker."""

    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._records_processed = 0
        self._records_updated = 0
        self._records_failed = 0
        self._last_sync: Dict[str, Optional[str]] = {
            "nvd": None,
            "epss": None,
            "cisa_kev": None,
            "bulk_sync": None,
        }

    def record_success(self, is_update: bool = False):
        """Increment processed and optionally updated counters."""
        with self._lock:
            self._records_processed += 1
            if is_update:
                self._records_updated += 1

    def record_failure(self):
        """Increment failed processing counter."""
        with self._lock:
            self._records_failed += 1

    def update_sync_time(self, source: str):
        """Update last successful sync timestamp for a given feed."""
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._lock:
            self._last_sync[source] = now_iso

    def get_metrics(self) -> Dict[str, Any]:
        """Return snapshot of telemetry metrics and uptime."""
        with self._lock:
            return {
                "records": {
                    "processed": self._records_processed,
                    "updated": self._records_updated,
                    "failed": self._records_failed,
                },
                "last_sync": dict(self._last_sync),
                "uptime_seconds": round(time.time() - self._start_time, 2),
            }


telemetry = TelemetryTracker()
