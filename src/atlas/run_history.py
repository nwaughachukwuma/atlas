"""Helpers for persisted run history across queued and direct operations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from .benchmark import BenchmarkStats, registry
from .settings import settings
from .task_queue import serialize_result, write_file
from .task_queue.config import TaskStatus
from .task_queue.store import RunStore
from .uuid import uuid

RUNS_DIR = Path(settings.atlas_home) / "runs"
DIRECT_RESULTS_DIR = RUNS_DIR / "results"


def create_run_id(size: int = 10) -> str:
    """Return a unique run ID for non-queued media operations."""
    return uuid(size)


def direct_results_dir_for(run_id: str) -> Path:
    """Return the persisted results directory for a direct run."""
    return DIRECT_RESULTS_DIR / run_id


def direct_output_file_for(run_id: str) -> Path:
    """Return the canonical output file path for a direct run."""
    return direct_results_dir_for(run_id) / "output.json"


def direct_benchmark_file_for(run_id: str) -> Path:
    """Return the canonical benchmark file path for a direct run."""
    return direct_results_dir_for(run_id) / "benchmark.txt"


def parse_output_content(path: Path) -> tuple[Any, str]:
    """Return stored output content and its content kind."""
    content = path.read_text()
    try:
        return json.loads(content), "json"
    except json.JSONDecodeError:
        return content, "text"


def build_benchmark_summary(stats: list[BenchmarkStats], total_s: float | None = None) -> str:
    """Render benchmark stats as an ASCII table."""
    if not stats:
        return ""

    headers = ("Function", "Calls", "Total (s)", "Avg (s)", "Min (s)", "Max (s)")
    rows = [
        (
            s.name,
            str(s.calls),
            f"{s.total_s:.3f}",
            f"{s.avg_s:.3f}",
            f"{s.min_s:.3f}",
            f"{s.max_s:.3f}",
        )
        for s in stats
    ]

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def _fmt_row(cells: tuple[str, ...]) -> str:
        return "| " + " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cells)) + " |"

    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    lines = [
        "Benchmark Summary",
        sep,
        _fmt_row(headers),
        sep,
        *[_fmt_row(r) for r in rows],
        sep,
    ]
    if total_s is not None:
        lines.append(f"\nTotal runtime: {total_s:.2f}s")
    return "\n".join(lines)


@dataclass(slots=True)
class DirectRunContext:
    run_id: str
    command: str
    label: str
    input_path: str
    output_path: Path
    benchmark_path: Path
    requested_output_path: str | None
    fmt: str | None
    benchmark_requested: bool
    started_perf: float
    benchmark_snapshot: dict[str, int] | None


def start_direct_run(
    *,
    command: str,
    label: str,
    input_path: str,
    requested_output_path: str | None = None,
    fmt: str | None = None,
    metadata: dict[str, Any] | None = None,
    benchmark: bool = False,
) -> DirectRunContext:
    """Create and mark a new direct run as running."""
    run_id = create_run_id()
    output_path = direct_output_file_for(run_id)
    benchmark_path = direct_benchmark_file_for(run_id)
    store = RunStore()
    store.add(
        run_id,
        command,
        label,
        mode="direct",
        status=TaskStatus.PENDING,
        input_path=input_path,
        output_path=str(output_path),
        user_output_path=requested_output_path,
        benchmark_path=str(benchmark_path) if benchmark else None,
        fmt=fmt,
        metadata=metadata,
    )
    store.mark_running(run_id)
    return DirectRunContext(
        run_id=run_id,
        command=command,
        label=label,
        input_path=input_path,
        output_path=output_path,
        benchmark_path=benchmark_path,
        requested_output_path=requested_output_path,
        fmt=fmt,
        benchmark_requested=benchmark,
        started_perf=perf_counter(),
        benchmark_snapshot=registry.snapshot() if benchmark else None,
    )


def complete_direct_run(
    context: DirectRunContext,
    result: Any,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist direct-run output and optional benchmark data."""
    content = serialize_result(result)
    write_file(context.output_path, content)
    if context.requested_output_path:
        write_file(Path(context.requested_output_path), content)

    benchmark_path: str | None = None
    if context.benchmark_requested:
        stats = registry.delta_stats(context.benchmark_snapshot)
        benchmark_content = build_benchmark_summary(stats, total_s=perf_counter() - context.started_perf)
        if benchmark_content:
            write_file(context.benchmark_path, benchmark_content)
            benchmark_path = str(context.benchmark_path)

    RunStore().mark_completed(
        context.run_id,
        output_path=str(context.output_path),
        benchmark_path=benchmark_path,
        user_output_path=context.requested_output_path,
        metadata=metadata,
    )
    return {
        "run_id": context.run_id,
        "command": context.command,
        "queued": False,
        "status": TaskStatus.COMPLETED,
        "output_path": str(context.output_path),
        "benchmark_path": benchmark_path,
        "user_output_path": context.requested_output_path,
    }


def fail_direct_run(
    context: DirectRunContext,
    error: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a direct-run failure for later inspection."""
    error_content = json.dumps({"error": error}, indent=2)
    write_file(context.output_path, error_content)
    if context.requested_output_path:
        write_file(Path(context.requested_output_path), error_content)

    RunStore().mark_failed(
        context.run_id,
        error,
        output_path=str(context.output_path),
        user_output_path=context.requested_output_path,
        metadata=metadata,
    )
    return {
        "run_id": context.run_id,
        "command": context.command,
        "queued": False,
        "status": TaskStatus.FAILED,
        "output_path": str(context.output_path),
        "benchmark_path": None,
        "user_output_path": context.requested_output_path,
        "error": error,
    }
