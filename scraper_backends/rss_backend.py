import asyncio
import logging

import feedparser

from scraper_interface import Release, ScraperBackend

FEED_URL = "https://ir.ui.com/rss-feeds"


class RSSBackend(ScraperBackend):
    """Scraper backend for UniFi releases using an RSS feed."""

    async def get_latest_release(self) -> Release | None:
        """Fetches the latest release from the RSS feed."""
        try:
            # feedparser is synchronous, run it in a thread to avoid
            # blocking the event loop.
            feed = await asyncio.to_thread(feedparser.parse, FEED_URL)

            if feed.bozo:
                # bozo is set to 1 if the feed is malformed.
                logging.warning(
                    f"Feed is malformed: {FEED_URL}, "
                    f"reason: {feed.bozo_exception}"
                )

            if not feed.entries:
                logging.warning(f"No entries found in feed: {FEED_URL}")
                return None

            latest_entry = feed.entries[0]
            return Release(title=latest_entry.title, url=latest_entry.link)

        except Exception as e:
            logging.error(f"Error fetching or parsing feed {FEED_URL}: {e}")
            return None
