from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

import requests

from .models import ExplorerMove


class ExplorerCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS explorer_cache (cache_key TEXT PRIMARY KEY, response TEXT NOT NULL, created_at INTEGER NOT NULL)"
        )

    def get(self, key: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT response FROM explorer_cache WHERE cache_key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def set(self, key: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            "REPLACE INTO explorer_cache(cache_key, response, created_at) VALUES (?, ?, ?)",
            (key, json.dumps(payload), int(time.time())),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


class LichessExplorerClient:
    BASE_URL = "https://explorer.lichess.ovh/lichess"

    def __init__(
        self,
        cache: ExplorerCache,
        speeds: list[str],
        ratings: list[int],
        top_games: int = 0,
        recent_games: int = 0,
        timeout: int = 20,
    ) -> None:
        self.cache = cache
        self.speeds = speeds
        self.ratings = ratings
        self.top_games = top_games
        self.recent_games = recent_games
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "lichess-opening-analyzer/0.1"})

    def get_position(self, fen: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "fen": fen,
            "speeds": ",".join(self.speeds),
            "ratings": ",".join(str(r) for r in self.ratings),
            "topGames": self.top_games,
            "recentGames": self.recent_games,
        }
        key = self._cache_key(params)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        response = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        self.cache.set(key, payload)
        return payload

    @staticmethod
    def moves(payload: dict[str, Any]) -> list[ExplorerMove]:
        return [ExplorerMove.from_api(move) for move in payload.get("moves", [])]

    @staticmethod
    def _cache_key(params: dict[str, Any]) -> str:
        encoded = json.dumps(params, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()
