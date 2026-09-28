"""Multi-tier SQLite Persistence for Assessment Batches, Results, and Risk Snapshots.

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
Phase 1: Persistent Assessment History & Risk Snapshots

Provides thread-safe, idempotent SQLite persistence for:
1. assessment_batches: Record of batch uploads, execution status, and row metrics
2. assessment_results: Individual per-asset quantified risk and financial exposure
3. risk_snapshots: Point-in-time aggregate portfolio risk metrics and risk appetite
"""

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import settings
from .schemas import (
    AssessmentBatchCreate,
    AssessmentBatchResponse,
    AssessmentResultItem,
    RiskSnapshotResponse,
)

logger = logging.getLogger("trinetra.risk.storage")

_STORAGE_INSTANCE: Optional["AssessmentStorage"] = None
_INIT_LOCK = threading.Lock()


class AssessmentStorage:
    """Thread-safe SQLite storage for assessment batches, asset results, and portfolio snapshots."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._lock = threading.RLock()
        self._ensure_schema_initialized()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and configure a SQLite connection with WAL journal mode."""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=15.0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        self._ensure_schema(conn)
        return conn

    def _ensure_schema(self, conn: sqlite3.Connection):
        """Create assessment tables and indexes idempotently without affecting existing tables."""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assessment_batches (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                source TEXT NOT NULL,
                total_rows INTEGER NOT NULL,
                successful_rows INTEGER NOT NULL,
                failed_rows INTEGER NOT NULL,
                status TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_created_at ON assessment_batches(created_at);"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assessment_results (
                id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                asset_identifier TEXT NOT NULL,
                asset_name TEXT,
                risk_score REAL NOT NULL,
                financial_exposure REAL NOT NULL,
                assessment_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES assessment_batches(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_result_batch_id ON assessment_results(batch_id);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_result_asset_id ON assessment_results(asset_identifier);"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_snapshots (
                id TEXT PRIMARY KEY,
                batch_id TEXT,
                timestamp TEXT NOT NULL,
                total_exposure REAL NOT NULL,
                average_risk REAL NOT NULL,
                critical_assets INTEGER NOT NULL,
                high_risk_assets INTEGER NOT NULL,
                risk_appetite REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES assessment_batches(id) ON DELETE SET NULL
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON risk_snapshots(timestamp);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshot_batch_id ON risk_snapshots(batch_id);"
        )

    def _ensure_schema_initialized(self):
        """Ensure parent directory exists and tables are initialized."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=15.0,
        )
        try:
            with conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA foreign_keys=ON;")
                self._ensure_schema(conn)
            logger.debug("[AssessmentStorage] Schema verified at %s", self.db_path)
        finally:
            conn.close()

    def save_batch(self, batch_data: AssessmentBatchCreate) -> AssessmentBatchResponse:
        """Atomically persist assessment batch, asset results, and computed risk snapshot.

        Args:
            batch_data: Validated AssessmentBatchCreate schema

        Returns:
            AssessmentBatchResponse containing batch metadata and calculated risk snapshot.
        """
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        batch_id = batch_data.batch_id or f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        snapshot_id = f"SNAP-{uuid.uuid4().hex[:8].upper()}"

        # Calculate snapshot aggregates
        results = batch_data.results
        total_exposure = round(sum(r.financial_exposure for r in results), 2)
        avg_risk = (
            round(sum(r.risk_score for r in results) / len(results), 2)
            if results
            else 0.0
        )
        critical_count = sum(1 for r in results if r.risk_score >= 75.0)
        high_count = sum(1 for r in results if 50.0 <= r.risk_score < 75.0)

        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    # 1. Insert assessment batch
                    conn.execute(
                        """
                        INSERT INTO assessment_batches (
                            id, created_at, source, total_rows, successful_rows, failed_rows, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            batch_id,
                            now_iso,
                            batch_data.source,
                            batch_data.total_rows,
                            batch_data.successful_rows,
                            batch_data.failed_rows,
                            batch_data.status,
                        ),
                    )

                    # 2. Insert individual assessment results
                    for item in results:
                        res_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
                        asset_name = item.asset_name or item.asset_id
                        serialized_data = json.dumps(item.assessment_data)

                        conn.execute(
                            """
                            INSERT INTO assessment_results (
                                id, batch_id, asset_identifier, asset_name, risk_score,
                                financial_exposure, assessment_data, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                            """,
                            (
                                res_id,
                                batch_id,
                                item.asset_id,
                                asset_name,
                                item.risk_score,
                                item.financial_exposure,
                                serialized_data,
                                now_iso,
                            ),
                        )

                    # 3. Insert risk snapshot
                    conn.execute(
                        """
                        INSERT INTO risk_snapshots (
                            id, batch_id, timestamp, total_exposure, average_risk,
                            critical_assets, high_risk_assets, risk_appetite, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            snapshot_id,
                            batch_id,
                            now_iso,
                            total_exposure,
                            avg_risk,
                            critical_count,
                            high_count,
                            batch_data.risk_appetite,
                            now_iso,
                        ),
                    )

                logger.info(
                    "[AssessmentStorage] Persisted batch %s with %d results and snapshot %s",
                    batch_id,
                    len(results),
                    snapshot_id,
                )

                snapshot_res = RiskSnapshotResponse(
                    id=snapshot_id,
                    batch_id=batch_id,
                    timestamp=now_iso,
                    total_exposure=total_exposure,
                    average_risk=avg_risk,
                    critical_assets=critical_count,
                    high_risk_assets=high_count,
                    risk_appetite=batch_data.risk_appetite,
                    created_at=now_iso,
                )

                return AssessmentBatchResponse(
                    batch_id=batch_id,
                    created_at=now_iso,
                    source=batch_data.source,
                    total_rows=batch_data.total_rows,
                    successful_rows=batch_data.successful_rows,
                    failed_rows=batch_data.failed_rows,
                    status=batch_data.status,
                    snapshot=snapshot_res,
                )
            finally:
                conn.close()

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve batch metadata by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM assessment_batches WHERE id = ?;", (batch_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_batches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List assessment batches in descending chronological order."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM assessment_batches ORDER BY created_at DESC LIMIT ?;",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def get_batch_results(self, batch_id: str) -> List[Dict[str, Any]]:
        """Retrieve all individual assessment results for a specific batch."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT id, batch_id, asset_identifier, asset_name, risk_score,
                       financial_exposure, assessment_data, created_at
                FROM assessment_results
                WHERE batch_id = ?
                ORDER BY financial_exposure DESC;
                """,
                (batch_id,),
            )
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                try:
                    item["assessment_data"] = json.loads(item["assessment_data"])
                except Exception:
                    pass
                results.append(item)
            return results
        finally:
            conn.close()

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent portfolio risk snapshot."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM risk_snapshots ORDER BY timestamp DESC, created_at DESC LIMIT 1;"
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_snapshots(self, limit: int = 50, order: str = "asc") -> List[Dict[str, Any]]:
        """List historical risk snapshots in chronological ('asc') or reverse ('desc') order."""
        conn = self._get_connection()
        try:
            direction = "DESC" if str(order).lower() == "desc" else "ASC"
            cursor = conn.execute(
                f"SELECT * FROM risk_snapshots ORDER BY timestamp {direction}, created_at {direction} LIMIT ?;",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()


    def get_snapshot_by_id(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific snapshot by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM risk_snapshots WHERE id = ?;", (snapshot_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


def get_assessment_storage() -> AssessmentStorage:
    """Dependency provider and singleton accessor for AssessmentStorage."""
    global _STORAGE_INSTANCE
    if _STORAGE_INSTANCE is None:
        with _INIT_LOCK:
            if _STORAGE_INSTANCE is None:
                _STORAGE_INSTANCE = AssessmentStorage()
    return _STORAGE_INSTANCE


def set_assessment_storage(storage: Optional[AssessmentStorage]) -> None:
    """Override singleton storage (useful for isolated testing)."""
    global _STORAGE_INSTANCE
    with _INIT_LOCK:
        _STORAGE_INSTANCE = storage


def init_assessment_storage() -> AssessmentStorage:
    """Explicitly initialize storage on application lifespan startup."""
    return get_assessment_storage()
