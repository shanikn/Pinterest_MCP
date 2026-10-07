import json
import time

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