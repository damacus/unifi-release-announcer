import logging

import httpx
from defusedxml import ElementTree as DefusedET

from scraper_interface import Release, ScraperBackend

FEED_URL = "https://ir.ui.com/rss-feeds"


class XMLBackend(ScraperBackend):
    """Scraper backend for UniFi releases using an XML feed."""

    async def get_latest_release(self) -> Release | None:
        """Fetches the latest release from the XML feed."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(FEED_URL)
                response.raise_for_status()
                root = DefusedET.fromstring(response.content)

                # The first item in the feed is the latest
                latest_item = root.find(".//item")
                if latest_item is None:
                    return None

                title_element = latest_item.find("title")
                link_element = latest_item.find("link")

                if title_element is None or link_element is None:
                    return None

                title = title_element.text
                link = link_element.text

                if title is None or link is None:
                    return None

                return Release(title=title, url=link)

            except httpx.HTTPStatusError as e:
                logging.error(f"Error fetching feed {FEED_URL}: {e}")
            except DefusedET.ParseError as e:
                logging.error(f"Error parsing feed {FEED_URL}: {e}")

        return None
