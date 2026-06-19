from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class MoveOccurrence:
    fen: str
    move_uci: str
    move_san: str
    ply: int
    color: str


@dataclass
class MoveAggregate:
    fen: str
    move_uci: str
    move_san: str
    color: str
    count: int = 0
    plies: List[int] = field(default_factory=list)

    def add(self, occurrence: MoveOccurrence) -> None:
        self.count += 1
        self.plies.append(occurrence.ply)
        if len(occurrence.move_san) > len(self.move_san):
            self.move_san = occurrence.move_san


@dataclass(frozen=True)
class ExplorerMove:
    uci: str
    san: str
    white: int
    draws: int
    black: int

    @property
    def total(self) -> int:
        return self.white + self.draws + self.black

    def score_for(self, color: str) -> float:
        decisive = self.white if color == "white" else self.black
        return (decisive + 0.5 * self.draws) / self.total if self.total else 0.0

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "ExplorerMove":
        return cls(
            uci=payload["uci"],
            san=payload.get("san") or payload["uci"],
            white=int(payload.get("white", 0)),
            draws=int(payload.get("draws", 0)),
            black=int(payload.get("black", 0)),
        )
