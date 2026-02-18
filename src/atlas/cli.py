"""
Atlas CLI — stdlib argparse, zero third-party import overhead at startup.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from rich.console import Console

    from .utils import DescriptionAttr


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

VERSION = "0.1.0"
PROG_NAME = "atlas"


# ---------------------------------------------------------------------------
# Lazy singletons — nothing heavy is imported until a real command runs
# ---------------------------------------------------------------------------

_console: Optional["Console"] = None


def get_console() -> "Console":
    global _console
    if _console is None:
        from rich.console import Console

        _console = Console()
    return _console


def get_logger():
    from .logger import logger

    return logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _short_name(full: str) -> str:
    """Strip module prefix from a qualified name.
    'atlas.utils.MediaFileManager._clip_media_async' → '_clip_media_async'
    """
    v = full.rsplit(".", 1)
    return v[1] if len(v) > 0 else v[0]


def _print_benchmark_summary() -> None:
    """Print benchmark timing table if --benchmark was requested (set by _state)."""
    if not _state.get("benchmark"):
        return
    from rich.table import Table

    from .benchmark import registry

    stats = registry.all_stats()
    if not stats:
        return
    console = get_console()
    console.print("\n[bold yellow]⏱  Benchmark Summary[/bold yellow]")
    # Use ratio=1 on Function so Rich gives it all remaining terminal width.
    # Numeric columns get fixed widths; they're narrow so Function always fits.
    table = Table(show_header=True, header_style="bold cyan", show_lines=False)
    table.add_column("Function", style="cyan", ratio=1, no_wrap=True, min_width=20)
    table.add_column("Runs", justify="right", width=5, style="dim")
    table.add_column("Total", justify="right", width=8)
    table.add_column("Avg", justify="right", width=7)
    table.add_column("Min", justify="right", width=7)
    table.add_column("Max", justify="right", width=7)
    for s in stats:
        table.add_row(
            _short_name(s.name),
            str(s.calls),
            f"{s.total_s:.2f}s",
            f"{s.avg_s:.2f}s",
            f"{s.min_s:.2f}s",
            f"{s.max_s:.2f}s",
        )
    console.print(table)


def _err(msg: str) -> None:
    get_console().print(f"[red]Error: {msg}[/red]")
    sys.exit(1)


def validate_api_keys(require_gemini: bool = True, require_groq: bool = False) -> None:
    if require_gemini and not os.environ.get("GEMINI_API_KEY"):
        _err("GEMINI_API_KEY environment variable is required.\nSet it with: export GEMINI_API_KEY=your-api-key")
    if require_groq and not os.environ.get("GROQ_API_KEY"):
        _err(
            "GROQ_API_KEY environment variable is required for transcription.\nSet it with: export GROQ_API_KEY=your-api-key"
        )


def parse_duration(duration_str: str) -> int:
    """Parse duration string to seconds: '15s' → 15, '1m30s' → 90, '1h' → 3600."""
    s = duration_str.strip().lower()
    try:
        return int(s)
    except ValueError:
        pass
    total, current = 0, ""
    for ch in s:
        if ch.isdigit():
            current += ch
        elif ch == "h" and current:
            total += int(current) * 3600
            current = ""
        elif ch == "m" and current:
            total += int(current) * 60
            current = ""
        elif ch == "s" and current:
            total += int(current)
            current = ""
    if current:
        total += int(current)
    if total == 0 and s:
        _err(f"Invalid duration format: {duration_str!r} — use e.g. 15s, 1m, 1m30s")
    return total


def validate_video_path(video_path: str) -> Path:
    path = Path(video_path)
    if not path.exists():
        _err(f"Video file not found: {video_path}")
    if not path.is_file():
        _err(f"Not a file: {video_path}")
    return path


def _make_progress():
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=get_console(),
    )


# ---------------------------------------------------------------------------
# Module-level state (set by _run_main before dispatching to a sub-command)
# ---------------------------------------------------------------------------

_state: dict = {"benchmark": False}


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


def _cmd_extract(args: argparse.Namespace) -> None:
    from .utils import DEFAULT_DESCRIPTION_ATTRS, TempPath
    from .video_processor import VideoProcessor, VideoProcessorConfig

    console = get_console()
    validate_api_keys(require_gemini=True, require_groq=True)

    video_path = str(validate_video_path(args.video_path))
    chunk_sec = parse_duration(args.chunk_duration)
    overlap_sec = parse_duration(args.overlap)
    fmt: str = args.format

    description_attrs: List[DescriptionAttr] = list(args.attrs) if args.attrs else DEFAULT_DESCRIPTION_ATTRS
    valid_attrs: set = set(DEFAULT_DESCRIPTION_ATTRS)
    for attr in description_attrs:
        if attr not in valid_attrs:
            _err(f"Invalid attribute: {attr!r} — valid: {', '.join(sorted(valid_attrs))}")

    if fmt not in ("json", "text"):
        _err("--format must be 'json' or 'text'")

    console.print(f"\n[bold blue]Processing video:[/bold blue] {video_path}")
    console.print(f"[dim]Chunk duration: {chunk_sec}s, Overlap: {overlap_sec}s[/dim]")

    async def _run():
        config = VideoProcessorConfig(
            video_path=video_path,
            chunk_duration=chunk_sec,
            overlap=overlap_sec,
            description_attrs=description_attrs,
        )
        with _make_progress() as progress:
            task = progress.add_task("Extracting insights…", total=None)
            async with VideoProcessor(config) as processor:
                result = await processor.process()
            progress.update(task, completed=True)
        return result

    try:
        result = asyncio.run(_run())
        if fmt == "json":
            output_str = json.dumps(result.model_dump(), indent=2)
            if args.output:
                Path(args.output).write_text(output_str)
                console.print(f"[green]Results saved to:[/green] {args.output}")
            else:
                print(output_str)
        else:
            console.print(f"\n[bold green]Results for {video_path}[/bold green]")
            console.print(f"Duration: {result.duration:.2f}s")
            console.print(f"Segments: {len(result.video_descriptions)}\n")
            for desc in result.video_descriptions:
                console.print(f"[bold cyan]Segment {desc.start:.1f}s – {desc.end:.1f}s[/bold cyan]")
                for analysis in desc.video_analysis:
                    label = " ".join(analysis.attr.upper().split("_"))
                    console.print(f"  [yellow]{label}:[/yellow] {analysis.value[:200]}…")
                console.print()
            if args.output:
                Path(args.output).write_text(json.dumps(result.model_dump(), indent=2))
                console.print(f"[green]Full results saved to:[/green] {args.output}")
    except Exception as e:
        console.print(f"[red]Error processing video: {e}[/red]")
        get_logger().exception("Error in extract command")
        sys.exit(1)
    finally:
        TempPath.cleanup()
        _print_benchmark_summary()


def _cmd_index(args: argparse.Namespace) -> None:
    from .utils import TempPath
    from .vector_store import index_video

    console = get_console()
    validate_api_keys(require_gemini=True, require_groq=True)

    video_path = str(validate_video_path(args.video_path))
    chunk_sec = parse_duration(args.chunk_duration)
    overlap_sec = parse_duration(args.overlap)

    console.print(f"\n[bold blue]Indexing video:[/bold blue] {video_path}")
    console.print(f"[dim]Chunk duration: {chunk_sec}s, Overlap: {overlap_sec}s[/dim]")

    async def _run():
        with _make_progress() as progress:
            task = progress.add_task("Processing and indexing video…", total=None)
            indexed_count, result = await index_video(
                video_path=video_path,
                chunk_duration=chunk_sec,
                overlap=overlap_sec,
                store_path=args.store_path,
            )
            progress.update(task, completed=True)
        return indexed_count, result

    try:
        indexed_count, result = asyncio.run(_run())
        console.print("\n[bold green]Indexing complete![/bold green]")
        console.print(f"  Video: {video_path}")
        console.print(f"  Duration: {result.duration:.2f}s")
        console.print(f"  Segments processed: {len(result.video_descriptions)}")
        console.print(f"  Documents indexed: {indexed_count}")
        console.print(f"  Index location: {args.store_path or '~/.atlas/index'}")
    except Exception as e:
        console.print(f"[red]Error indexing video: {e}[/red]")
        get_logger().exception("Error in index command")
        sys.exit(1)
    finally:
        TempPath.cleanup()
        _print_benchmark_summary()


def _cmd_search(args: argparse.Namespace) -> None:
    from rich.table import Table

    from .vector_store import search_video

    console = get_console()
    validate_api_keys(require_gemini=True, require_groq=False)

    try:
        results = asyncio.run(
            search_video(
                query=args.query,
                top_k=args.top_k,
                video_filter=args.video,
                store_path=args.store_path,
            )
        )
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            console.print("Make sure you have indexed some videos first with 'atlas index'")
            return

        console.print(f"\n[bold green]Found {len(results)} results for:[/bold green] '{args.query}'\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Score", justify="right", width=8)
        table.add_column("Video", width=30)
        table.add_column("Time", width=15)
        table.add_column("Content", width=50)
        for i, result in enumerate(results, 1):
            time_str = f"{result.start:.1f}s – {result.end:.1f}s"
            content = result.content[:47] + "…" if len(result.content) > 50 else result.content
            video_name = Path(result.video_path).name
            if len(video_name) > 30:
                video_name = video_name[:27] + "…"
            table.add_row(str(i), f"{result.score:.3f}", video_name, time_str, content)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error searching: {e}[/red]")
        get_logger().exception("Error in search command")
        sys.exit(1)
    finally:
        _print_benchmark_summary()


def _cmd_transcribe(args: argparse.Namespace) -> None:
    from .utils import TempPath
    from .video_processor import extract_transcript

    console = get_console()
    fmt: str = args.format
    if fmt not in ("text", "vtt", "srt"):
        _err("--format must be 'text', 'vtt', or 'srt'")

    validate_api_keys(require_gemini=False, require_groq=True)
    video_path = str(validate_video_path(args.video_path))

    console.print(f"\n[bold blue]Transcribing:[/bold blue] {video_path}")
    console.print(f"[dim]Output format: {fmt}[/dim]")

    async def _run():
        from rich.progress import Progress, SpinnerColumn, TextColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Transcribing…", total=None)
            result = await extract_transcript(video_path, format=fmt)
            progress.update(task, completed=True)
        return result

    try:
        result = asyncio.run(_run())
        if not result:
            console.print("[yellow]No transcript content generated.[/yellow]")
            return
        if args.output:
            Path(args.output).write_text(result)
            console.print(f"[green]Transcript saved to:[/green] {args.output}")
        else:
            console.print("\n[bold green]Transcript:[/bold green]")
            print(result)
    except Exception as e:
        console.print(f"[red]Error transcribing: {e}[/red]")
        get_logger().exception("Error in transcribe command")
        sys.exit(1)
    finally:
        TempPath.cleanup()
        _print_benchmark_summary()


def _cmd_stats(args: argparse.Namespace) -> None:
    from rich.table import Table

    from .vector_store import VectorStore

    console = get_console()
    store = VectorStore()
    stats_data = store.get_stats()

    console.print("\n[bold blue]Atlas Vector Store Statistics[/bold blue]\n")
    table = Table(show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    for key, value in stats_data.items():
        table.add_row(key, str(value))
    console.print(table)
    _print_benchmark_summary()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    # Shared parent that injects --benchmark into every subcommand so it can
    # appear in any position: `atlas transcribe file.mp4 --benchmark`
    # or `atlas --benchmark transcribe file.mp4` both work.
    _shared = argparse.ArgumentParser(add_help=False)
    _shared.add_argument(
        "--benchmark",
        action="store_true",
        default=False,
        help="Print a per-function timing breakdown after the command completes.",
    )

    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description="Atlas — Multimodal insights engine for video understanding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Requires GEMINI_API_KEY for video analysis and GROQ_API_KEY for transcription.\n\n"
            "Examples:\n"
            "  atlas transcribe video.mp4\n"
            "  atlas extract video.mp4 --chunk-duration=15s\n"
            "  atlas index video.mp4 --store-path ./my_index\n"
            "  atlas search 'people discussing AI'\n"
            "  atlas stats\n"
            "  atlas transcribe video.mp4 --benchmark\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"atlas {VERSION}")

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ------------------------------------------------------------------
    # extract
    # ------------------------------------------------------------------
    p_extract = sub.add_parser(
        "extract",
        help="Extract multimodal insights from a video.",
        description="Analyze video content and extract visual cues, interactions, contextual information, audio analysis, and transcripts.",
        epilog="Example:\n  atlas extract video.mp4 --chunk-duration=15s --overlap=1s",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[_shared],
    )
    p_extract.add_argument("video_path", help="Path to the video file.")
    p_extract.add_argument(
        "--chunk-duration", "-c", default="15s", metavar="DUR", help="Duration of each chunk (default: 15s)."
    )
    p_extract.add_argument("--overlap", "-l", default="1s", metavar="DUR", help="Overlap between chunks (default: 1s).")
    p_extract.add_argument(
        "--attrs",
        "-a",
        action="append",
        metavar="ATTR",
        help="Attribute to extract; repeat for multiple (visual_cues, interactions, contextual_information, audio_analysis, transcript).",
    )
    p_extract.add_argument("--output", "-o", metavar="FILE", help="Output file path (JSON).")
    p_extract.add_argument(
        "--format", "-f", default="text", metavar="FMT", help="Output format: json or text (default: text)."
    )
    p_extract.set_defaults(func=_cmd_extract)

    # ------------------------------------------------------------------
    # index
    # ------------------------------------------------------------------
    p_index = sub.add_parser(
        "index",
        help="Index a video for semantic search.",
        description="Process a video and store embeddings in a local vector store for fast semantic search.",
        epilog="Example:\n  atlas index video.mp4 --chunk-duration=15s",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[_shared],
    )
    p_index.add_argument("video_path", help="Path to the video file.")
    p_index.add_argument(
        "--chunk-duration", "-c", default="15s", metavar="DUR", help="Duration of each chunk (default: 15s)."
    )
    p_index.add_argument("--overlap", "-o", default="0s", metavar="DUR", help="Overlap between chunks (default: 0s).")
    p_index.add_argument("--store-path", "-s", default=None, metavar="DIR", help="Path to store the vector index.")
    p_index.add_argument(
        "--embedding-dim",
        "-e",
        type=int,
        default=768,
        metavar="N",
        help="Embedding dimension: 768 or 3072 (default: 768).",
    )
    p_index.set_defaults(func=_cmd_index)

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------
    p_search = sub.add_parser(
        "search",
        help="Search indexed videos semantically.",
        description="Run a natural-language query against previously indexed videos.",
        epilog="Example:\n  atlas search 'people discussing AI'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[_shared],
    )
    p_search.add_argument("query", help="Natural-language search query.")
    p_search.add_argument(
        "--top-k", "-k", type=int, default=10, metavar="N", help="Number of results to return (default: 10)."
    )
    p_search.add_argument(
        "--video", "-v", default=None, metavar="FILE", help="Filter results to a specific video path."
    )
    p_search.add_argument("--store-path", "-s", default=None, metavar="DIR", help="Path to the vector index.")
    p_search.set_defaults(func=_cmd_search)

    # ------------------------------------------------------------------
    # transcribe
    # ------------------------------------------------------------------
    p_transcribe = sub.add_parser(
        "transcribe",
        help="Extract transcript from a video or audio file.",
        description="Transcribe a video or audio file using Groq Whisper.",
        epilog="Example:\n  atlas transcribe video.mp4 --format=srt --output=transcript.srt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[_shared],
    )
    p_transcribe.add_argument("video_path", help="Path to the video or audio file.")
    p_transcribe.add_argument(
        "--format", "-f", default="text", metavar="FMT", help="Output format: text, vtt, or srt (default: text)."
    )
    p_transcribe.add_argument("--output", "-o", default=None, metavar="FILE", help="Output file path.")
    p_transcribe.set_defaults(func=_cmd_transcribe)

    # ------------------------------------------------------------------
    # stats
    # ------------------------------------------------------------------
    p_stats = sub.add_parser(
        "stats",
        help="Show statistics about the local vector store.",
        description="Display key metrics about the local Atlas vector index.",
        epilog="Example:\n  atlas stats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[_shared],
    )
    p_stats.set_defaults(func=_cmd_stats)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _format_elapsed(seconds: float) -> str:
    """Return a human-readable duration string.

    Examples: 0.91s → '0.91s'  |  90.4s → '1m 30s'  |  3661s → '1h 1m 1s'
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {secs}s"


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Store global flags before dispatching
    _state["benchmark"] = args.benchmark

    # Load .env only when a real command is about to run (never on --help/--version
    # since those exit during parse_args before we reach here).
    from time import perf_counter

    from dotenv import load_dotenv

    load_dotenv()

    t0 = perf_counter()
    try:
        args.func(args)
    finally:
        elapsed = perf_counter() - t0
        get_console().print(f"\n[dim]Execution time: {_format_elapsed(elapsed)}[/dim]")


if __name__ == "__main__":
    main()
