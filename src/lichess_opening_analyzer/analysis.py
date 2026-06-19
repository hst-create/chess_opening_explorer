from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .explorer import LichessExplorerClient
from .models import ExplorerMove, MoveAggregate

ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class Finding:
    move: MoveAggregate
    explorer_total: int
    played_score: float
    best_alternative: ExplorerMove
    best_score: float

    @property
    def delta(self) -> float:
        return self.played_score - self.best_score

    @property
    def impact(self) -> float:
        return self.move.count * (self.best_score - self.played_score)


def analyze_moves(
    aggregates: dict[tuple[str, str], MoveAggregate],
    client: LichessExplorerClient,
    min_own_occurrences: int,
    min_explorer_games: int,
    min_move_games: int,
    max_alternatives: int,
    progress_callback: ProgressCallback | None = None,
    min_ply: int = 4,
    include_lines: list[str] | None = None,
    exclude_lines: list[str] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    repeated_aggregates = [
        aggregate
        for aggregate in aggregates.values()
        if aggregate.count >= min_own_occurrences and _is_allowed_line(aggregate, min_ply, include_lines, exclude_lines)
    ]
    unique_fens = list(dict.fromkeys(aggregate.fen for aggregate in repeated_aggregates))
    total = len(unique_fens)
    explorer_payloads: dict[str, dict[str, Any]] = {}
    for index, fen in enumerate(unique_fens, start=1):
        explorer_payloads[fen] = client.get_position(fen)
        if progress_callback is not None:
            progress_callback(index, total)

    for aggregate in repeated_aggregates:
        payload = explorer_payloads[aggregate.fen]
        explorer_total = int(payload.get("white", 0)) + int(payload.get("draws", 0)) + int(payload.get("black", 0))
        if explorer_total < min_explorer_games:
            continue
        common_moves = [m for m in client.moves(payload) if m.total >= min_move_games]
        played = next((m for m in common_moves if m.uci == aggregate.move_uci), None)
        if played is None:
            continue
        candidates = sorted(common_moves, key=lambda m: m.score_for(aggregate.color), reverse=True)[:max_alternatives]
        if not candidates:
            continue
        best = candidates[0]
        played_score = played.score_for(aggregate.color)
        best_score = best.score_for(aggregate.color)
        if best.uci != played.uci and best_score > played_score:
            findings.append(Finding(aggregate, explorer_total, played_score, best, best_score))
    return sorted(findings, key=lambda item: (item.best_score - item.played_score, item.impact), reverse=True)


def _is_allowed_line(
    aggregate: MoveAggregate, min_ply: int, include_lines: list[str] | None, exclude_lines: list[str] | None
) -> bool:
    first_seen_ply = min(aggregate.plies) if aggregate.plies else _infer_ply(aggregate.line_san)
    if first_seen_ply < min_ply:
        return False
    normalized_line = aggregate.line_san.casefold()
    includes = _normalize_patterns(include_lines)
    excludes = _normalize_patterns(exclude_lines)
    if includes and not any(pattern in normalized_line for pattern in includes):
        return False
    return not any(pattern in normalized_line for pattern in excludes)


def _normalize_patterns(patterns: list[str] | None) -> list[str]:
    return [pattern.casefold().strip() for pattern in patterns or [] if pattern.strip()]


def _infer_ply(line_san: str) -> int:
    return sum(1 for token in line_san.split() if not token.rstrip('.').isdigit() and token != '...')
