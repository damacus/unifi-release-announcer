# Configuration

| Variable | Requirement | Default |
| --- | --- | --- |
| `DISCORD_BOT_TOKEN` | Required bot token | None |
| `DISCORD_CHANNEL_ID` | Required positive numeric channel ID | None |
| `TAGS` | Comma-separated allowed product tags | `unifi-protect` |

Tag names are case-sensitive. Spaces and empty entries are removed; repeated tags are deduplicated. An invalid tag or a list containing only commas fails startup.

Production monitors `unifi-drive,unifi-network,unifi-protect`. Compose defaults to Protect and Network when TAGS is omitted; direct execution defaults to Protect.

The GraphQL backend is the only backend. `SCRAPER_BACKEND` is not used and there is no RSS implementation.

Grant the bot permission to view the channel, read message history and send messages. Forum targets also require permission to create posts and read relevant threads. Keep credentials in the existing Kubernetes Secret or a private local environment file.

The poll interval is ten minutes. GraphQL requests have a 30-second timeout. Discord history loading has a 120-second overall bound; each HTTP request has a 30-second timeout. Posting has a 30-second overall bound.

The bot can appear offline because no Gateway connection is maintained.
