# UniFi Release Announcer

A Discord bot that monitors UniFi community releases and posts announcements to a Discord channel.

## Features

- **Modular Scraper Architecture**: Swappable backends for different scraping needs
- **JavaScript Support**: Handles modern React SPAs with Playwright
- **Lightweight Options**: httpx + BeautifulSoup for static content
- **Legacy Support**: Selenium backend for compatibility
- **Docker Ready**: Optimized container with Playwright dependencies
- **Environment Configuration**: Easy backend switching via environment variables
- 🔍 **Automatic Monitoring**: Checks for new UniFi releases every 10 minutes
- 📱 **Platform Detection**: Automatically tags releases with platform-specific emojis (iOS 📱, Android 🤖, Desktop 💻)
- 🎯 **Smart Filtering**: Only posts new releases, avoiding duplicates
- 🐳 **Docker Ready**: Containerized for easy deployment
- ☸️ **Kubernetes Support**: Ready for deployment on k3s/Kubernetes clusters

## Prerequisites

- Python 3.11+
- Discord Bot Token
- Discord Channel ID where announcements will be posted

## Installation

### Local Development

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd unifi-release-announcer
   ```

2. **Install dependencies using uv**:

   ```bash
   uv sync
   ```

3. **Set environment variables**:

   ```bash
   export DISCORD_BOT_TOKEN="your_bot_token_here"
   export DISCORD_CHANNEL_ID="your_channel_id_here"
   # Optional: Filter for specific releases (e.g., Protect, Network)
   # export RELEASE_KEYWORDS="Protect,Network"
   ```

4. **Run the application**:

   ```bash
   uv run main.py
   ```

### Docker Deployment

1. **Build the Docker image**:

   ```bash
   docker build -t unifi-release-announcer .
   ```

2. **Run the container**:

   ```bash
   docker run -e DISCORD_BOT_TOKEN="your_token" \
              -e DISCORD_CHANNEL_ID="your_channel_id" \
              -e RELEASE_KEYWORDS="Protect,Network" \
              unifi-release-announcer
   ```

### Kubernetes Deployment

See the [k8s/README.md](k8s/README.md) for detailed Kubernetes deployment instructions.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_BOT_TOKEN`  | Your Discord bot token                                                                                       | Yes      |
| `DISCORD_CHANNEL_ID` | Discord channel ID for announcements                                                                         | Yes      |
| `RELEASE_KEYWORDS`   | Comma-separated list of keywords to filter releases (e.g., "Protect,Network"). Defaults to "UniFi Protect". | No       |

### Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token
5. Invite the bot to your server with "Send Messages" permission
6. Get your channel ID by right-clicking on the channel and selecting "Copy ID"

## How It Works

1. **Scraping**: The bot scrapes the Ubiquiti Community forums for the latest UniFi releases
2. **Comparison**: It compares the latest release URL with the previously posted one (stored in `last_release_url.txt`)
3. **Posting**: If a new release is found, it formats a message with platform tags and posts to Discord
4. **State Management**: Updates the stored URL to prevent duplicate posts

## Message Format

The bot posts messages in this format:

```markdown
🎉 **New UniFi Release Posted**

🔗 [UniFi Protect iOS 2.13.1](https://community.ui.com/releases/...) 📱
```

Platform tags:

- 📱 for iOS releases
- 🤖 for Android releases
- 💻 for Desktop/Application releases
- 🔧 UniFi for other releases

## Development

### Project Structure

```markdown
├── main.py              # Main Discord bot application
├── scraper.py           # Web scraping logic
├── test_scraper.py      # Unit tests
├── pyproject.toml       # Project dependencies
├── Dockerfile           # Container configuration
├── k8s/                 # Kubernetes manifests
│   ├── deployment.yaml
│   ├── secret.yaml
│   ├── kustomization.yaml
│   └── README.md
└── README.md           # This file
```

### Running Tests

```bash
uv run python -m pytest test_scraper.py -v
```

## Troubleshooting

### Common Issues

1. **Bot not posting**: Check that the bot has "Send Messages" permission in the target channel
2. **Environment variables**: Ensure both `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` are set
3. **Channel ID format**: The channel ID must be a valid number (Discord snowflake)

### Logs

The application provides detailed logging:

- Connection status
- Release checking activity
- Error messages with context
- Successful post confirmations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License
