# Configuration

## Environment Variables

| Variable             | Description                                                                                                 | Required |
|----------------------|-------------------------------------------------------------------------------------------------------------|----------|
| `DISCORD_BOT_TOKEN`  | Your Discord bot token                                                                                      | Yes      |
| `DISCORD_CHANNEL_ID` | Discord channel ID for announcements                                                                        | Yes      |
| `SCRAPER_BACKEND`    | Backend to use for scraping: `graphql` (default) or `rss`                                                  | No       |
| `TAGS`               | Comma-separated list of UniFi product tags to monitor (e.g., "unifi-protect,unifi-network"). Defaults to "unifi-protect" if not set. See [Available Tags](#available-tags) below. | No       |

## Automatic Filtering

The release announcer automatically filters out certain types of releases to focus on main application updates:

**Filtered Release Types:**
- Mobile applications (Android, iOS, iPhone, iPad)
- Hardware-specific tools (SFP Wizard)
- Peripheral devices (UPS firmware)

This ensures you only receive notifications for core application releases (e.g., UniFi Network Application, UniFi Protect Application) and not for mobile app updates or hardware accessories.


## Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token
5. Invite the bot to your server with "Send Messages" permission
6. Get your channel ID by right-clicking on the channel and selecting "Copy ID"

## Available Tags

The following tags are available for filtering UniFi releases:

### UniFi Products

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

### Other Ubiquiti Products

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

### General Categories

- `community-feedback` - Community feedback
- `general` - General announcements
- `routing` - Routing products
- `security` - Security products
- `site-manager` - Site management
- `solar` - Solar products
- `switching` - Switching products

### Examples

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
