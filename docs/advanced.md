# Advanced Usage

This guide covers advanced usage scenarios and customization options for the UniFi Release Announcer.

## Custom Check Intervals

By default, the bot checks for new releases every 10 minutes. You can customize this interval by modifying the `@tasks.loop` decorator in `main.py`:

```python
# Default: Check every 10 minutes
@tasks.loop(minutes=10)
async def check_for_updates() -> None:
    """Periodically checks for new releases and posts them."""
    # ...

# Custom: Check every 5 minutes
@tasks.loop(minutes=5)
async def check_for_updates() -> None:
    """Periodically checks for new releases and posts them."""
    # ...

# Custom: Check every hour
@tasks.loop(hours=1)
async def check_for_updates() -> None:
    """Periodically checks for new releases and posts them."""
    # ...
```

!!! warning "Rate Limiting"
    Be mindful of rate limits when setting shorter intervals. The Ubiquiti Community API may throttle requests if you check too frequently.

## Multiple Discord Channels

To post announcements to multiple Discord channels, you can modify the bot to support multiple channel IDs.

### Option 1: Multiple Bot Instances

Run separate instances of the bot with different configurations:

```yaml
# docker-compose.yml
services:
  announcer-protect:
    build: .
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - DISCORD_CHANNEL_ID=${PROTECT_CHANNEL_ID}
      - TAGS=unifi-protect
    volumes:
      - ./cache/protect:/cache

  announcer-network:
    build: .
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - DISCORD_CHANNEL_ID=${NETWORK_CHANNEL_ID}
      - TAGS=unifi-network
    volumes:
      - ./cache/network:/cache
```

### Option 2: Modify Code for Multiple Channels

Modify `main.py` to support comma-separated channel IDs:

```python
# Get multiple channel IDs
DISCORD_CHANNEL_IDS = os.getenv("DISCORD_CHANNEL_IDS", "").split(",")

# In process_new_release function
for channel_id_str in DISCORD_CHANNEL_IDS:
    try:
        channel_id = int(channel_id_str.strip())
        channel = client.get_channel(channel_id)
        if channel:
            await channel.send(message)
    except ValueError:
        logging.error(f"Invalid channel ID: {channel_id_str}")
```

## Custom Message Formatting

You can customize the Discord message format by modifying the `format_release_message` function in `main.py`:

### Default Format

```python
def format_release_message(release: Release) -> str:
    """Formats the release information into a Discord message."""
    title = release.title
    url = release.url

    platform_emoji = "🔧"  # Default emoji
    if "ios" in title.lower():
        platform_emoji = "📱"
    elif "android" in title.lower():
        platform_emoji = "🤖"
    elif "desktop" in title.lower() or "application" in title.lower():
        platform_emoji = "💻"

    return f"🎉 **New UniFi Release Posted**\\n\\n🔗 [{title}]({url}) {platform_emoji}"
```

### Custom Format Examples

#### Minimal Format

```python
def format_release_message(release: Release) -> str:
    """Minimal message format."""
    return f"[{release.title}]({release.url})"
```

#### Rich Embed Format

```python
async def post_release_embed(channel, release: Release):
    """Post release as a rich embed."""
    embed = discord.Embed(
        title=release.title,
        url=release.url,
        description="A new UniFi release has been posted!",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Tag: {release.tag}")
    embed.timestamp = discord.utils.utcnow()
    
    await channel.send(embed=embed)
```

#### With Mentions

```python
def format_release_message(release: Release) -> str:
    """Format with role mention."""
    role_id = "YOUR_ROLE_ID"  # Replace with actual role ID
    return f"<@&{role_id}> 🎉 **New UniFi Release**\\n\\n🔗 [{release.title}]({release.url})"
```

## Forum Channel Support

The bot supports posting to Discord Forum channels. When posting to a forum channel, it creates a new thread for each release:

```python
if isinstance(channel, discord.ForumChannel):
    thread = await channel.create_thread(
        name=f"UniFi Release: {latest_release.title}",
        content=message
    )
    logging.info("Posted to forum thread: %s", thread.thread.name)
```

To use forum channels:

1. Create a forum channel in your Discord server
2. Get the forum channel ID
3. Set `DISCORD_CHANNEL_ID` to the forum channel ID

## Custom Tag Filtering Logic

The bot filters releases based on tags. You can customize the filtering logic in `scraper_backends/graphql_backend.py`:

### Current Implementation

```python
# Get tags from environment or use default
tags_env = os.getenv("TAGS", "unifi-protect")
self.tags = [tag.strip() for tag in tags_env.split(",")]
```

### Custom Filter Examples

#### Filter by Version Pattern

```python
def should_announce_release(release: Release) -> bool:
    """Only announce stable releases (not beta/RC)."""
    title_lower = release.title.lower()
    if "beta" in title_lower or "rc" in title_lower:
        return False
    return True
```

#### Filter by Date

```python
from datetime import datetime, timedelta

def should_announce_release(release: Release, max_age_days: int = 7) -> bool:
    """Only announce releases from the last N days."""
    # Assuming release has a published_date field
    if hasattr(release, 'published_date'):
        age = datetime.now() - release.published_date
        return age.days <= max_age_days
    return True
```

