from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

TOKEN_ENV_VAR = "LICHESS_TOKEN"


def download_games(
    username: str,
    output: Path,
    max_games: int | None = None,
    since: str | None = None,
    until: str | None = None,
    token: str | None = None,
) -> None:
    params: dict[str, str | int | bool] = {"pgnInJson": False, "clocks": False, "evals": False, "opening": True}
    if max_games:
        params["max"] = max_games
    if since:
        params["since"] = _date_to_millis(since)
    if until:
        params["until"] = _date_to_millis(until)
    headers = _lichess_headers(token)
    output.parent.mkdir(parents=True, exist_ok=True)
    import requests

    with requests.get(f"https://lichess.org/api/games/user/{username}", params=params, headers=headers, stream=True, timeout=60) as response:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(_download_error_message(response.status_code, username)) from exc
        with output.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)


def _lichess_headers(token: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/x-chess-pgn", "User-Agent": "lichess-opening-analyzer/0.1"}
    resolved_token = token or os.environ.get(TOKEN_ENV_VAR)
    if resolved_token:
        headers["Authorization"] = f"Bearer {resolved_token}"
    return headers


def _download_error_message(status_code: int, username: str) -> str:
    if status_code in {401, 403}:
        return (
            f"Lichess rejected the game download for {username} with HTTP {status_code}. "
            f"If this account's games are not publicly exportable, create a Lichess personal access token "
            f"with game-read access and pass it with --lichess-token or set {TOKEN_ENV_VAR}."
        )
    return f"Lichess game download for {username} failed with HTTP {status_code}."


def _date_to_millis(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)
