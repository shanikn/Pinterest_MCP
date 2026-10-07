# sends a request to the Pinterest API and returns the JSON
import logging
import time
from typing import Any

import httpx

from pinterest_mcp import auth, config

# httpx logs every request at INFO; keep the MCP server output quiet
logging.getLogger("httpx").setLevel(logging.WARNING)

# one shared client: reuses the connection and SSL setup instead of rebuilding them per request
_http = httpx.Client(timeout=30)


class PinterestError(Exception):
    """Pinterest answered with an error status; the message comes from its {"code", "message"} body."""


def _error(response: httpx.Response) -> PinterestError:
    try:
        body = response.json()
        detail = f"{body['message']} (code {body['code']})"
    except (ValueError, KeyError, TypeError):
        detail = response.text[:200] or response.reason_phrase
    return PinterestError(f"Pinterest error {response.status_code}: {detail}")


def call(method: str, path: str, **params) -> Any:  # parsed JSON
    """One request to the API, e.g. call("GET", "/boards", page_size=25). Params that are None are left out."""
    url = config.API_BASE + path
    headers = {"Authorization": f"Bearer {auth.get_access_token()}"}
    params = {key: value for key, value in params.items() if value is not None}
    response = _http.request(method, url, params=params, headers=headers)
    if response.status_code >= 500:
        # a passing server error; one retry usually works
        time.sleep(1)
        response = _http.request(method, url, params=params, headers=headers)
    if response.is_error:
        raise _error(response)
    return response.json()
