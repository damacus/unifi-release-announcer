# UniFi Release Announcer

A Discord bot that monitors UniFi community releases and posts announcements to a Discord channel.

## Features

- **Modular Scraper Architecture**: Swappable backends for different scraping needs
- **GraphQL API**: Direct API access for reliable data fetching
- **Docker Ready**: Optimized Alpine-based container (157MB)
- **Environment Configuration**: Easy backend switching via environment variables
- 🔍 **Automatic Monitoring**: Checks for new UniFi releases every 10 minutes
- 📱 **Platform Detection**: Automatically tags releases with platform-specific emojis (iOS 📱, Android 🤖, Desktop 💻)
- 🎯 **Smart Filtering**: Only posts new releases, avoiding duplicates
- ☸️ **Kubernetes Support**: Ready for deployment on k3s/Kubernetes clusters

## Prerequisites

- Python 3.13
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
   uv sync --extra dev
   ```

3. **Configure environment variables**:

   Create a `.env` file in the project root:

   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_discord_channel_id
   SCRAPER_BACKEND=graphql  # or 'rss' if you prefer
   ```

4. **Run the application**:

   ```bash
   uv run main.py
   ```

### Docker Development

1. **Build the Docker image**:

   ```bash
   docker compose build
   ```

2. **Run the container**:

   ```bash
   docker compose run announcer
   ```

### Dev Container (Recommended for Development)

For the best development experience, use the provided dev container configuration:

1. **Prerequisites**:
   - VS Code with the Dev Containers extension
   - Docker Desktop

2. **Open in Dev Container**:
   - Open the project in VS Code
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Select "Dev Containers: Reopen in Container"
   - Wait for the container to build and start

3. **Features included**:
   - Pre-configured Python environment with all dependencies
   - GraphQL API support
   - Python extensions (Black, Ruff, MyPy, Pytest)
   - Volume mounts for live code editing
   - Automatic dependency installation

### Kubernetes Deployment

See the [k8s/README.md](k8s/README.md) for detailed Kubernetes deployment instructions.

## Configuration

### Environment Variables

| Variable             | Description                                                                                                 | Required |
|----------------------|-------------------------------------------------------------------------------------------------------------|----------|
| `DISCORD_BOT_TOKEN`  | Your Discord bot token                                                                                      | Yes      |
| `DISCORD_CHANNEL_ID` | Discord channel ID for announcements                                                                        | Yes      |
| `SCRAPER_BACKEND`    | Backend to use for scraping: `graphql` (default) or `rss`                                                  | No       |
| `TAGS`               | Comma-separated list of UniFi product tags to monitor (e.g., "unifi-protect,unifi-network"). Defaults to "unifi-protect" if not set. See [Available Tags](#available-tags) below. | No       |

### Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token
5. Invite the bot to your server with "Send Messages" permission
6. Get your channel ID by right-clicking on the channel and selecting "Copy ID"

### Available Tags

The following tags are available for filtering UniFi releases:

**UniFi Products:**
- `unifi` - General UniFi releases
- `unifi-access` - UniFi Access (door access control)
- `unifi-cloud-gateway` - UniFi Cloud Gateway
- `unifi-connect` - UniFi Connect
- `unifi-design-center` - UniFi Design Center
- `unifi-drive` - UniFi Drive (storage)
- `unifi-gateway-cloudkey` - UniFi Gateway and Cloud Key
- `unifi-led` - UniFi LED
- `unifi-mobility` - UniFi Mobility
- `unifi-network` - UniFi Network (switches, routers)
- `unifi-play` - UniFi Play
- `unifi-portal` - UniFi Portal
- `unifi-protect` - UniFi Protect (security cameras) - **Default**
- `unifi-routing-switching` - UniFi Routing and Switching
- `unifi-switching` - UniFi Switching
- `unifi-talk` - UniFi Talk (VoIP)
- `unifi-video` - UniFi Video (legacy)
- `unifi-voip` - UniFi VoIP
- `unifi-wireless` - UniFi Wireless (access points)

**Other Ubiquiti Products:**
- `60GHz` - 60GHz wireless products
- `aircontrol` - AirControl software
- `airfiber` - AirFiber products
- `airfiber-ltu` - AirFiber LTU
- `airmax` - AirMax products
- `airmax-aircube` - AirMax AirCube
- `amplifi` - AmpliFi consumer routers
- `edgemax` - EdgeMax routers
- `edgeswitch` - EdgeSwitch products
- `gigabeam` - GigaBeam products
- `innerspace` - InnerSpace location services
- `isp` - ISP solutions
- `isp-design-center` - ISP Design Center
- `ufiber` - UFiber products
- `uid` - UID products
- `uisp-app` - UISP application
- `uisp-power` - UISP Power management
- `unms` - UNMS (legacy)
- `wave` - Wave products
- `wifiman` - WiFiman application

**General Categories:**
- `community-feedback` - Community feedback
- `general` - General announcements
- `routing` - Routing products
- `security` - Security products
- `site-manager` - Site management
- `solar` - Solar products
- `switching` - Switching products

**Examples:**
```bash
# Monitor only UniFi Protect releases (default)
TAGS="unifi-protect"

# Monitor UniFi Protect and Network releases
TAGS="unifi-protect,unifi-network"

# Monitor all UniFi products
TAGS="unifi,unifi-protect,unifi-network,unifi-access,unifi-talk"

# Monitor EdgeMax and AmpliFi products
TAGS="edgemax,amplifi"
```

## How It Works

1. **Scraping**: The bot scrapes the Ubiquiti Community forums for the latest UniFi releases
2. **Comparison**: It compares the latest release URL with the previously posted one (stored in `releases.json`)
3. **Posting**: If a new release is found, it formats a message with platform tags and posts to Discord
4. **State Management**: Updates the stored URL to prevent duplicate posts (stored in `releases.json`)

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
├── main.py                     # Main Discord bot application
├── scraper_interface.py        # Scraper backend interface and factory
├── scraper_backends/           # Scraper backend implementations
│   ├── graphql_backend.py
│   └── rss_backend.py
├── test_scraper_interface.py   # Unit tests for the scraper interface
├── test_integration.py         # Integration tests
├── pyproject.toml              # Project dependencies
├── Dockerfile                  # Container configuration
├── k8s/                        # Kubernetes manifests
│   ├── deployment.yaml
│   ├── secret.yaml
│   ├── kustomization.yaml
│   └── README.md
└── README.md                   # This file
```

### Running Tests

```bash
uv run python -m pytest test_scraper_interface.py -v
uv run python -m pytest test_integration.py -v
```

## Troubleshooting

### Common Issues

1. **Bot not posting**: Check that the bot has "Send Messages" permission in the target channel
2. **Environment variables**: Ensure both `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` are set
3. **Channel ID format**: The channel ID must be a valid number (Discord snowflake)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License
