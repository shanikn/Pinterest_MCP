import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

APP_ID = os.environ.get("PINTEREST_APP_ID", default="")
APP_SECRET = os.environ.get("PINTEREST_APP_SECRET", default="")
REDIRECT_URI = os.environ.get("PINTEREST_REDIRECT_URI", default="http://localhost:8085/callback")
SCOPES = ["boards:read", "pins:read", "user_accounts:read"]
API_BASE = "https://api.pinterest.com/v5"
AUTH_URL = "https://www.pinterest.com/oauth/"
TOKEN_URL = API_BASE + "/oauth/token"
TOKEN_FILE = Path(__file__).resolve().parents[2]/".state"/"tokens.json"
