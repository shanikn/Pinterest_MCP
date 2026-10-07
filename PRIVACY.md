# Privacy Policy

_Last updated: 7 October 2026_

Pinterest_MCP is a personal, single-user hobby project. It is run by its author, on the author's own computer, against the author's own Pinterest account.

## What data is accessed

After the account owner approves access on Pinterest's OAuth consent screen, the server can read from that account:

- Boards (name, description, Pin count)
- Pins saved in those boards (title, description, link, image URL)
- Basic account information needed to identify the authorized account

It reads data only from the account that authorized it. It does not access other Pinterest users' accounts.

## How the data is used

The data is returned to the author's own AI assistant, on request, so it can answer questions about the author's saved content. It is not used for advertising, profiling, or analytics.

## Storage

- OAuth access and refresh tokens are stored locally on the author's machine and are never committed to this repository.
- Board and Pin data is fetched on demand and is not kept in any database.

## Sharing

No data is sold or shared with third parties. Data fetched by a tool call is passed only to the MCP client that the author is using.

## Revoking access

Access can be revoked at any time from the Pinterest account's security settings, under connected apps. Deleting the locally stored tokens removes all credentials held by the server.

## Contact

Questions can be raised by opening an issue in this repository.