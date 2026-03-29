"""GraphQL scraper for UniFi releases."""

import logging
from dataclasses import dataclass

import aiohttp

from scraper_backends.graphql_backend import GraphQLBackend

_backend = GraphQLBackend()


@dataclass
class Release:
    """
    Represents a UniFi release with title and URL.
    """

    title: str
    url: str
    tag: str = ""  # Optional tag field for multi-tag support


async def get_latest_release(session: aiohttp.ClientSession | None = None) -> Release | None:
    """Get the latest release using GraphQL backend.

    Args:
        session: Optional aiohttp ClientSession for connection pooling

    Returns:
        Release object if found, None otherwise
    """
    try:
        scraper = GraphQLBackend(session=session) if session else _backend
        result = await scraper.get_latest_release()
        if result is None:
            return None
        return Release(title=result["title"], url=result["url"], tag=result["tag"])
    except Exception as e:
        logging.error(f"Error fetching release: {e}")
        return None


async def get_latest_releases(session: aiohttp.ClientSession | None = None) -> list[Release]:
    """Get the latest releases for all configured tags using GraphQL backend.

    Args:
        session: Optional aiohttp ClientSession for connection pooling

    Returns:
        List of Release objects, one per configured tag (if available)
    """
    try:
        scraper = GraphQLBackend(session=session) if session else _backend
        release_dicts = await scraper.get_latest_releases()
        return [Release(title=r["title"], url=r["url"], tag=r["tag"]) for r in release_dicts]
    except Exception as e:
        logging.error(f"Error fetching releases: {e}")
        return []
