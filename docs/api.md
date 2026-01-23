# API Reference

This page provides detailed API documentation for the UniFi Release Announcer codebase.

## Core Modules

### main.py

The main Discord bot application that orchestrates the release checking and announcement process.

#### Functions

##### `format_release_message(release: Release) -> str`

Formats a release object into a Discord message string.

**Parameters:**
- `release` (Release): The release object to format

**Returns:**
- `str`: Formatted message string with emojis and markdown

**Example:**
```python
release = Release(
    title="UniFi Protect iOS 2.13.1",
    url="https://community.ui.com/releases/...",
    tag="unifi-protect"
)
message = format_release_message(release)
# Returns: "🎉 **New UniFi Release Posted**\n\n🔗 [UniFi Protect iOS 2.13.1](...) 📱"
```

##### `async process_new_release(latest_release: Release, state_manager: StateManager) -> None`

Processes a new release by sending a Discord notification and updating state.

**Parameters:**
- `latest_release` (Release): The release to announce
- `state_manager` (StateManager): State manager instance for tracking announced releases

**Raises:**
- `discord.Forbidden`: If bot lacks permissions
- `discord.HTTPException`: If Discord API request fails

**Example:**
```python
state_manager = StateManager("/cache/release_state.json")
await process_new_release(release, state_manager)
```

##### `async check_for_updates() -> None`

Background task that periodically checks for new releases. Runs every 10 minutes by default.

**Decorator:**
- `@tasks.loop(minutes=10)`: Configures the check interval

**Example:**
```python
# Customize interval
@tasks.loop(minutes=5)  # Check every 5 minutes
async def check_for_updates() -> None:
    # ...
```

#### Events

##### `async on_ready() -> None`

Discord event handler called when the bot successfully logs in.

**Behavior:**
- Logs bot username and ID
- Starts the `check_for_updates` background task

---

### scraper_interface.py

Provides the interface for scraping UniFi releases.

#### Classes

##### `Release`

Dataclass representing a UniFi release.

**Attributes:**
- `title` (str): Release title (e.g., "UniFi Protect iOS 2.13.1")
- `url` (str): URL to the release announcement
- `tag` (str): Product tag (e.g., "unifi-protect")

**Example:**
```python
from scraper_interface import Release

release = Release(
    title="UniFi Protect iOS 2.13.1",
    url="https://community.ui.com/releases/UniFi-Protect-iOS-2-13-1/...",
    tag="unifi-protect"
)
```

#### Functions

##### `async get_latest_release() -> Release | None`

Fetches the latest release using the GraphQL backend.

**Returns:**
- `Release | None`: Release object if found, None if error occurs

**Example:**
```python
release = await get_latest_release()
if release:
    print(f"Latest: {release.title}")
```

##### `async get_latest_releases() -> list[Release]`

Fetches the latest releases for all configured tags.

**Returns:**
- `list[Release]`: List of Release objects, one per configured tag

**Example:**
```python
releases = await get_latest_releases()
for release in releases:
    print(f"{release.tag}: {release.title}")
```

---

### state_manager.py

Manages persistent state for tracking announced releases.

#### Classes

##### `StateManager`

Handles reading and writing release state to a JSON file.

**Constructor:**
```python
StateManager(state_file: str)
```

**Parameters:**
- `state_file` (str): Path to the JSON state file

**Methods:**

###### `has_seen_url(tag: str, url: str) -> bool`

Checks if a URL has been previously announced for a given tag.

**Parameters:**
- `tag` (str): Product tag (e.g., "unifi-protect")
- `url` (str): Release URL to check

**Returns:**
- `bool`: True if URL has been seen, False otherwise

**Example:**
```python
state_manager = StateManager("/cache/release_state.json")
if not state_manager.has_seen_url("unifi-protect", release_url):
    # This is a new release
    await announce_release(release)
```

###### `set_last_url(tag: str, url: str) -> None`

Stores the last announced URL for a given tag.

**Parameters:**
- `tag` (str): Product tag
- `url` (str): Release URL to store

**Example:**
```python
state_manager.set_last_url("unifi-protect", release.url)
```

###### `_load_state() -> dict[str, str]`

Private method that loads state from the JSON file.

**Returns:**
- `dict[str, str]`: Dictionary mapping tags to URLs

###### `_save_state(state: dict[str, str]) -> None`

Private method that saves state to the JSON file.

**Parameters:**
- `state` (dict[str, str]): State dictionary to save

---

### scraper_backends/graphql_backend.py

GraphQL-based backend for fetching UniFi releases.

#### Classes

##### `GraphQLBackend`

Scraper implementation using the Ubiquiti Community GraphQL API.

**Constructor:**
```python
GraphQLBackend()
```

**Attributes:**
- `tags` (list[str]): List of product tags to monitor (from TAGS env var)
- `api_url` (str): GraphQL API endpoint

**Methods:**

###### `async get_latest_release() -> Release | None`

Fetches the latest release for the first configured tag.

**Returns:**
- `Release | None`: Latest release or None if not found

