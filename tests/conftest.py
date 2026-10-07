"""Shared test setup: fake app credentials and a token file in tmp_path.

config.py reads the environment when it is imported, so the env vars are set here,
before any pinterest_mcp module is imported, and the real .env is never loaded.
"""
import os

import dotenv
import pytest

dotenv.load_dotenv = lambda *args, **kwargs: False  # keep the real app secret in .env out of tests
os.environ.update({
    "PINTEREST_APP_ID": "app-id",
    "PINTEREST_APP_SECRET": "app-SECRET",
    "PINTEREST_REDIRECT_URI": "http://localhost:8085/callback",
})

from pinterest_mcp import config  # noqa: E402  (must come after the env setup)


@pytest.fixture(autouse=True)
def token_file(tmp_path, monkeypatch):
    """Every test writes tokens to tmp_path, never to the real .state/tokens.json."""
    path = tmp_path / ".state" / "tokens.json"
    monkeypatch.setattr(config, "TOKEN_FILE", path)
    return path
