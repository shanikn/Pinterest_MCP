import base64
from urllib.parse import parse_qsl

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
