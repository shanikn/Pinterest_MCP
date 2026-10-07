# Pinterest_MCP

A personal [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that lets an AI assistant read my own Pinterest boards and Pins.

## What it does

The server exposes a small set of read-only tools to an MCP client such as Claude:

| Tool | Description |
|---|---|
| `list_boards` | Lists the boards of the authenticated account |
| `list_board_pins` | Lists the Pins saved in one board |
| `get_pin` | Returns the details of a single Pin |
| `search_my_pins` | Searches the authenticated account's own Pins by keyword |

With these, I can ask my assistant things like "what did I save in my living-room board?" or "find the recipe Pins I saved last month".

## How it works

- It uses the official Pinterest API v5.
- Access is granted through Pinterest's standard OAuth 2.0 flow. The account owner approves the requested read scopes on Pinterest's own consent screen.
- The server only reads data from the account that authorized it. It does not post, follow, message, or act on behalf of anyone else.

## Status

Work in progress. This is a hobby project for single-user, personal use.

## Privacy

See [PRIVACY.md](PRIVACY.md).

## Author

Shani Knobel ([@shanikn](https://github.com/shanikn))

This project is not affiliated with or endorsed by Pinterest.