## State Management

The bot uses a JSON file to track announced releases. The state is stored in `/cache/release_state.json`:

```json
{
  "unifi-protect": "https://community.ui.com/releases/...",
  "unifi-network": "https://community.ui.com/releases/..."
}
```

### Resetting State

To force the bot to re-announce the latest release:

```bash
# Docker
docker compose exec announcer rm /cache/release_state.json

# Kubernetes
kubectl exec <pod-name> -- rm /cache/release_state.json

# Local
rm cache/release_state.json
```

### Custom State Storage

You can modify `state_manager.py` to use a different storage backend:

#### Redis Example

```python
import redis
import json

class RedisStateManager:
    """State manager using Redis."""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def has_seen_url(self, tag: str, url: str) -> bool:
        """Check if URL has been seen for this tag."""
        stored_url = self.redis.get(f"release:{tag}")
        return stored_url and stored_url.decode() == url
    
    def set_last_url(self, tag: str, url: str) -> None:
        """Store the last URL for this tag."""
        self.redis.set(f"release:{tag}", url)
```

## Webhook Integration

Instead of using a Discord bot, you can use webhooks for simpler deployment:

```python
import requests

def post_to_webhook(webhook_url: str, release: Release):
    """Post release to Discord webhook."""
    data = {
        "content": format_release_message(release),
        "username": "UniFi Release Announcer"
    }
    
    response = requests.post(webhook_url, json=data)
    response.raise_for_status()
```

Update your `.env`:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Monitoring and Alerts

### Health Checks

Add a health check endpoint for monitoring:

```python
from aiohttp import web

async def health_check(request):
    """Health check endpoint."""
    return web.Response(text="OK")

# Add to your bot
async def start_health_server():
    """Start health check server."""
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
```

### Prometheus Metrics

Add Prometheus metrics for monitoring:

```python
from prometheus_client import Counter, Gauge, start_http_server

# Metrics
releases_announced = Counter('releases_announced_total', 'Total releases announced')
last_check_time = Gauge('last_check_timestamp', 'Timestamp of last check')
check_errors = Counter('check_errors_total', 'Total check errors')

# In your code
releases_announced.inc()
last_check_time.set_to_current_time()

# Start metrics server
start_http_server(9090)
```

## Testing Locally

### Test with Mock Data

Create a test script to verify message formatting without posting to Discord:

```python
# test_message.py
from scraper_interface import Release
from main import format_release_message

# Create test release
test_release = Release(
    title="UniFi Protect iOS 2.13.1",
    url="https://community.ui.com/releases/test",
    tag="unifi-protect"
)

# Print formatted message
print(format_release_message(test_release))
```

Run with:
```bash
uv run python test_message.py
```

### Test Scraper Backends

Test each backend independently:

```bash
# Test GraphQL backend
uv run python -c "
import asyncio
from scraper_backends.graphql_backend import GraphQLBackend

async def test():
    backend = GraphQLBackend()
    releases = await backend.get_latest_releases()
    for release in releases:
        print(f'{release[\"tag\"]}: {release[\"title\"]}')

asyncio.run(test())
"
```

## Performance Optimization

### Caching Responses

Add caching to reduce API calls:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedBackend:
    """Backend with response caching."""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
    
    async def get_latest_releases(self):
        """Get releases with caching."""
        now = datetime.now()
        
        if 'releases' in self.cache:
            cached_time, cached_data = self.cache['releases']
            if now - cached_time < self.cache_duration:
                return cached_data
        
        # Fetch fresh data
        releases = await self._fetch_releases()
        self.cache['releases'] = (now, releases)
        return releases
```

### Async Optimization

Process multiple tags concurrently:

```python
import asyncio

async def get_all_releases(tags: list[str]) -> list[Release]:
    """Fetch releases for all tags concurrently."""
    tasks = [get_release_for_tag(tag) for tag in tags]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    releases = []
    for result in results:
        if isinstance(result, Release):
            releases.append(result)
        elif isinstance(result, Exception):
            logging.error(f"Error fetching release: {result}")
    
    return releases
```

## Security Best Practices

### Environment Variable Validation

Add validation for sensitive configuration:

```python
import re

def validate_discord_token(token: str) -> bool:
    """Validate Discord token format."""
    # Discord tokens are typically base64 encoded
    pattern = r'^[A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27}$'
    return bool(re.match(pattern, token))

def validate_channel_id(channel_id: str) -> bool:
    """Validate Discord channel ID."""
    return channel_id.isdigit() and len(channel_id) >= 17
```

### Secrets Management

Use Docker secrets or Kubernetes secrets instead of environment variables:

```yaml
# docker-compose.yml with secrets
services:
  announcer:
    build: .
    secrets:
      - discord_token
      - discord_channel_id

secrets:
  discord_token:
    file: ./secrets/discord_token.txt
  discord_channel_id:
    file: ./secrets/discord_channel_id.txt
```

```python
# Read from secrets
def read_secret(secret_name: str) -> str:
    """Read secret from Docker/Kubernetes secrets."""
    secret_path = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return os.getenv(secret_name.upper(), "")
```