**Example:**
```python
backend = GraphQLBackend()
release = await backend.get_latest_release()
```

###### `async get_latest_releases() -> list[dict]`

Fetches the latest releases for all configured tags.

**Returns:**
- `list[dict]`: List of release dictionaries with keys: title, url, tag

**Example:**
```python
backend = GraphQLBackend()
releases = await backend.get_latest_releases()
for release in releases:
    print(f"{release['tag']}: {release['title']}")
```

###### `async _fetch_releases_for_tag(tag: str) -> dict | None`

Private method that fetches releases for a specific tag.

**Parameters:**
- `tag` (str): Product tag to fetch

**Returns:**
- `dict | None`: Release dictionary or None if not found

---

### scraper_backends/rss_backend.py

RSS-based backend for fetching UniFi releases (legacy).

#### Classes

##### `RSSBackend`

Scraper implementation using the Ubiquiti Community RSS feed.

**Constructor:**
```python
RSSBackend()
```

**Methods:**

###### `async get_latest_release() -> Release | None`

Fetches the latest release from the RSS feed.

**Returns:**
- `Release | None`: Latest release or None if error occurs

**Note:** The RSS backend does not support tag filtering and returns the absolute latest release regardless of product.

---

### release_parser.py

Utilities for parsing release data.

#### Functions

##### `parse_release_title(title: str) -> dict[str, str]`

Parses a release title into components.

**Parameters:**
- `title` (str): Release title to parse

**Returns:**
- `dict[str, str]`: Dictionary with keys: product, version, platform

**Example:**
```python
from release_parser import parse_release_title

result = parse_release_title("UniFi Protect iOS 2.13.1")
# Returns: {
#     "product": "UniFi Protect",
#     "platform": "iOS",
#     "version": "2.13.1"
# }
```

---

## Environment Variables

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `DISCORD_BOT_TOKEN` | string | Discord bot authentication token |
| `DISCORD_CHANNEL_ID` | string | Discord channel ID (numeric) |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SCRAPER_BACKEND` | string | `"graphql"` | Backend to use: `graphql` or `rss` |
| `TAGS` | string | `"unifi-protect"` | Comma-separated list of product tags |

---

## Data Structures

### State File Format

The state file (`/cache/release_state.json`) uses the following format:

```json
{
  "unifi-protect": "https://community.ui.com/releases/UniFi-Protect-iOS-2-13-1/...",
  "unifi-network": "https://community.ui.com/releases/UniFi-Network-8-0-7/...",
  "unifi-access": "https://community.ui.com/releases/UniFi-Access-1-2-3/..."
}
```

**Structure:**
- Keys: Product tags (string)
- Values: Last announced release URL (string)

---

## Error Handling

### Common Exceptions

#### `discord.Forbidden`

Raised when the bot lacks permissions to perform an action.

**Handling:**
```python
try:
    await channel.send(message)
except discord.Forbidden:
    logging.error("Bot lacks permissions in channel")
```

#### `discord.HTTPException`

Raised when a Discord API request fails.

**Handling:**
```python
try:
    await channel.send(message)
except discord.HTTPException as e:
    logging.error(f"Discord API error: {e}")
```

#### `ValueError`

Raised when environment variables have invalid values.

**Handling:**
```python
try:
    channel_id = int(DISCORD_CHANNEL_ID)
except ValueError:
    logging.error("Invalid DISCORD_CHANNEL_ID")
    sys.exit(1)
```

---

## Testing

### Test Utilities

#### Mock Release Creation

```python
from scraper_interface import Release

def create_test_release(
    title: str = "Test Release",
    url: str = "https://example.com",
    tag: str = "unifi-protect"
) -> Release:
    """Create a test release object."""
    return Release(title=title, url=url, tag=tag)
```

#### Mock State Manager

```python
from unittest.mock import Mock

def create_mock_state_manager():
    """Create a mock state manager for testing."""
    mock = Mock(spec=StateManager)
    mock.has_seen_url.return_value = False
    mock.set_last_url.return_value = None
    return mock
```

---

## Type Hints

The codebase uses Python type hints for better IDE support and type checking.

### Common Types

```python
from typing import Optional, List, Dict

# Release object
Release: dataclass

# State dictionary
StateDict = Dict[str, str]

# Release list
ReleaseList = List[Release]

# Optional release
OptionalRelease = Optional[Release]
```

---

## Logging

### Log Levels

The application uses Python's standard logging module with the following levels:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for non-critical issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors that prevent startup

### Log Format

```
%(asctime)s - %(levelname)s - %(message)s
```

**Example output:**
```
2025-11-24 10:00:00 - INFO - Checking for new UniFi releases...
2025-11-24 10:00:01 - INFO - New release found: UniFi Protect iOS 2.13.1 (tag: unifi-protect)
2025-11-24 10:00:02 - INFO - Posted to text channel: releases
```

### Configuring Log Level

```python
import logging

# Set to DEBUG for verbose output
logging.basicConfig(level=logging.DEBUG)

# Set to WARNING to reduce noise
logging.basicConfig(level=logging.WARNING)
```
