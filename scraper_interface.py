"""GraphQL scraper for UniFi releases."""

import logging
from dataclasses import dataclass

from scraper_backends.graphql_backend import GraphQLBackend


@dataclass
class Release:
    """
    Represents a UniFi release with title and URL.
    """
    title: str
    url: str


async def get_latest_release() -> Release | None:
    """Get the latest release using GraphQL backend.

    Returns:
        Release object if found, None otherwise
    """
    try:
        scraper = GraphQLBackend()
        return await scraper.get_latest_release()
    except Exception as e:
        logging.error(f"Error fetching release: {e}")
        return None
