from __future__ import annotations

from pathlib import Path
from typing import Iterable, TextIO

import chess.pgn

from .models import MoveAggregate, MoveOccurrence


def iter_occurrences(
    pgn_file: TextIO,
    username: str,
    color: str = "both",
    max_fullmove: int = 12,
) -> Iterable[MoveOccurrence]:
    """Yield moves made by username through max_fullmove from a PGN stream."""
    wanted = username.casefold()
    while True:
        game = chess.pgn.read_game(pgn_file)
        if game is None:
            break
        white = (game.headers.get("White") or "").casefold()
        black = (game.headers.get("Black") or "").casefold()
        if wanted == white:
            player_color = "white"
        elif wanted == black:
            player_color = "black"
        else:
            continue
        if color != "both" and player_color != color:
            continue

        board = game.board()
        played_moves: list[chess.Move] = []
        for move in game.mainline_moves():
            if board.fullmove_number > max_fullmove:
                break
            mover_color = "white" if board.turn == chess.WHITE else "black"
            san = board.san(move)
            fen = board.fen()
            if mover_color == player_color:
                yield MoveOccurrence(
                    fen=fen,
                    move_uci=move.uci(),
                    move_san=san,
                    line_san=game.board().variation_san([*played_moves, move]),
                    ply=board.ply() + 1,
                    color=player_color,
                )
            board.push(move)
            played_moves.append(move)


def aggregate_occurrences(occurrences: Iterable[MoveOccurrence]) -> dict[tuple[str, str], MoveAggregate]:
    aggregates: dict[tuple[str, str], MoveAggregate] = {}
    for occ in occurrences:
        key = (occ.fen, occ.move_uci)
        if key not in aggregates:
            aggregates[key] = MoveAggregate(occ.fen, occ.move_uci, occ.move_san, occ.color, line_san=occ.line_san)
        aggregates[key].add(occ)
    return aggregates


def aggregate_pgn(path: Path, username: str, color: str, max_fullmove: int) -> dict[tuple[str, str], MoveAggregate]:
    with path.open(encoding="utf-8") as handle:
        return aggregate_occurrences(iter_occurrences(handle, username, color, max_fullmove))
