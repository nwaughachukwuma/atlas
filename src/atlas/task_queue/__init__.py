"""
SQLite-backed task queue with subprocess workers.

Design
~~~~~~
* SQLite (WAL mode) for task persistence — survives process restarts.
* Each task runs in its own detached Python subprocess via
  ``python -m atlas.task_queue.worker <task_id>``. The parent CLI
  returns immediately.
* Workers handle their own timeout enforcement (watchdog thread).
* Completed tasks (last 25) and failed tasks (last 50) are retained for
  inspection; everything else is trimmed automatically.
* Results written to ``~/.atlas/queue/queued_tasks/results/{task_id}/output.txt``.
* Cross-platform system notifications on completion/failure/timeout.
* No Redis, no external broker, no long-lived daemons.
"""

from .commands import _cmd_queue_list, _cmd_queue_status, add_queue_commands
from .config import (
    DB_PATH,
    DEFAULT_WORKERS,
    HEARTBEAT_INTERVAL,
    HEAVY_COMMANDS,
    HEAVY_CONCURRENCY,
    MAX_COMPLETED_TASKS,
    MAX_CONCURRENT,
    MAX_FAILED_TASKS,
    MAX_WORKERS,
    QUEUE_DIR,
    RESULTS_DIR,
    TASK_TIMEOUT,
    TRANSCRIBE_CONCURRENCY,
    TaskStatus,
)
from .helpers import _serialize_result, _write_file, results_dir_for
from .queue import TaskQueue, get_queue
from .store import TaskStore

__all__ = [
    # config
    "DB_PATH",
    "DEFAULT_WORKERS",
    "HEARTBEAT_INTERVAL",
    "HEAVY_COMMANDS",
    "HEAVY_CONCURRENCY",
    "MAX_COMPLETED_TASKS",
    "MAX_CONCURRENT",
    "MAX_FAILED_TASKS",
    "MAX_WORKERS",
    "QUEUE_DIR",
    "RESULTS_DIR",
    "TASK_TIMEOUT",
    "TRANSCRIBE_CONCURRENCY",
    "TaskStatus",
    # store
    "TaskStore",
    # queue
    "TaskQueue",
    "get_queue",
    # helpers
    "_serialize_result",
    "_write_file",
    "results_dir_for",
    # commands
    "add_queue_commands",
    "_cmd_queue_list",
    "_cmd_queue_status",
]
