from functools import wraps

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from pinterest_mcp import account, boards, pins
from pinterest_mcp.auth import AuthError
from pinterest_mcp.client import PinterestError

mcp = MCPServer(
    "pinterest",
    instructions=("Read-only access to the user's own Pinterest account: their boards, the Pins saved in them, "
    "and search over their Pins. Nothing can be created, changed or deleted. The app's API access is limited to "
    "1000 requests a day, so fetch more pages (with bookmark) only when the user needs them."),
)

READ_ONLY = ToolAnnotations(read_only_hint=True)


def tool(fn):
    """Register a read-only tool. Expected failures (Pinterest errors such as a missing Pin or the daily
    limit, a missing or expired login, bad input, network problems) become ToolError, whose message Claude sees;
    mcp hides the text of any other exception and reports only "Error executing tool"."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (PinterestError, AuthError, ValueError) as exc:
            raise ToolError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ToolError(f"Could not reach Pinterest: {exc}") from exc
    return mcp.tool(annotations=READ_ONLY)(wrapper)


@tool
def list_boards(page_size: int = 25, bookmark: str | None = None) -> dict:
    """List the user's Pinterest boards, one page at a time.

    Returns {"boards": [...], "bookmark": str | null}. Each board has: id (used by
    list_board_pins), name, description (null if empty), pin_count, privacy ("PUBLIC",
    "PROTECTED" or "SECRET"), created_at and cover_image_url (null if the board has no cover).

    page_size: 1-250 boards per page (default 25).
    bookmark: null for the first page; to get the next page, call again with the bookmark
    from the previous result. A null bookmark in the result means there are no more pages.
    Each page is one API request out of a daily limit of 1000, so only fetch further pages
    when needed.
    """
    return boards.list_boards(page_size, bookmark)


@tool
def list_board_pins(board_id: str, page_size: int = 25, bookmark: str | None = None) -> dict:
    """List the Pins saved in one board, one page at a time. board_id comes from list_boards.

    Returns {"pins": [...], "bookmark": str | null}, each Pin in the same format as get_pin.

    page_size: 1-250 Pins per page (default 25).
    bookmark: null for the first page; pass the previous result's bookmark for the next one.
    A null bookmark means there are no more pages. Each page is one API request out of a
    daily limit of 1000.
    """
    return pins.list_board_pins(board_id, page_size, bookmark)


@tool
def get_pin(pin_id: str) -> dict:
    """The details of one Pin. pin_id comes from list_board_pins or search_my_pins.

    Returns: id, title, description, link (the web page the Pin points to), alt_text,
    board_id, board_section_id, created_at, media_type (e.g. "image", "video") and
    image_url (a 600px wide image, or another size if that one is missing). Any text field
    and image_url can be null.
    """
    return pins.get_pin(pin_id)


@tool
def search_my_pins(query: str, bookmark: str | None = None) -> dict:
    """Search the user's own saved Pins (not all of Pinterest) by keyword, e.g. "lemon cake".

    Returns {"pins": [...], "bookmark": str | null}, each Pin in the same format as get_pin.
    Matches Pin text such as title and description; Pins in secret boards are included.
    bookmark: null for the first page; pass the previous result's bookmark for more results.
    Each page is one API request out of a daily limit of 1000.
    """
    return pins.search_my_pins(query, bookmark)


@tool
def whoami() -> dict:
    """The Pinterest account this server is logged in as.

    Returns: id, username, account_type (e.g. "PINNER" or "BUSINESS"), business_name,
    website_url, profile_image (url), board_count, pin_count, follower_count and
    following_count. Fields Pinterest does not return for this account are null.
    Useful to check that the login works.
    """
    return account.whoami()


def main() -> None:
    """Run over stdio, for the Claude desktop app / Claude Code."""
    mcp.run()
