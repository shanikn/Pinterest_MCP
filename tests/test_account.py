import httpx

from pinterest_mcp.account import whoami


def test_whoami_trims_account(api):
    api.get("/user_account").mock(return_value=httpx.Response(200, json={
        "username": "shani", "account_type": "PINNER", "profile_image": "https://i.pinimg.com/me.jpg",
        "website_url": None, "board_count": 12, "pin_count": 340, "follower_count": 5,
        "following_count": 20, "monthly_views": 100, "about": "hi",
    }))
    assert whoami() == {
        "id": None, "username": "shani", "account_type": "PINNER", "business_name": None, "website_url": None,
        "profile_image": "https://i.pinimg.com/me.jpg", "board_count": 12, "pin_count": 340,
        "follower_count": 5, "following_count": 20,
    }
