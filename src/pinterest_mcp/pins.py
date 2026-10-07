# the logic for reading the user's Pins: one board's Pins, a single Pin, and search
from urllib.parse import quote

from pinterest_mcp.client import call
from pinterest_mcp.paging import check_page_size

# preferred image first; "600x" is big enough to look at without being a huge download
IMAGE_SIZES = ["600x", "1200x", "400x300", "150x150"]


def _image_url(media: dict) -> str | None:
    images = media.get("images") or {}
    for size in IMAGE_SIZES:
        if url := (images.get(size) or {}).get("url"):
            return url
    return None


def _pin(p: dict) -> dict:
    media = p.get("media") or {}
    return {
        "id": p["id"],
        "title": p.get("title") or None,
        "description": p.get("description") or None,
        "link": p.get("link"),
        "alt_text": p.get("alt_text"),
        "board_id": p.get("board_id"),
        "board_section_id": p.get("board_section_id"),
        "created_at": p.get("created_at"),
        "media_type": media.get("media_type"),
        "image_url": _image_url(media),
    }


def _segment(value: str, name: str) -> str:
    """An id for a URL path; quoted so that e.g. "1/../.." cannot reach another endpoint."""
    if not value:
        raise ValueError(f"{name} is required.")
    return quote(value, safe="")


def _page(page: dict) -> dict:
    return {"pins": [_pin(p) for p in page["items"]], "bookmark": page.get("bookmark")}


def list_board_pins(board_id: str, page_size: int = 25, bookmark: str | None = None) -> dict:
    path = f"/boards/{_segment(board_id, 'board_id')}/pins"
    return _page(call("GET", path, page_size=check_page_size(page_size), bookmark=bookmark))


def get_pin(pin_id: str) -> dict:
    return _pin(call("GET", f"/pins/{_segment(pin_id, 'pin_id')}"))


def search_my_pins(query: str, bookmark: str | None = None) -> dict:
    if not query.strip():
        raise ValueError("query must not be empty.")
    return _page(call("GET", "/search/pins", query=query, bookmark=bookmark))
