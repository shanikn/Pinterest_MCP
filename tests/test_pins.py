import httpx
import pytest

from pinterest_mcp.pins import get_pin, list_board_pins, search_my_pins

PIN = {
    "id": "813744226420795884", "title": "Lemon cake", "description": "Easy recipe",
    "link": "https://example.com/cake", "alt_text": None, "board_id": "549755885175",
    "board_section_id": None, "created_at": "2025-05-01T08:30:00", "dominant_color": "#f5e050",
    "board_owner": {"username": "shani"}, "is_owner": True,
    "media": {"media_type": "image", "images": {
        "150x150": {"width": 150, "height": 150, "url": "https://i.pinimg.com/150.jpg"},
        "600x": {"width": 600, "height": 900, "url": "https://i.pinimg.com/600.jpg"},
    }},
}
TRIMMED = {
    "id": "813744226420795884", "title": "Lemon cake", "description": "Easy recipe",
    "link": "https://example.com/cake", "alt_text": None, "board_id": "549755885175",
    "board_section_id": None, "created_at": "2025-05-01T08:30:00",
    "media_type": "image", "image_url": "https://i.pinimg.com/600.jpg",
}


def test_list_board_pins(api):
    route = api.get("/boards/549755885175/pins").mock(
        return_value=httpx.Response(200, json={"items": [PIN], "bookmark": "next"}))
    assert list_board_pins("549755885175", page_size=10, bookmark="b1") == {"pins": [TRIMMED], "bookmark": "next"}
    assert dict(route.calls.last.request.url.params) == {"page_size": "10", "bookmark": "b1"}


def test_list_board_pins_checks_page_size(api):
    with pytest.raises(ValueError, match="between 1 and 250"):
        list_board_pins("1", page_size=500)


def test_get_pin(api):
    api.get("/pins/813744226420795884").mock(return_value=httpx.Response(200, json=PIN))
    assert get_pin("813744226420795884") == TRIMMED


def test_pin_with_null_text_and_video_media(api):
    video = {"id": "7", "title": None, "description": "", "link": None, "alt_text": None,
             "media": {"media_type": "video", "images": None}}
    api.get("/pins/7").mock(return_value=httpx.Response(200, json=video))
    pin = get_pin("7")
    assert (pin["title"], pin["description"], pin["media_type"], pin["image_url"]) == (None, None, "video", None)


def test_image_url_falls_back_to_other_sizes(api):
    pin = {**PIN, "media": {"media_type": "image", "images": {"150x150": {"url": "https://i.pinimg.com/150.jpg"}}}}
    api.get("/pins/1").mock(return_value=httpx.Response(200, json=pin))
    assert get_pin("1")["image_url"] == "https://i.pinimg.com/150.jpg"


def test_ids_cannot_escape_the_path(api):
    route = api.get("/pins/1%2F..%2Fuser_account").mock(return_value=httpx.Response(200, json={**PIN, "id": "1"}))
    get_pin("1/../user_account")
    assert route.called


def test_empty_id_rejected(api):
    with pytest.raises(ValueError, match="pin_id is required"):
        get_pin("")


def test_search_my_pins(api):
    route = api.get("/search/pins").mock(return_value=httpx.Response(200, json={"items": [PIN], "bookmark": None}))
    assert search_my_pins("lemon cake") == {"pins": [TRIMMED], "bookmark": None}
    assert dict(route.calls.last.request.url.params) == {"query": "lemon cake"}


def test_search_needs_a_query(api):
    with pytest.raises(ValueError, match="query must not be empty"):
        search_my_pins("  ")
    assert not api.calls
