import json
import time
from urllib.parse import urlencode

import httpx

from pinterest_mcp import config


def save_tokens(response: dict) -> None:
    """Store Pinterest's token response, converting lifetimes to absolute expiry times"""
    now = time.time()
    tokens = {
        "access_token": response["access_token"],
        "refresh_token": response["refresh_token"],
        "expires_at": now + response["expires_in"],
        "refresh_expires_at": now + response["refresh_token_expires_in"],
        "scope": response.get("scope", ""),
    }
    config.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.TOKEN_FILE.write_text(json.dumps(tokens, indent=2))


def load_tokens() -> dict | None:
    if not config.TOKEN_FILE.exists():
        return None
    return json.loads(config.TOKEN_FILE.read_text())


def build_auth_url(state: str) -> str:
    params = {
        "client_id": config.APP_ID,
        "redirect_uri": config.REDIRECT_URI,
        "response_type": "code",
        "scope": ",".join(config.SCOPES),
        "state": state,
    }
    query = urlencode(params)
    return f"{config.AUTH_URL}?{query}"


def _request_tokens(fields: dict) -> dict:
    """POST to Pinterest's token endpoint, save the tokens it returns, and return them."""
    response = httpx.post(
        config.TOKEN_URL,
        data=fields,
        auth=(config.APP_ID, config.APP_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    save_tokens(response.json())
    return load_tokens()


def exchange_code(code: str) -> dict:
    """First login: trade the code from the redirect for tokens."""
    return _request_tokens({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.REDIRECT_URI,
    })


def refresh(refresh_token: str) -> dict:
    """Renewal: trade the refresh token for a new access token."""
    return _request_tokens({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })