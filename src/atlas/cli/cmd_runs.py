"""
CLI sub-commands for inspecting transcribe/extract/index run
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, cast

from ..task_queue import RunStore


def add_run_commands(subparsers: Any) -> None:
    """Register atlas runs list/show/output/benchmark sub-commands."""
    p_runs = subparsers.add_parser(
        "runs",
        help="Inspect transcribe/extract/index runs.",
        description="View run history and retrieve stored output and benchmarks.",
        epilog=(
            "Examples:\n"
            "  atlas runs list\n"
            "  atlas runs list --command transcribe --mode direct\n"
            "  atlas runs show --run-id abc123\n"
            "  atlas runs output --run-id abc123\n"
            "  atlas runs benchmark --run-id abc123\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p_runs.add_subparsers(dest="runs_command", metavar="<action>")
    sub.required = True

    p_list = sub.add_parser("list", help="List all runs.")
    p_list.add_argument("--status", choices=["pending", "running", "completed", "failed", "timeout"])
    p_list.add_argument("--command", choices=["transcribe", "extract", "index"])
    p_list.add_argument("--mode", choices=["queued", "direct"])
    p_list.add_argument("--limit", type=int, default=50)
    p_list.set_defaults(func=cmd_runs_list)

    p_show = sub.add_parser("show", help="Show metadata for one run.")
    p_show.add_argument("--run-id", "-r", required=True)
    p_show.set_defaults(func=cmd_runs_show)

    p_output = sub.add_parser("output", help="Print stored output for one run.")
    p_output.add_argument("--run-id", "-r", required=True)
    p_output.set_defaults(func=cmd_runs_output)

    p_benchmark = sub.add_parser("benchmark", help="Print stored benchmark output for one run.")
    p_benchmark.add_argument("--run-id", "-r", required=True)
    p_benchmark.set_defaults(func=cmd_runs_benchmark)


def _get_run_or_error(run_id: str) -> dict | None:
    run = RunStore().get(run_id)
    if run is None:
        print(json.dumps({"error": f"Run {run_id} not found"}))
        return None
    return run


def cmd_runs_list(args: argparse.Namespace) -> dict[str, Any]:
    runs = RunStore().list_all(
        status=getattr(args, "status", None),
        command=getattr(args, "command", None),
        mode=getattr(args, "mode", None),
        limit=getattr(args, "limit", None),
    )
    result = {
        "count": len(runs),
        "status_filter": getattr(args, "status", None),
        "command_filter": getattr(args, "command", None),
        "mode_filter": getattr(args, "mode", None),
        "runs": runs,
    }
    print(json.dumps(result, indent=2, default=str))
    return result


def cmd_runs_show(args: argparse.Namespace) -> dict[str, Any] | None:
    run = _get_run_or_error(args.run_id)
    if run is None:
        return
    print(json.dumps(run, indent=2, default=str))
    return run


def cmd_runs_output(args: argparse.Namespace) -> str | Dict | None:
    run = _get_run_or_error(args.run_id)
    if run is None:
        return

    output_text = run.get("output_text")
    if not output_text:
        print(json.dumps({"error": f"No stored output found for run {args.run_id}"}))
        return

    try:
        content = json.loads(output_text)
        print(json.dumps(content, indent=2, default=str))
        return content
    except json.JSONDecodeError:
        print(output_text)
        return output_text


def cmd_runs_benchmark(args: argparse.Namespace):
    run = _get_run_or_error(args.run_id)
    if run is None:
        return
    benchmark_text = run.get("benchmark_text")
    if not benchmark_text:
        print(json.dumps({"error": f"No stored benchmark found for run {args.run_id}"}))
        return
    print(benchmark_text)
    return cast(str, benchmark_text)
