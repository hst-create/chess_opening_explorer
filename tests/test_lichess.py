from __future__ import annotations

from lichess_opening_analyzer.lichess import _download_error_message, _lichess_headers


def test_lichess_headers_include_explicit_bearer_token(monkeypatch) -> None:
    monkeypatch.delenv("LICHESS_TOKEN", raising=False)

    headers = _lichess_headers("lip_test")

    assert headers["Authorization"] == "Bearer lip_test"


def test_lichess_headers_use_environment_token(monkeypatch) -> None:
    monkeypatch.setenv("LICHESS_TOKEN", "lip_env")

    headers = _lichess_headers()

    assert headers["Authorization"] == "Bearer lip_env"


def test_auth_error_mentions_token_options() -> None:
    message = _download_error_message(403, "unleesh")

    assert "HTTP 403" in message
    assert "--lichess-token" in message
    assert "LICHESS_TOKEN" in message
