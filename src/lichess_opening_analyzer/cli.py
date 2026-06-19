from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .analysis import analyze_moves
from .explorer import ExplorerCache, LichessExplorerClient
from .lichess import download_games
from .pgn import aggregate_pgn
from .report import write_csv, write_markdown

DEFAULT_RATINGS = [1800, 2000, 2200]
DEFAULT_SPEEDS = ["rapid", "classical"]
PROGRESS_INTERVAL_SECONDS = 2.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find repeated opening moves that score worse than common Lichess Explorer alternatives.")
    parser.add_argument("--username", required=True, help="Lichess username whose games should be analyzed.")
    parser.add_argument("--pgn", type=Path, help="Existing PGN export. If omitted, games are downloaded from Lichess.")
    parser.add_argument("--download-to", type=Path, default=Path("data/games.pgn"), help="Where to save downloaded games when --pgn is omitted.")
    parser.add_argument("--max-games", type=int, help="Maximum recent games to download from Lichess.")
    parser.add_argument("--since", help="Only download games since this ISO date, e.g. 2025-01-01.")
    parser.add_argument("--until", help="Only download games until this ISO date, e.g. 2026-01-01.")
    parser.add_argument("--lichess-token", help="Lichess personal access token for downloading private/non-public games. Defaults to LICHESS_TOKEN.")
    parser.add_argument("--color", choices=["white", "black", "both"], default="both", help="Analyze only moves you played as this color.")
    parser.add_argument("--max-fullmove", type=int, default=12, help="Opening depth limit in full moves.")
    parser.add_argument("--min-own-occurrences", type=int, default=3, help="Minimum times you must have played the move.")
    parser.add_argument("--min-ply", type=int, default=4, help="Ignore moves before this ply. The default 4 skips the first three half-moves.")
    parser.add_argument(
        "--include-line",
        action="append",
        default=[],
        help="Only report lines whose SAN sequence contains this text. Repeat to allow multiple repertoire branches.",
    )
    parser.add_argument(
        "--exclude-line",
        action="append",
        default=[],
        help="Do not report lines whose SAN sequence contains this text. Repeat to hide lines you no longer play.",
    )
    parser.add_argument("--min-explorer-games", type=int, default=1000, help="Minimum total Explorer games for the position.")
    parser.add_argument("--min-move-games", type=int, default=100, help="Minimum Explorer games for each compared move.")
    parser.add_argument("--ratings", nargs="+", type=int, default=DEFAULT_RATINGS, help="Lichess Explorer rating buckets, e.g. 1800 2000 2200.")
    parser.add_argument("--speeds", nargs="+", default=DEFAULT_SPEEDS, help="Explorer speed filters, e.g. rapid classical blitz.")
    parser.add_argument("--cache", type=Path, default=Path(".cache/lichess_explorer.sqlite3"), help="SQLite cache for Explorer API responses.")
    parser.add_argument("--output", type=Path, default=Path("reports/opening_leaks.md"), help="Report output path.")
    parser.add_argument("--format", choices=["markdown", "csv"], default="markdown", help="Report format.")
    parser.add_argument("--sort", choices=["delta", "impact"], default="delta", help="Sort by score deficit or frequency-weighted impact.")
    parser.add_argument("--max-alternatives", type=int, default=8, help="Only consider this many best-scoring common moves as alternatives.")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output and only print the final summary.")
    return parser


class ProgressReporter:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.started_at = time.monotonic()
        self.last_update = 0.0

    def message(self, text: str) -> None:
        if self.enabled:
            print(text, file=sys.stderr, flush=True)

    def explorer_update(self, current: int, total: int) -> None:
        if not self.enabled:
            return
        now = time.monotonic()
        if current != total and now - self.last_update < PROGRESS_INTERVAL_SECONDS:
            return
        self.last_update = now
        elapsed = now - self.started_at
        percent = (current / total * 100) if total else 100.0
        eta = _format_duration((elapsed / current) * (total - current)) if current else "unknown"
        print(
            f"Explorer queries: {current}/{total} ({percent:.1f}%) elapsed {_format_duration(elapsed)}, ETA {eta}",
            file=sys.stderr,
            flush=True,
        )


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, remaining_minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {remaining_minutes}m"
    if remaining_minutes:
        return f"{remaining_minutes}m {remaining_seconds}s"
    return f"{remaining_seconds}s"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    progress = ProgressReporter(enabled=not args.quiet)
    pgn_path = args.pgn or args.download_to
    if args.pgn is None:
        limit = f" up to {args.max_games:,} games" if args.max_games else " games"
        progress.message(f"Downloading{limit} for {args.username} to {pgn_path}...")
        download_games(args.username, pgn_path, args.max_games, args.since, args.until, args.lichess_token)

    progress.message(f"Parsing {pgn_path} through fullmove {args.max_fullmove}...")
    aggregates = aggregate_pgn(pgn_path, args.username, args.color, args.max_fullmove)
    repeated_candidates = sum(1 for aggregate in aggregates.values() if aggregate.count >= args.min_own_occurrences)
    progress.message(
        f"Found {len(aggregates):,} unique move candidates; {repeated_candidates:,} meet "
        f"--min-own-occurrences {args.min_own_occurrences}. Moves before ply {args.min_ply} and "
        "line filters are applied before Explorer queries."
    )
    cache = ExplorerCache(args.cache)
    try:
        client = LichessExplorerClient(cache, args.speeds, args.ratings, token=args.lichess_token)
        findings = analyze_moves(
            aggregates,
            client,
            min_own_occurrences=args.min_own_occurrences,
            min_explorer_games=args.min_explorer_games,
            min_move_games=args.min_move_games,
            max_alternatives=args.max_alternatives,
            progress_callback=progress.explorer_update,
            min_ply=args.min_ply,
            include_lines=args.include_line,
            exclude_lines=args.exclude_line,
        )
    finally:
        cache.close()

    if args.format == "csv":
        write_csv(findings, args.output, args.sort)
    else:
        write_markdown(findings, args.output, args.sort)
    print(f"Analyzed {len(aggregates)} unique move candidates; wrote {len(findings)} findings to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
