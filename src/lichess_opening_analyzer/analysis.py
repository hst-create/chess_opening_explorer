from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .explorer import LichessExplorerClient
from .models import ExplorerMove, MoveAggregate


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
    aggregates: Dict[Tuple[str, str], MoveAggregate],
    client: LichessExplorerClient,
    min_own_occurrences: int,
    min_explorer_games: int,
    min_move_games: int,
    max_alternatives: int,
) -> List[Finding]:
    findings: List[Finding] = []
    for aggregate in aggregates.values():
        if aggregate.count < min_own_occurrences:
            continue
        payload = client.get_position(aggregate.fen)
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
