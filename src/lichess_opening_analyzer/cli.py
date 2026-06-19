from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .analysis import analyze_moves
from .explorer import ExplorerCache, LichessExplorerClient
from .lichess import download_games
from .pgn import aggregate_pgn
from .report import write_csv, write_markdown

DEFAULT_RATINGS = [1800, 2000, 2200]
DEFAULT_SPEEDS = ["rapid", "classical"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find repeated opening moves that score worse than common Lichess Explorer alternatives.")
    parser.add_argument("--username", required=True, help="Lichess username whose games should be analyzed.")
    parser.add_argument("--pgn", type=Path, help="Existing PGN export. If omitted, games are downloaded from Lichess.")
    parser.add_argument("--download-to", type=Path, default=Path("data/games.pgn"), help="Where to save downloaded games when --pgn is omitted.")
    parser.add_argument("--max-games", type=int, help="Maximum recent games to download from Lichess.")
    parser.add_argument("--since", help="Only download games since this ISO date, e.g. 2025-01-01.")
    parser.add_argument("--until", help="Only download games until this ISO date, e.g. 2026-01-01.")
    parser.add_argument("--color", choices=["white", "black", "both"], default="both", help="Analyze only moves you played as this color.")
    parser.add_argument("--max-fullmove", type=int, default=12, help="Opening depth limit in full moves.")
    parser.add_argument("--min-own-occurrences", type=int, default=3, help="Minimum times you must have played the move.")
    parser.add_argument("--min-explorer-games", type=int, default=1000, help="Minimum total Explorer games for the position.")
    parser.add_argument("--min-move-games", type=int, default=100, help="Minimum Explorer games for each compared move.")
    parser.add_argument("--ratings", nargs="+", type=int, default=DEFAULT_RATINGS, help="Lichess Explorer rating buckets, e.g. 1800 2000 2200.")
    parser.add_argument("--speeds", nargs="+", default=DEFAULT_SPEEDS, help="Explorer speed filters, e.g. rapid classical blitz.")
    parser.add_argument("--cache", type=Path, default=Path(".cache/lichess_explorer.sqlite3"), help="SQLite cache for Explorer API responses.")
    parser.add_argument("--output", type=Path, default=Path("reports/opening_leaks.md"), help="Report output path.")
    parser.add_argument("--format", choices=["markdown", "csv"], default="markdown", help="Report format.")
    parser.add_argument("--sort", choices=["delta", "impact"], default="delta", help="Sort by score deficit or frequency-weighted impact.")
    parser.add_argument("--max-alternatives", type=int, default=8, help="Only consider this many best-scoring common moves as alternatives.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    pgn_path = args.pgn or args.download_to
    if args.pgn is None:
        download_games(args.username, pgn_path, args.max_games, args.since, args.until)

    aggregates = aggregate_pgn(pgn_path, args.username, args.color, args.max_fullmove)
    cache = ExplorerCache(args.cache)
    try:
        client = LichessExplorerClient(cache, args.speeds, args.ratings)
        findings = analyze_moves(
            aggregates,
            client,
            min_own_occurrences=args.min_own_occurrences,
            min_explorer_games=args.min_explorer_games,
            min_move_games=args.min_move_games,
            max_alternatives=args.max_alternatives,
        )
    finally:
        cache.close()

    if args.format == "csv":
        write_csv(findings, args.output, args.sort)
    else:
        write_markdown(findings, args.output, args.sort)
    print(f"Analyzed {len(aggregates)} repeated move candidates; wrote {len(findings)} findings to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
