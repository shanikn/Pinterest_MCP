# the logic for the logged-in Pinterest account
from pinterest_mcp.client import call

# copied when present; Pinterest leaves some out depending on the account type
FIELDS = ["id", "username", "account_type", "business_name", "website_url", "profile_image",
          "board_count", "pin_count", "follower_count", "following_count"]


def whoami() -> dict:
    account = call("GET", "/user_account")
    return {field: account.get(field) for field in FIELDS}
