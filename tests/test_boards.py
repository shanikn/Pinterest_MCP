import httpx
import pytest

from pinterest_mcp.boards import list_boards

BOARD = {
    "id": "549755885175", "name": "Living room", "description": "Cosy ideas",
    "pin_count": 42, "privacy": "PUBLIC", "created_at": "2024-03-01T10:00:00",
    "owner": {"username": "shani"}, "follower_count": 3, "collaborator_count": 0,
    "media": {"image_cover_url": "https://i.pinimg.com/cover.jpg", "pin_thumbnail_urls": ["a", "b"]},
}


def test_list_boards_trims_and_returns_bookmark(api):
    route = api.get("/boards").mock(return_value=httpx.Response(200, json={"items": [BOARD], "bookmark": "next"}))
    assert list_boards() == {"boards": [{
        "id": "549755885175", "name": "Living room", "description": "Cosy ideas", "pin_count": 42,
        "privacy": "PUBLIC", "created_at": "2024-03-01T10:00:00", "cover_image_url": "https://i.pinimg.com/cover.jpg",
    }], "bookmark": "next"}
    assert dict(route.calls.last.request.url.params) == {"page_size": "25"}


def test_list_boards_passes_bookmark_and_handles_missing_fields(api):
    route = api.get("/boards").mock(return_value=httpx.Response(200, json={
        "items": [{"id": "1", "name": "Bare", "description": None, "media": None}], "bookmark": None}))
    result = list_boards(page_size=250, bookmark="abc")
    assert result["bookmark"] is None
    assert result["boards"][0]["cover_image_url"] is None
    assert result["boards"][0]["description"] is None
    assert dict(route.calls.last.request.url.params) == {"page_size": "250", "bookmark": "abc"}


@pytest.mark.parametrize("page_size", [0, 251])
def test_page_size_out_of_range(api, page_size):
    with pytest.raises(ValueError, match="between 1 and 250"):
        list_boards(page_size=page_size)
    assert not api.calls
