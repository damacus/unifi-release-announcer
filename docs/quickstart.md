# Quick start

Create a private `.env` file:

```text
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id
TAGS=unifi-drive,unifi-network,unifi-protect
```

Keep this file out of Git. Run a read-only poll first:

```sh
docker compose build announcer
docker compose run --rm announcer --once --dry-run
```

Check the output decisions, then start normal polling:

```sh
docker compose up -d announcer
docker compose logs announcer
```

Do not run a second production writer alongside the existing bot. No cache reset is needed; Discord history carries restart compatibility.

A forum target creates a post with a starter message. A text target receives a message.
