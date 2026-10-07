import httpx
import pytest

from pinterest_mcp.client import PinterestError, call


def test_sends_bearer_token_and_params(api):
    route = api.get("/boards").mock(return_value=httpx.Response(200, json={"items": [], "bookmark": None}))
    assert call("GET", "/boards", page_size=25, bookmark=None) == {"items": [], "bookmark": None}
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer access-1"
    assert dict(request.url.params) == {"page_size": "25"}  # None is left out


def test_retries_once_on_server_error(api):
    route = api.get("/user_account").mock(side_effect=[
        httpx.Response(503, text="Service Unavailable"),
        httpx.Response(200, json={"username": "shani"}),
    ])
    assert call("GET", "/user_account") == {"username": "shani"}
    assert route.call_count == 2


def test_second_server_error_raises(api):
    route = api.get("/user_account").mock(return_value=httpx.Response(500, json={"code": 0, "message": "Oops"}))
    with pytest.raises(PinterestError, match="500: Oops"):
        call("GET", "/user_account")
    assert route.call_count == 2


def test_client_error_uses_pinterest_message_without_retry(api):
    route = api.get("/pins/1").mock(return_value=httpx.Response(404, json={"code": 50, "message": "Pin not found."}))
    with pytest.raises(PinterestError, match=r"Pinterest error 404: Pin not found\. \(code 50\)"):
        call("GET", "/pins/1")
    assert route.call_count == 1


def test_error_without_json_body(api):
    api.get("/boards").mock(return_value=httpx.Response(429, text="Too Many Requests"))
    with pytest.raises(PinterestError, match="429: Too Many Requests"):
        call("GET", "/boards")
