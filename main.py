import logging
import os
import sys

import discord
from discord.ext import tasks

from scraper_interface import Release, get_latest_release

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
LAST_RELEASE_FILE = "last_release_url.txt"

# --- Bot Setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)


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

    return (
        f"🎉 **New UniFi Release Posted**\n\n"
        f"🔗 [{title}]({url}) {platform_emoji}"
    )


def get_last_posted_url() -> str:
    """Reads the URL of the last posted release from the state file."""
    try:
        with open(LAST_RELEASE_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def set_last_posted_url(url: str) -> None:
    """Writes the URL of the latest release to the state file."""
    with open(LAST_RELEASE_FILE, "w") as f:
        f.write(url)


# --- Core Logic ---
async def process_new_release(latest_release: Release) -> None:
    """Processes a new release by sending a Discord notification."""
    logging.info(f"New release found: {latest_release.title}")

    if not DISCORD_CHANNEL_ID:
        logging.error("DISCORD_CHANNEL_ID is not set; cannot post.")
        return

    try:
        channel_id = int(DISCORD_CHANNEL_ID)
    except ValueError:
        logging.error(f"Invalid DISCORD_CHANNEL_ID: {DISCORD_CHANNEL_ID}")
        return

    channel = client.get_channel(channel_id)
    if not channel:
        logging.error(f"Could not find channel with ID {DISCORD_CHANNEL_ID}")
        return

    message = format_release_message(latest_release)

    try:
        if isinstance(channel, discord.ForumChannel):
            thread = await channel.create_thread(
                name=f"UniFi Release: {latest_release.title}", content=message
            )
            logging.info("Posted to forum thread: %s", thread.thread.name)
        else:
            logging.warning(
                "Channel type %s is not explicitly supported.",
                type(channel).__name__,
            )
            # Fallback for any other channel types that have a 'send' method
            if hasattr(channel, "send"):
                await channel.send(message)
                logging.info(
                    "Announcement posted to channel: %s",
                    getattr(channel, "name", "N/A"),
                )
            else:
                logging.error(
                    "Channel type %s does not support posting messages.",
                    type(channel).__name__,
                )
                return  # Stop if we can't post

        set_last_posted_url(latest_release.url)

    except discord.Forbidden:
        logging.error(
            "Permission error in channel %s.",
            getattr(channel, "name", channel.id),
        )
    except discord.HTTPException as e:
        logging.error(f"Failed to send message due to an HTTP exception: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while posting: {e}")


# --- Bot Events ---
@client.event
async def on_ready() -> None:
    """Called when the bot successfully logs in."""
    if client.user:
        logging.info(f"Logged in as {client.user.name} ({client.user.id})")
    else:
        logging.info("Logged in, but user details not available yet.")
    check_for_updates.start()


# --- Background Task ---
@tasks.loop(minutes=10)
async def check_for_updates() -> None:
    """Periodically checks for new releases and posts them."""
    logging.info("Checking for new UniFi releases...")

    latest_release = await get_latest_release()
    if not latest_release:
        logging.info("No new release found or failed to fetch.")
        return

    last_posted_url = get_last_posted_url()

    if latest_release.url != last_posted_url:
        await process_new_release(latest_release)
    else:
        logging.info("No new release found.")


@check_for_updates.before_loop
async def before_check() -> None:
    """Ensures the bot is ready before the task loop starts."""
    await client.wait_until_ready()


# --- Main Execution ---
if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        logging.critical(
            "Missing required environment variables: DISCORD_BOT_TOKEN and "
            "DISCORD_CHANNEL_ID must be set."
        )
        sys.exit(1)

    try:
        int(DISCORD_CHANNEL_ID)
    except ValueError:
        logging.critical(
            "Config error: DISCORD_CHANNEL_ID must be a valid integer."
        )
        sys.exit(1)

    try:
        client.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logging.critical("Authentication failed: Invalid Discord Bot Token.")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Failed to start the bot: {e}")
        sys.exit(1)
