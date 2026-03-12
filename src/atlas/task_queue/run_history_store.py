"""SQLite-backed run history for queued and direct media operations."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

from .config import DB_PATH, MAX_COMPLETED_TASKS, MAX_FAILED_TASKS, TASK_TIMEOUT, TaskStatus, now_iso

_DDL = """\
CREATE TABLE IF NOT EXISTS run_history (
    id             TEXT PRIMARY KEY,
    command        TEXT NOT NULL,
    label          TEXT NOT NULL DEFAULT '',
    run_type       TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
    created_at     TEXT NOT NULL,
    started_at     TEXT,
    finished_at    TEXT,
    error          TEXT,
    output_path    TEXT,
    benchmark      INTEGER NOT NULL DEFAULT 0,
    result_text    TEXT,
    result_path    TEXT,
    benchmark_text TEXT,
    benchmark_path TEXT
);
"""


class RunHistoryStore:
    """Store persisted run history separately from the queued-task table."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._local = threading.local()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn()

    def _conn(self) -> sqlite3.Connection:
        """Return a thread-local connection with WAL enabled."""
        conn: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_DDL)
            self._local.conn = conn
        return conn

    @contextmanager
    def _tx(self):
        """Yield a connection inside a transaction."""
        conn = self._conn()
        try:
            yield conn
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise exc

    def add(
        self,
        run_id: str,
        command: str,
        label: str,
        *,
        run_type: str,
        output_path: Optional[str] = None,
        benchmark: bool = False,
    ) -> None:
        """Insert a new run-history row."""
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO run_history (id, command, label, run_type, status, created_at, output_path, benchmark)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, command, label, run_type, TaskStatus.PENDING, now_iso(), output_path, int(benchmark)),
            )

    def mark_running(self, run_id: str) -> None:
        """Transition run to running."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE run_history SET status=?, started_at=? WHERE id=?",
                (TaskStatus.RUNNING, now_iso(), run_id),
            )

    def mark_completed(
        self,
        run_id: str,
        *,
        result_text: str | None = None,
        result_path: str | None = None,
        benchmark_text: str | None = None,
        benchmark_path: str | None = None,
    ) -> None:
        """Transition run to completed and retain artifact metadata."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE run_history SET status=?, finished_at=?, result_text=?, result_path=?, benchmark_text=?,"
                " benchmark_path=? WHERE id=?",
                (TaskStatus.COMPLETED, now_iso(), result_text, result_path, benchmark_text, benchmark_path, run_id),
            )
            self._trim(conn)

    def mark_failed(
        self,
        run_id: str,
        error: str,
        *,
        result_text: str | None = None,
        result_path: str | None = None,
        benchmark_text: str | None = None,
        benchmark_path: str | None = None,
    ) -> None:
        """Transition run to failed."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE run_history SET status=?, finished_at=?, error=?, result_text=?, result_path=?, benchmark_text=?,"
                " benchmark_path=? WHERE id=?",
                (
                    TaskStatus.FAILED,
                    now_iso(),
                    error,
                    result_text,
                    result_path,
                    benchmark_text,
                    benchmark_path,
                    run_id,
                ),
            )
            self._trim(conn)

    def mark_timeout(
        self,
        run_id: str,
        *,
        result_text: str | None = None,
        result_path: str | None = None,
    ) -> None:
        """Transition run to timeout."""
        with self._tx() as conn:
            conn.execute(
                "UPDATE run_history SET status=?, finished_at=?, error=?, result_text=?, result_path=? WHERE id=?",
                (
                    TaskStatus.TIMEOUT,
                    now_iso(),
                    f"Exceeded {TASK_TIMEOUT}s timeout",
                    result_text,
                    result_path,
                    run_id,
                ),
            )

    def get(self, run_id: str) -> Optional[dict]:
        """Return a single run-history record or ``None``."""
        row = self._conn().execute("SELECT * FROM run_history WHERE id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def list_all(
        self,
        status: Optional[str] = None,
        *,
        command: Optional[str] = None,
        run_type: Optional[str] = None,
    ) -> List[dict]:
        """Return all runs, optionally filtered by status, command, and run type."""
        query = "SELECT * FROM run_history"
        clauses: list[str] = []
        values: list[str] = []
        if status:
            clauses.append("status=?")
            values.append(status)
        if command:
            clauses.append("command=?")
            values.append(command)
        if run_type:
            clauses.append("run_type=?")
            values.append(run_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        rows = self._conn().execute(query, values).fetchall()
        return [dict(r) for r in rows]

    def _trim(self, conn: sqlite3.Connection) -> None:
        """Keep only the newest completed/failed runs."""
        conn.execute(
            "DELETE FROM run_history WHERE id IN ("
            "  SELECT id FROM run_history WHERE status='completed'"
            "  ORDER BY finished_at DESC LIMIT -1 OFFSET ?"
            ")",
            (MAX_COMPLETED_TASKS,),
        )
        conn.execute(
            "DELETE FROM run_history WHERE id IN ("
            "  SELECT id FROM run_history WHERE status='failed'"
            "  ORDER BY finished_at DESC LIMIT -1 OFFSET ?"
            ")",
            (MAX_FAILED_TASKS,),
        )
