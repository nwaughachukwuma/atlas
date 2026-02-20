"""Task queue configuration — constants, paths, and status enum."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

# ── Worker & timeout knobs ────────────────────────────────────────────────────

DEFAULT_WORKERS = 4
MAX_WORKERS = 16
TASK_TIMEOUT = 600  # seconds (10 minutes)
HEARTBEAT_INTERVAL = 10  # seconds between heartbeat checks

# ── File-system paths ─────────────────────────────────────────────────────────

QUEUE_DIR = Path.home() / ".atlas" / "queue"
DB_PATH = QUEUE_DIR / "tasks.db"
RESULTS_DIR = QUEUE_DIR / "queued_tasks" / "results"

# ── Retention limits ──────────────────────────────────────────────────────────

MAX_FAILED_TASKS = 50
MAX_COMPLETED_TASKS = 25


# ── Task status ───────────────────────────────────────────────────────────────


class TaskStatus(str, Enum):
    """Possible lifecycle states for a queued task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ── Helpers ───────────────────────────────────────────────────────────────────


def now_iso() -> str:
    """Return the current local time as a compact ISO-8601 string."""
    return datetime.now().isoformat(timespec="seconds")
