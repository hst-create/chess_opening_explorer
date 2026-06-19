from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
) -> list[Finding]:
    findings: list[Finding] = []
    repeated_aggregates = [aggregate for aggregate in aggregates.values() if aggregate.count >= min_own_occurrences]
    total = len(repeated_aggregates)
    for index, aggregate in enumerate(repeated_aggregates, start=1):
        payload = client.get_position(aggregate.fen)
        if progress_callback is not None:
            progress_callback(index, total)
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
