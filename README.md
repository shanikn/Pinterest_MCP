# Pinterest_MCP

A personal [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that lets an AI assistant read my own Pinterest boards and Pins.

## What it does

The server exposes a small set of read-only tools to an MCP client such as Claude:

| Tool | Description |
|---|---|
| `list_boards(page_size, bookmark)` | Lists the boards of the authenticated account, one page at a time |
| `list_board_pins(board_id, page_size, bookmark)` | Lists the Pins saved in one board, one page at a time |
| `get_pin(pin_id)` | Returns the details of a single Pin |
| `search_my_pins(query, bookmark)` | Searches the authenticated account's own Pins by keyword |
| `whoami()` | Shows which Pinterest account the server is logged in as |

Lists return one page and a `bookmark`; pass it back to get the next page. The server never pages through everything on its own, because trial API access is limited to 1000 requests a day.

With these, I can ask my assistant things like "what did I save in my living-room board?" or "find the recipe Pins I saved last month".

## How it works

- It uses the official Pinterest API v5 and runs locally over stdio.
- Access is granted through Pinterest's standard OAuth 2.0 flow. The account owner approves the requested read scopes on Pinterest's own consent screen.
- The server only reads data from the account that authorized it. It does not post, follow, message, or act on behalf of anyone else.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and a Pinterest app from the [Pinterest developer portal](https://developers.pinterest.com/apps/).

1. In the app's settings, add the redirect URI `http://localhost:8085/callback`.
2. Copy `.env.example` to `.env` and fill in the app id and secret:

   ```
   PINTEREST_APP_ID=...
   PINTEREST_APP_SECRET=...
   PINTEREST_REDIRECT_URI=
   ```

   Leave `PINTEREST_REDIRECT_URI` empty to use `http://localhost:8085/callback`, or set it to another local URI that is also registered in the app.
3. Install the dependencies:

   ```
   uv sync
   ```

### Log in

```
uv run pinterest-mcp-login
```

This opens Pinterest's consent screen in the browser and asks for `boards:read`, `pins:read`, `user_accounts:read`, `boards:read_secret` and `pins:read_secret` (the last two are required by Pinterest's Pin search). After you approve, Pinterest redirects to the local URI, where a one-shot server catches the reply and saves the tokens to `.state/tokens.json` (git-ignored). The server refreshes the access token on its own; run the login again only when it tells you to.

### Use it in Claude Desktop

Add this to `claude_desktop_config.json` under `mcpServers`, adjusting the paths:

```json
"pinterest": {
  "command": "C:\\Users\\Shani\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\uv.exe",
  "args": [
    "run",
    "--directory",
    "C:\\Users\\Shani\\Projects\\Pinterest_MCP",
    "pinterest-mcp"
  ],
  "env": {}
}
```

Then restart Claude Desktop.

### Tests

```
uv run pytest
```

The tests mock the Pinterest API with [respx](https://lundberg.github.io/respx/) and never touch the network or the real token file.

## Status

Work in progress. This is a hobby project for single-user, personal use.

## Privacy

See [PRIVACY.md](PRIVACY.md).

## Author

Shani Knobel ([@shanikn](https://github.com/shanikn))

This project is not affiliated with or endorsed by Pinterest.