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
        return await scraper.get_latest_release()
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
        # Convert dicts to Release objects
        releases = []
        for release_dict in release_dicts:
            release = Release(title=release_dict["title"], url=release_dict["url"], tag=release_dict["tag"])
            releases.append(release)
        return releases
    except Exception as e:
        logging.error(f"Error fetching releases: {e}")
        return []
