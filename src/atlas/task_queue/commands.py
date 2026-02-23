"""CLI sub-commands for ``atlas queue list`` and ``atlas queue status``."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import RESULTS_DIR
from .store import TaskStore

_STATUS_COLORS = {
    "pending": "yellow",
    "running": "cyan",
    "completed": "green",
    "failed": "red",
    "timeout": "magenta",
}


# ── Parser registration ──────────────────────────────────────────────────────


def add_queue_commands(subparsers: Any) -> None:
    """Register ``atlas queue list`` and ``atlas queue status`` sub-commands."""
    p_queue = subparsers.add_parser(
        "queue",
        help="Manage the task queue.",
        description="View and manage background tasks (transcribe / extract / index).",
        epilog=(
            "Examples:\n"
            "  atlas queue list\n"
            "  atlas queue list --status pending\n"
            "  atlas queue status --task-id abc12345\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p_queue.add_subparsers(dest="queue_command", metavar="<action>")
    sub.required = True

    # atlas queue list
    p_list = sub.add_parser("list", help="List tasks in the queue.")
    p_list.add_argument(
        "--status",
        "-s",
        choices=["pending", "running", "completed", "failed", "timeout"],
        help="Filter by status.",
    )
    p_list.set_defaults(func=cmd_queue_list)

    # atlas queue status
    p_status = sub.add_parser("status", help="Show status of a specific task.")
    p_status.add_argument("--task-id", "-t", required=True, help="Task ID to check.")
    p_status.set_defaults(func=cmd_queue_status)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _duration_str(started: str | None, finished: str | None) -> str:
    """Return a human-readable elapsed duration, or empty string if unavailable."""
    if not started or not finished:
        return ""
    try:
        secs = int((datetime.fromisoformat(finished) - datetime.fromisoformat(started)).total_seconds())
        if secs < 60:
            return f"{secs}s"
        return f"{secs // 60}m {secs % 60}s"
    except Exception:
        return ""


def _parse_benchmark_file(path: Path) -> list[tuple[str, ...]]:
    """Parse the pipe-table benchmark.txt and return data rows (excluding header).

    Each returned tuple has six elements:
    (Function, Calls, Total (s), Avg (s), Min (s), Max (s))
    """
    rows: list[tuple[str, ...]] = []
    header_seen = False
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue  # skip title, separator lines
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        if not header_seen:
            header_seen = True  # skip the header row itself
            continue
        rows.append(tuple(cells))
    return rows


# ── Handlers ──────────────────────────────────────────────────────────────────


def cmd_queue_list(args: argparse.Namespace) -> None:
    """Display a table of tasks in the queue."""
    from rich.table import Table

    from ..cli import get_console

    console = get_console()
    store = TaskStore()
    status = getattr(args, "status", None)
    tasks = store.list_all(status)

    if not tasks:
        msg = f"No {status} tasks." if status else "No tasks in queue."
        console.print(f"[yellow]{msg}[/yellow]")
        return

    table = Table(show_header=True, title="Task Queue")
    table.add_column("ID", width=10, style="cyan")
    table.add_column("Command", width=12)
    table.add_column("Status", width=12)
    table.add_column("Created", width=20)
    table.add_column("Label", ratio=1)

    for t in tasks:
        color = _STATUS_COLORS.get(t["status"], "white")
        table.add_row(
            t["id"],
            t["command"],
            f"[{color}]{t['status']}[/{color}]",
            (t.get("created_at") or "")[:19],
            (t.get("label") or "")[:50],
        )

    console.print(table)


def cmd_queue_status(args: argparse.Namespace) -> None:
    """Show detailed status for a single task, rendered as a Rich table."""
    from rich.table import Table

    from ..cli import get_console

    console = get_console()
    store = TaskStore()
    task = store.get(args.task_id)

    if not task:
        console.print(f"[yellow]Task {args.task_id} not found.[/yellow]")
        return

    results_dir = RESULTS_DIR / task["id"]
    output_file = results_dir / "output.txt"
    benchmark_file = results_dir / "benchmark.txt"
    color = _STATUS_COLORS.get(task["status"], "white")

    # ── Task details table ────────────────────────────────────────────
    table = Table(show_header=True, title=f"Task {task['id']}", title_style="bold")
    table.add_column("Field", style="dim", width=14, no_wrap=True)
    table.add_column("Value", ratio=1)

    table.add_row("Command", task["command"])
    table.add_row("Label", task.get("label") or "")
    table.add_row("Status", f"[{color}]{task['status']}[/{color}]")
    table.add_row("Created", (task.get("created_at") or "")[:19])

    if task.get("started_at"):
        table.add_row("Started", task["started_at"][:19])
    if task.get("finished_at"):
        table.add_row("Finished", task["finished_at"][:19])

    duration = _duration_str(task.get("started_at"), task.get("finished_at"))
    if duration:
        table.add_row("Duration", duration)

    if task.get("error"):
        table.add_row("Error", f"[red]{task['error']}[/red]")
    if output_file.exists():
        table.add_row("Output", str(output_file))
    if task.get("output_path"):
        table.add_row("Output (→)", task["output_path"])
    if benchmark_file.exists():
        table.add_row("Benchmark", str(benchmark_file))

    console.print(table)

    # ── Benchmark table (if available) ────────────────────────────────
    if benchmark_file.exists():
        rows = _parse_benchmark_file(benchmark_file)
        if rows:
            bench_table = Table(show_header=True, title="Benchmark", title_style="bold yellow")
            bench_table.add_column("Function", ratio=1)
            bench_table.add_column("Calls", width=7, justify="right")
            bench_table.add_column("Total (s)", width=10, justify="right")
            bench_table.add_column("Avg (s)", width=9, justify="right")
            bench_table.add_column("Min (s)", width=9, justify="right")
            bench_table.add_column("Max (s)", width=9, justify="right")
            for row in rows:
                bench_table.add_row(*row)
            console.print(bench_table)
