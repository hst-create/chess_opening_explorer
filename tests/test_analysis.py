from __future__ import annotations

from lichess_opening_analyzer.analysis import analyze_moves
from lichess_opening_analyzer.models import MoveAggregate


class FakeClient:
    def get_position(self, fen: str):
        return {
            "white": 600,
            "draws": 100,
            "black": 300,
            "moves": [
                {"uci": "e2e4", "san": "e4", "white": 45, "draws": 10, "black": 45},
                {"uci": "d2d4", "san": "d4", "white": 60, "draws": 20, "black": 20},
            ],
        }

    @staticmethod
    def moves(payload):
        from lichess_opening_analyzer.explorer import LichessExplorerClient

        return LichessExplorerClient.moves(payload)


def test_analyze_moves_reports_worse_repeated_move() -> None:
    aggregate = MoveAggregate("startpos", "e2e4", "e4", "white", count=5)

    findings = analyze_moves({("startpos", "e2e4"): aggregate}, FakeClient(), 3, 100, 10, 8)  # type: ignore[arg-type]

    assert len(findings) == 1
    assert findings[0].best_alternative.san == "d4"
    assert round(findings[0].delta, 2) == -0.20


def test_analyze_moves_reports_progress_for_repeated_candidates_only() -> None:
    repeated = MoveAggregate("startpos", "e2e4", "e4", "white", count=5)
    single = MoveAggregate("other", "g1f3", "Nf3", "white", count=1)
    updates: list[tuple[int, int]] = []

    analyze_moves(
        {("startpos", "e2e4"): repeated, ("other", "g1f3"): single},
        FakeClient(),  # type: ignore[arg-type]
        3,
        100,
        10,
        8,
        progress_callback=lambda current, total: updates.append((current, total)),
    )

    assert updates == [(1, 1)]


class CountingFakeClient(FakeClient):
    def __init__(self) -> None:
        self.requested_fens: list[str] = []

    def get_position(self, fen: str):
        self.requested_fens.append(fen)
        return super().get_position(fen)


def test_analyze_moves_queries_each_repeated_position_once() -> None:
    first = MoveAggregate("startpos", "e2e4", "e4", "white", count=5)
    second = MoveAggregate("startpos", "d2d4", "d4", "white", count=4)
    other = MoveAggregate("other", "e2e4", "e4", "white", count=3)
    client = CountingFakeClient()
    updates: list[tuple[int, int]] = []

    analyze_moves(
        {
            ("startpos", "e2e4"): first,
            ("startpos", "d2d4"): second,
            ("other", "e2e4"): other,
        },
        client,  # type: ignore[arg-type]
        3,
        100,
        10,
        8,
        progress_callback=lambda current, total: updates.append((current, total)),
    )

    assert client.requested_fens == ["startpos", "other"]
    assert updates == [(1, 2), (2, 2)]
