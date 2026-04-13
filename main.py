import logging
import os
import sys

import aiohttp
import discord
from discord.ext import tasks

from scraper_interface import Release, get_latest_releases

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
HISTORY_SEARCH_LIMIT = 200


# --- Bot Setup ---
class AnnouncerClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        await super().close()


intents = discord.Intents.default()
client = AnnouncerClient(intents=intents)


# --- Helper Functions ---
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

    return f"🎉 **New UniFi Release Posted**\n\n🔗 [{title}]({url}) {platform_emoji}"


async def get_announced_message_contents(
    channel: discord.TextChannel | discord.ForumChannel | discord.abc.GuildChannel,
) -> set[str]:
    """Fetches recent message contents to cache channel history efficiently."""
    contents: set[str] = set()
    try:
        if isinstance(channel, discord.ForumChannel):
            for thread in channel.threads:
                async for message in thread.history(limit=1):
                    contents.add(message.content)
            async for thread in channel.archived_threads(limit=50):
                async for message in thread.history(limit=1):
                    contents.add(message.content)
        elif hasattr(channel, "history"):
            async for message in channel.history(limit=HISTORY_SEARCH_LIMIT):
                contents.add(message.content)
        else:
            logging.warning(
                "Channel type %s does not support history(); skipping fetch.",
                type(channel).__name__,
            )
    except discord.HTTPException as e:
        logging.warning("Failed to fetch channel history: %s — treating as empty.", e)
    return contents


async def _post_to_forum(channel: discord.ForumChannel, release: Release, message: str) -> None:
    """Posts a release announcement to a forum channel."""
    thread = await channel.create_thread(name=f"UniFi Release: {release.title}", content=message)
    logging.info("Posted to forum thread: %s", thread.thread.name)


async def _post_to_text_channel(channel: discord.TextChannel, message: str) -> None:
    """Posts a release announcement to a text channel."""
    await channel.send(message)
    logging.info("Posted to text channel: %s", channel.name)


async def _post_to_generic_channel(
    channel: discord.abc.GuildChannel | discord.abc.PrivateChannel | discord.Thread, message: str
) -> bool:
    """Posts a release announcement to a generic channel with a send method."""
    logging.warning(
        "Channel type %s is not explicitly supported.",
        type(channel).__name__,
    )
    # Fallback for any other channel types that have a 'send' method
    if hasattr(channel, "send"):
        await channel.send(message)  # type: ignore[union-attr]
        logging.info(
            "Announcement posted to channel: %s",
            getattr(channel, "name", "N/A"),
        )
        return True

    logging.error(
        "Channel type %s does not support posting messages.",
        type(channel).__name__,
    )
    return False


# --- Core Logic ---


async def process_new_release(latest_release: Release) -> None:
    """Processes a new release by sending a Discord notification."""
    logging.info("New release found: %s (tag: %s)", latest_release.title, latest_release.tag)

    message = format_release_message(latest_release)

    # channel is resolved by the caller; retrieve it here for posting
    channel_id = int(DISCORD_CHANNEL_ID)  # type: ignore[arg-type]
    channel = client.get_channel(channel_id)
    if not channel:
        logging.error("Could not find channel with ID %s", DISCORD_CHANNEL_ID)
        return

    try:
        if isinstance(channel, discord.ForumChannel):
            await _post_to_forum(channel, latest_release, message)
        elif isinstance(channel, discord.TextChannel):
            await _post_to_text_channel(channel, message)
        else:
            await _post_to_generic_channel(channel, message)

    except discord.Forbidden:
        logging.error(
            "Permission error in channel %s.",
            getattr(channel, "name", channel.id),
        )
    except discord.HTTPException as e:
        logging.error("Failed to send message due to an HTTP exception: %s", e)
    except Exception as e:
        logging.error("An unexpected error occurred while posting: %s", e)


# --- Bot Events ---
@client.event
async def on_ready() -> None:
    """Called when the bot successfully logs in."""
    if client.user:
        logging.info("Logged in as %s (%s)", client.user.name, client.user.id)
    else:
        logging.info("Logged in, but user details not available yet.")
    check_for_updates.start()


# --- Background Task ---
@tasks.loop(minutes=10)
async def check_for_updates() -> None:
    """Periodically checks for new releases and posts them."""
    logging.info("Checking for new UniFi releases...")

    if not DISCORD_CHANNEL_ID:
        logging.error("DISCORD_CHANNEL_ID is not set.")
        return

    try:
        channel_id = int(DISCORD_CHANNEL_ID)
    except ValueError:
        logging.error("Invalid DISCORD_CHANNEL_ID: %s", DISCORD_CHANNEL_ID)
        return

    channel = client.get_channel(channel_id)
    if not channel:
        logging.error("Could not find channel with ID %s", DISCORD_CHANNEL_ID)
        return

    latest_releases = await get_latest_releases(session=client.session)

    if not latest_releases:
        logging.info("No releases found from scraper.")
        return

    announced_contents = await get_announced_message_contents(channel)

    new_releases_found = False
    for release in latest_releases:
        is_announced = False
        for content in announced_contents:
            if release.url in content:
                is_announced = True
                break

        if not is_announced:
            await process_new_release(release)
            new_releases_found = True

    if not new_releases_found:
        logging.info("No new releases found.")


@check_for_updates.before_loop
async def before_check() -> None:
    """Ensures the bot is ready before the task loop starts."""
    await client.wait_until_ready()


# --- Main Execution ---
if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        logging.critical(
            "Missing required environment variables: DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID must be set."
        )
        sys.exit(1)

    try:
        int(DISCORD_CHANNEL_ID)
    except ValueError:
        logging.critical("Config error: DISCORD_CHANNEL_ID must be a valid integer.")
        sys.exit(1)

    try:
        client.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logging.critical("Authentication failed: Invalid Discord Bot Token.")
        sys.exit(1)
    except Exception as e:
        logging.critical("Failed to start the bot: %s", e)
        sys.exit(1)
