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
    aggregate = MoveAggregate("startpos", "e2e4", "e4", "white", "1. e4", count=5, plies=[4, 4, 4, 4, 4])

    findings = analyze_moves({("startpos", "e2e4"): aggregate}, FakeClient(), 3, 100, 10, 8)  # type: ignore[arg-type]

    assert len(findings) == 1
    assert findings[0].best_alternative.san == "d4"
    assert round(findings[0].delta, 2) == -0.20


def test_analyze_moves_reports_progress_for_repeated_candidates_only() -> None:
    repeated = MoveAggregate("startpos", "e2e4", "e4", "white", "1. e4", count=5, plies=[4, 4, 4, 4, 4])
    single = MoveAggregate("other", "g1f3", "Nf3", "white", "1. Nf3", count=1, plies=[4])
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
    first = MoveAggregate("startpos", "e2e4", "e4", "white", "1. e4", count=5, plies=[4, 4, 4, 4, 4])
    second = MoveAggregate("startpos", "d2d4", "d4", "white", "1. d4", count=4, plies=[4, 4, 4, 4])
    other = MoveAggregate("other", "e2e4", "e4", "white", "1. e4", count=3, plies=[4, 4, 4])
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


def test_analyze_moves_ignores_early_plies_by_default() -> None:
    aggregate = MoveAggregate("startpos", "e2e4", "e4", "white", "1. e4", count=5, plies=[1, 1, 1, 1, 1])

    findings = analyze_moves({("startpos", "e2e4"): aggregate}, FakeClient(), 3, 100, 10, 8)  # type: ignore[arg-type]

    assert findings == []


def test_analyze_moves_filters_lines() -> None:
    sicilian = MoveAggregate(
        "startpos", "e2e4", "e4", "white", "1. e4 c5 2. Nf3 d6 3. d4", count=5, plies=[5, 5, 5, 5, 5]
    )
    caro = MoveAggregate(
        "caro", "e2e4", "e4", "white", "1. e4 c6 2. d4 d5 3. Nc3", count=5, plies=[5, 5, 5, 5, 5]
    )

    findings = analyze_moves(
        {("startpos", "e2e4"): sicilian, ("caro", "e2e4"): caro},
        FakeClient(),  # type: ignore[arg-type]
        3,
        100,
        10,
        8,
        include_lines=["1. e4"],
        exclude_lines=["c5 2. Nf3 d6 3. d4"],
    )

    assert len(findings) == 1
    assert findings[0].move.fen == "caro"
