"""CLI sub-commands for ``atlas queue list`` and ``atlas queue status``."""

from __future__ import annotations

import argparse
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
    p_list.set_defaults(func=_cmd_queue_list)

    # atlas queue status
    p_status = sub.add_parser("status", help="Show status of a specific task.")
    p_status.add_argument("--task-id", "-t", required=True, help="Task ID to check.")
    p_status.set_defaults(func=_cmd_queue_status)


# ── Handlers ──────────────────────────────────────────────────────────────────


def _cmd_queue_list(args: argparse.Namespace) -> None:
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


def _cmd_queue_status(args: argparse.Namespace) -> None:
    """Show detailed status for a single task."""
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

    console.print(f"\n[bold]Task {task['id']}[/bold]")
    console.print(f"  Command:    {task['command']}")
    console.print(f"  Label:      {task.get('label', '')}")
    console.print(f"  Status:     [{color}]{task['status']}[/{color}]")
    console.print(f"  Created:    {task['created_at']}")
    if task.get("started_at"):
        console.print(f"  Started:    {task['started_at']}")
    if task.get("finished_at"):
        console.print(f"  Finished:   {task['finished_at']}")
    if task.get("error"):
        console.print(f"  [red]Error:[/red]     {task['error']}")
    if output_file.exists():
        console.print(f"  Output:     {output_file}")
    if task.get("output_path"):
        console.print(f"  Output (→): {task['output_path']}")
    if benchmark_file.exists():
        console.print(f"  Benchmark:  {benchmark_file}")
