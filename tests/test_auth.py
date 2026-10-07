import base64
import socket
import threading
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlsplit

import httpx
import pytest
import respx

from pinterest_mcp import auth, config

TOKEN_REPLY = {
    "access_token": "access-1",
    "refresh_token": "refresh-1",
    "expires_in": 2592000,
    "refresh_token_expires_in": 31536000,
    "scope": "boards:read,pins:read",
}


@pytest.fixture
def token_endpoint():
    with respx.mock as router:
        yield router.post(config.TOKEN_URL)


def sent_form(route) -> dict:
    return dict(parse_qsl(route.calls.last.request.content.decode()))


def test_exchange_code_saves_tokens(token_endpoint, token_file):
    token_endpoint.mock(return_value=httpx.Response(200, json=TOKEN_REPLY))
    tokens = auth.exchange_code("the-code")
    assert tokens["access_token"] == "access-1"
    assert tokens["refresh_token"] == "refresh-1"
    assert token_file.exists()
    assert sent_form(token_endpoint) == {
        "grant_type": "authorization_code",
        "code": "the-code",
        "redirect_uri": "http://localhost:8085/callback",
    }
    # HTTP Basic auth with the app id and secret
    expected = base64.b64encode(b"app-id:app-SECRET").decode()
    assert token_endpoint.calls.last.request.headers["authorization"] == f"Basic {expected}"


def test_refresh_sends_refresh_token(token_endpoint):
    token_endpoint.mock(return_value=httpx.Response(200, json={**TOKEN_REPLY, "access_token": "access-2"}))
    tokens = auth.refresh("refresh-1")
    assert tokens["access_token"] == "access-2"
    assert sent_form(token_endpoint) == {"grant_type": "refresh_token", "refresh_token": "refresh-1"}


def test_error_reply_saves_nothing(token_endpoint, token_file):
    token_endpoint.mock(return_value=httpx.Response(401, json={"code": 2, "message": "Authentication failed."}))
    with pytest.raises(httpx.HTTPStatusError):
        auth.exchange_code("bad-code")
    assert not token_file.exists()


def test_refresh_without_new_refresh_token_keeps_the_old_one(token_endpoint):
    token_endpoint.mock(return_value=httpx.Response(200, json=TOKEN_REPLY))
    first = auth.exchange_code("the-code")
    reply = {"access_token": "access-2", "expires_in": 2592000, "scope": "boards:read,pins:read"}
    token_endpoint.mock(return_value=httpx.Response(200, json=reply))
    tokens = auth.refresh("refresh-1")
    assert tokens["access_token"] == "access-2"
    assert tokens["refresh_token"] == "refresh-1"
    assert tokens["refresh_expires_at"] == first["refresh_expires_at"]


# --- login flow: a fake browser follows the auth URL back to the local server ---


@pytest.fixture
def redirect_uri(monkeypatch):
    """A free local port, so the test never clashes with a real login on 8085."""
    with socket.socket() as s:
        s.bind(("localhost", 0))
        port = s.getsockname()[1]
    uri = f"http://localhost:{port}/callback"
    monkeypatch.setattr(config, "REDIRECT_URI", uri)
    return uri


def fake_browser(monkeypatch, reply):
    """webbrowser.open stand-in: GETs the redirect URI with the query reply(auth_params) builds."""
    opened = []

    def visit(url):
        params = dict(parse_qsl(urlsplit(url).query))
        opened.append(params)
        # 127.0.0.1, not localhost: on Windows a refused ::1 attempt first costs ~2 s per request
        base = params["redirect_uri"].replace("localhost", "127.0.0.1")

        def go():
            for path in (base.replace("/callback", "/favicon.ico"), f"{base}?{urlencode(reply(params))}"):
                try:
                    urllib.request.urlopen(path, timeout=5).read()
                except urllib.error.HTTPError:
                    pass  # the favicon 404
        threading.Thread(target=go, daemon=True).start()
        return True

    monkeypatch.setattr(auth.webbrowser, "open", visit)
    return opened


def test_login_saves_tokens(token_endpoint, token_file, redirect_uri, monkeypatch):
    token_endpoint.mock(return_value=httpx.Response(200, json=TOKEN_REPLY))
    opened = fake_browser(monkeypatch, lambda p: {"code": "the-code", "state": p["state"]})
    auth.login()
    assert opened[0]["redirect_uri"] == redirect_uri
    assert sent_form(token_endpoint)["code"] == "the-code"
    assert auth.load_tokens()["access_token"] == "access-1"


def test_login_rejects_wrong_state(token_endpoint, token_file, redirect_uri, monkeypatch):
    fake_browser(monkeypatch, lambda p: {"code": "the-code", "state": "forged"})
    with pytest.raises(SystemExit, match="state does not match"):
        auth.login()
    assert not token_endpoint.called
    assert not token_file.exists()


def test_login_reports_denied_access(token_endpoint, redirect_uri, monkeypatch):
    fake_browser(monkeypatch, lambda p: {"error": "access_denied", "state": p["state"]})
    with pytest.raises(SystemExit, match="access_denied"):
        auth.login()
    assert not token_endpoint.called


@pytest.mark.parametrize("field", ["APP_ID", "APP_SECRET"])
def test_login_needs_app_credentials(field, monkeypatch):
    monkeypatch.setattr(config, field, "")
    monkeypatch.setattr(auth.webbrowser, "open", lambda url: pytest.fail("must not open the browser"))
    with pytest.raises(SystemExit, match="PINTEREST_APP_ID and PINTEREST_APP_SECRET"):
        auth.login()
