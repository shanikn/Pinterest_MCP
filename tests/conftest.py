"""Shared test setup: fake app credentials and a token file in tmp_path.

config.py reads the environment when it is imported, so the env vars are set here,
before any pinterest_mcp module is imported, and the real .env is never loaded.
"""
import json
import os
import time

import dotenv
import pytest
import respx

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


@pytest.fixture
def api(token_file, monkeypatch):
    """A logged-in user and a mocked Pinterest API: api.get("/boards").mock(...).

    Any request that is not mocked fails the test instead of reaching the network."""
    from pinterest_mcp import client

    now = time.time()
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(json.dumps({
        "access_token": "access-1", "refresh_token": "refresh-1",
        "expires_at": now + 3600, "refresh_expires_at": now + 86400, "scope": "",
    }))
    monkeypatch.setattr(client.time, "sleep", lambda seconds: None)
    with respx.mock(base_url=config.API_BASE) as router:
        yield router
