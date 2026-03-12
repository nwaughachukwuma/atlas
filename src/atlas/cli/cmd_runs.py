"""CLI subcommands for persisted run history."""

from __future__ import annotations

import argparse
import json
from typing import Any

from ..task_queue.commands import _duration_str
from ..task_queue.helpers import deserialize_result, get_result_artifacts
from ..task_queue.run_history_store import RunHistoryStore


def add_run_history_commands(subparsers: Any) -> None:
    """Register ``atlas runs list`` and ``atlas runs status``."""
    p_runs = subparsers.add_parser(
        "runs",
        help="Inspect persisted run history.",
        description="View persisted run history for queued and direct transcribe / extract / index operations.",
        epilog=(
            "Examples:\n"
            "  atlas runs list\n"
            "  atlas runs list --command transcribe --run-type direct\n"
            "  atlas runs status --run-id abc12345\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p_runs.add_subparsers(dest="runs_command", metavar="<action>")
    sub.required = True

    p_list = sub.add_parser("list", help="List persisted runs.")
    p_list.add_argument(
        "--status",
        "-s",
        choices=["pending", "running", "completed", "failed", "timeout"],
        help="Filter by status.",
    )
    p_list.add_argument(
        "--command",
        choices=["transcribe", "extract", "index"],
        help="Filter by command.",
    )
    p_list.add_argument(
        "--run-type",
        choices=["queued", "direct"],
        dest="run_type",
        help="Filter by execution mode.",
    )
    p_list.set_defaults(func=cmd_runs_list)

    p_status = sub.add_parser("status", help="Show status for a persisted run.")
    p_status.add_argument("--run-id", "-r", required=True, help="Run ID to inspect.")
    p_status.set_defaults(func=cmd_runs_status)


def _build_run_output(run: dict[str, Any]) -> dict[str, Any]:
    """Return the JSON-serialisable response shape for a run-history record."""
    output = dict(run)
    output["duration"] = _duration_str(run.get("started_at"), run.get("finished_at")) or None
    requested_output_path = output.get("output_path")
    artifacts = get_result_artifacts(run)
    if requested_output_path:
        output["requested_output_path"] = requested_output_path
    if artifacts["result_path"]:
        output["output_path"] = artifacts["result_path"]
    if artifacts["benchmark_path"]:
        output["benchmark_path"] = artifacts["benchmark_path"]
    if artifacts["result_text"] is not None:
        output["result"] = deserialize_result(artifacts["result_text"])
    if artifacts["benchmark_text"] is not None:
        output["benchmark_text"] = artifacts["benchmark_text"]
    return output


def cmd_runs_list(args: argparse.Namespace) -> None:
    """Print a JSON list of persisted runs."""
    store = RunHistoryStore()
    status = getattr(args, "status", None)
    command = getattr(args, "command", None)
    run_type = getattr(args, "run_type", None)
    runs = [_build_run_output(run) for run in store.list_all(status, command=command, run_type=run_type)]
    print(
        json.dumps(
            {
                "status_filter": status,
                "command_filter": command,
                "run_type_filter": run_type,
                "count": len(runs),
                "tasks": runs,
            },
            indent=2,
            default=str,
        )
    )


def cmd_runs_status(args: argparse.Namespace) -> None:
    """Print detailed status for a persisted run."""
    store = RunHistoryStore()
    run = store.get(args.run_id)
    if not run:
        print(json.dumps({"error": f"Run {args.run_id} not found"}))
        return
    print(json.dumps(_build_run_output(run), indent=2, default=str))
