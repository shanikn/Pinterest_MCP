import json
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlencode, urlsplit

import httpx

from pinterest_mcp import config


def save_tokens(response: dict) -> None:
    """Store Pinterest's token response, converting lifetimes to absolute expiry times.

    A refresh reply may leave out refresh_token; then the old refresh token and its expiry are kept."""
    now = time.time()
    tokens = {
        "access_token": response["access_token"],
        "expires_at": now + response["expires_in"],
        "scope": response.get("scope", ""),
    }
    if "refresh_token" in response:
        tokens["refresh_token"] = response["refresh_token"]
        tokens["refresh_expires_at"] = now + response["refresh_token_expires_in"]
    else:
        old = load_tokens() or {}
        tokens["refresh_token"] = old.get("refresh_token")
        tokens["refresh_expires_at"] = old.get("refresh_expires_at", 0)
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


REFRESH_MARGIN = 60  # seconds: refresh an access token this close to expiry instead of risking a 401
LOGIN_HINT = "Run `uv run pinterest-mcp-login` in the Pinterest_MCP folder to log in again."


class AuthError(Exception):
    """There is no usable Pinterest login; the user has to run pinterest-mcp-login."""


def get_access_token() -> str:
    """A valid access token, refreshing it first if it expires within REFRESH_MARGIN seconds."""
    tokens = load_tokens()
    if tokens is None:
        raise AuthError(f"Not logged in to Pinterest. {LOGIN_HINT}")
    now = time.time()
    if tokens["expires_at"] - now > REFRESH_MARGIN:
        return tokens["access_token"]
    if not tokens.get("refresh_token") or tokens["refresh_expires_at"] <= now:
        raise AuthError(f"The Pinterest login has expired. {LOGIN_HINT}")
    try:
        return refresh(tokens["refresh_token"])["access_token"]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code >= 500:
            raise
        # e.g. the user revoked the app's access on Pinterest
        raise AuthError(f"Pinterest refused the saved login ({exc.response.status_code}). {LOGIN_HINT}") from exc


LOGIN_TIMEOUT = 300  # seconds to wait for the browser to come back from Pinterest


class _CallbackServer(HTTPServer):
    """One-shot server for Pinterest's redirect: query holds the redirect's parameters once it arrives."""

    def __init__(self, address: tuple[str, int], callback_path: str):
        super().__init__(address, _CallbackHandler)
        self.callback_path = callback_path
        self.query: dict | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    """Catches Pinterest's redirect and stores its query on the server. Other paths (e.g. /favicon.ico) get 404."""

    server: _CallbackServer

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path != self.server.callback_path:
            self.send_error(404)
            return
        self.server.query = dict(parse_qsl(url.query))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<p>Pinterest login received. You can close this tab and go back to the terminal.</p>")

    def log_message(self, format, *args):
        pass  # keep the terminal quiet


def login() -> None:
    """Console script (pinterest-mcp-login): approve the app in the browser and save the tokens.

    Runs a one-shot local server on the host and port of REDIRECT_URI to catch Pinterest's redirect."""
    if not config.APP_ID or not config.APP_SECRET:
        raise SystemExit("PINTEREST_APP_ID and PINTEREST_APP_SECRET must be set in .env (see .env.example).")
    state = secrets.token_urlsafe(32)
    redirect = urlsplit(config.REDIRECT_URI)
    with _CallbackServer((redirect.hostname or "localhost", redirect.port or 80), redirect.path or "/") as server:
        server.timeout = 1  # so the deadline below is checked even when nothing arrives
        url = build_auth_url(state)
        print(f"Opening Pinterest in your browser. If it does not open, go to:\n{url}")
        webbrowser.open(url)
        deadline = time.monotonic() + LOGIN_TIMEOUT
        while server.query is None and time.monotonic() < deadline:
            server.handle_request()
    query = server.query
    if query is None:
        raise SystemExit("No reply from Pinterest within 5 minutes. Run pinterest-mcp-login again.")
    if not secrets.compare_digest(query.get("state", ""), state):
        raise SystemExit("The reply's state does not match this login, so it was ignored. Run pinterest-mcp-login again.")
    if "code" not in query:
        raise SystemExit(f"Pinterest did not grant access: {query.get('error', 'no code in the reply')}")
    try:
        exchange_code(query["code"])
    except httpx.HTTPStatusError as exc:
        raise SystemExit(f"Pinterest refused the login ({exc.response.status_code}): {exc.response.text}") from exc
    print(f"Logged in. Tokens saved to {config.TOKEN_FILE}")
