# the logic for listing the user's boards
from pinterest_mcp.client import call
from pinterest_mcp.paging import check_page_size


def _board(b: dict) -> dict:
    return {
        "id": b["id"],
        "name": b.get("name"),
        "description": b.get("description") or None,
        "pin_count": b.get("pin_count"),
        "privacy": b.get("privacy"),
        "created_at": b.get("created_at"),
        "cover_image_url": (b.get("media") or {}).get("image_cover_url"),
    }


def list_boards(page_size: int = 25, bookmark: str | None = None) -> dict:
    """One page of the user's boards; pass the returned bookmark back for the next page."""
    page = call("GET", "/boards", page_size=check_page_size(page_size), bookmark=bookmark)
    return {"boards": [_board(b) for b in page["items"]], "bookmark": page.get("bookmark")}
