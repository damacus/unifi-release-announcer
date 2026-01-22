# Quick Start Guide

Get the UniFi Release Announcer up and running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- Discord bot token ([Get one here](https://discord.com/developers/applications))
- Discord channel ID

## Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/damacus/unifi-release-announcer.git
cd unifi-release-announcer
```

### 2. Configure Environment

Create a `.env` file:

```bash
cat > .env << EOF
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
SCRAPER_BACKEND=graphql
TAGS=unifi-protect,unifi-network
EOF
```

### 3. Run with Docker Compose

```bash
docker compose up -d announcer
```

### 4. Verify It's Working

```bash
# Check logs
docker compose logs -f announcer

# You should see:
# INFO - Logged in as YourBot#1234
# INFO - Checking for new UniFi releases...
```

## Common Commands

### Using Taskfile

```bash
# Show all available tasks
task

# Install dependencies for local development
task dev-install

# Run tests
task test

# Run locally (without Docker)
task run

# Build Docker image
task build

# Run in Docker
task docker-run

# Serve documentation
task docs-serve
```

### Using Docker Compose

```bash
# Start the bot
docker compose up -d announcer

# View logs
docker compose logs -f announcer

# Stop the bot
docker compose down

# Rebuild and restart
docker compose up -d --build announcer
```

## Configuration Quick Reference

### Environment Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | `MTIzNDU2Nzg5...` | Your Discord bot token |
| `DISCORD_CHANNEL_ID` | `1234567890123456789` | Channel ID for announcements |
| `SCRAPER_BACKEND` | `graphql` | Backend: `graphql` or `rss` |
| `TAGS` | `unifi-protect,unifi-network` | Comma-separated product tags |

### Popular Tag Combinations

```bash
# UniFi Protect only (default)
TAGS=unifi-protect

# UniFi Protect and Network
TAGS=unifi-protect,unifi-network

# All major UniFi products
TAGS=unifi-protect,unifi-network,unifi-access,unifi-talk

# EdgeMax products
TAGS=edgemax

# All UniFi
TAGS=unifi
```

## Troubleshooting Quick Fixes

### Bot not posting messages?

1. **Check permissions**: Bot needs "Send Messages" permission
2. **Verify channel ID**: Right-click channel → Copy ID (enable Developer Mode first)
3. **Check logs**: `docker compose logs announcer`

### Want to re-announce the latest release?

```bash
# Delete state file
docker compose exec announcer rm /cache/release_state.json

# Or locally
rm cache/release_state.json
```

### Bot crashes on startup?

1. **Verify environment variables**:
   ```bash
   docker compose config
   ```

2. **Check token format**: Should be a long string, no quotes needed in `.env`

3. **Validate channel ID**: Should be a number, 17-19 digits

## Next Steps

- 📖 [Read the full documentation](https://damacus.github.io/unifi-release-announcer/)
- 🚀 [Deploy to Kubernetes](deployment.md#kubernetes-deployment)
- ⚙️ [Advanced configuration](advanced.md)
- 🐛 [Troubleshooting guide](troubleshooting.md)
- 🤝 [Contributing guide](contributing.md)

## Getting Help

- **Documentation**: https://damacus.github.io/unifi-release-announcer/
- **Issues**: https://github.com/damacus/unifi-release-announcer/issues
- **Discussions**: https://github.com/damacus/unifi-release-announcer/discussions

## Quick Development Setup

For contributors:

```bash
# Clone and enter directory
git clone https://github.com/damacus/unifi-release-announcer.git
cd unifi-release-announcer

# Install dependencies
task dev-install

# Run tests
task test

# Run all checks
task check

# Run locally
task run
```

---

**That's it!** Your bot should now be monitoring UniFi releases and posting to Discord. 🎉
