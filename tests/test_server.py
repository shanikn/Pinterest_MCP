import asyncio

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from pinterest_mcp.server import mcp

TOOLS = {"list_boards", "list_board_pins", "get_pin", "search_my_pins", "whoami"}


def call_tool(name, args):
    return asyncio.run(mcp.call_tool(name, args))


def test_all_tools_registered_and_read_only():
    tools = asyncio.run(mcp.list_tools())
    assert {t.name for t in tools} == TOOLS
    for t in tools:
        assert t.annotations.read_only_hint, t.name
        assert len(t.description) > 50, f"{t.name} needs a real description for Claude"


def test_tool_returns_trimmed_result(api):
    api.get("/boards").mock(return_value=httpx.Response(200, json={"items": [], "bookmark": None}))
    result = call_tool("list_boards", {})
    assert "boards" in str(result)


# mcp hides the message of unexpected exceptions; these errors must reach Claude as text


def test_pinterest_error_message_reaches_claude(api):
    api.get("/pins/1").mock(return_value=httpx.Response(404, json={"code": 50, "message": "Pin not found."}))
    with pytest.raises(ToolError, match="Pin not found"):
        call_tool("get_pin", {"pin_id": "1"})


def test_login_error_message_reaches_claude():
    with pytest.raises(ToolError, match="pinterest-mcp-login"):
        call_tool("whoami", {})


def test_bad_input_message_reaches_claude(api):
    with pytest.raises(ToolError, match="between 1 and 250"):
        call_tool("list_boards", {"page_size": 1000})


def test_network_error_message_reaches_claude(api):
    api.get("/user_account").mock(side_effect=httpx.ConnectError("connection refused"))
    with pytest.raises(ToolError, match="Could not reach Pinterest"):
        call_tool("whoami", {})
