from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import requests


def download_games(username: str, output: Path, max_games: int | None = None, since: str | None = None, until: str | None = None) -> None:
    params: dict[str, str | int | bool] = {"pgnInJson": False, "clocks": False, "evals": False, "opening": True}
    if max_games:
        params["max"] = max_games
    if since:
        params["since"] = _date_to_millis(since)
    if until:
        params["until"] = _date_to_millis(until)
    headers = {"Accept": "application/x-chess-pgn", "User-Agent": "lichess-opening-analyzer/0.1"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(f"https://lichess.org/api/games/user/{username}", params=params, headers=headers, stream=True, timeout=60) as response:
        response.raise_for_status()
        with output.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)


def _date_to_millis(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)
