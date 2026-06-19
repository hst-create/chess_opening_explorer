from __future__ import annotations

from lichess_opening_analyzer.explorer import _explorer_error_message, _explorer_headers


def test_explorer_headers_include_explicit_bearer_token(monkeypatch) -> None:
    monkeypatch.delenv("LICHESS_TOKEN", raising=False)

    headers = _explorer_headers("lip_test")

    assert headers["Authorization"] == "Bearer lip_test"


def test_explorer_headers_use_environment_token(monkeypatch) -> None:
    monkeypatch.setenv("LICHESS_TOKEN", "lip_env")

    headers = _explorer_headers()

    assert headers["Authorization"] == "Bearer lip_env"


def test_explorer_headers_omit_auth_without_token(monkeypatch) -> None:
    monkeypatch.delenv("LICHESS_TOKEN", raising=False)

    headers = _explorer_headers()

    assert "Authorization" not in headers


def test_explorer_auth_error_mentions_token_options() -> None:
    message = _explorer_error_message(401)

    assert "HTTP 401" in message
    assert "--lichess-token" in message
    assert "LICHESS_TOKEN" in message
