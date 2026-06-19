from __future__ import annotations

from io import StringIO

from lichess_opening_analyzer.pgn import aggregate_occurrences, iter_occurrences

PGN = """[Event \"Rated rapid game\"]
[Site \"https://lichess.org/test\"]
[White \"TargetUser\"]
[Black \"Opponent\"]
[Result \"1-0\"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0

[Event \"Rated rapid game\"]
[Site \"https://lichess.org/test2\"]
[White \"Opponent\"]
[Black \"TargetUser\"]
[Result \"0-1\"]

1. d4 Nf6 2. c4 e6 3. Nc3 Bb4 0-1
"""


def test_iter_occurrences_filters_by_player_color() -> None:
    moves = list(iter_occurrences(StringIO(PGN), "targetuser", color="black", max_fullmove=2))

    assert [move.move_san for move in moves] == ["Nf6", "e6"]
    assert all(move.color == "black" for move in moves)


def test_aggregate_occurrences_counts_repeated_positions() -> None:
    pgn = """[White \"TargetUser\"]
[Black \"Opponent\"]
[Result \"*\"]

1. e4 e5 2. Nf3 *

[White \"TargetUser\"]
[Black \"Opponent2\"]
[Result \"*\"]

1. e4 c5 2. Nf3 *
"""
    aggregates = aggregate_occurrences(iter_occurrences(StringIO(pgn), "TargetUser", color="white", max_fullmove=1))

    assert len(aggregates) == 1
    aggregate = next(iter(aggregates.values()))
    assert aggregate.move_san == "e4"
    assert aggregate.count == 2
