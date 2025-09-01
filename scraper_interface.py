"""Scraper backend interface."""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Release:
    """
    Represents a UniFi release with title and URL.
    """
    title: str
    url: str


class ScraperBackend(ABC):
    """Abstract base class for scraper backends."""

    @abstractmethod
    async def get_latest_release(self) -> Release | None:
        """
        Fetch the latest release matching configured keywords.

        Returns:
            Release object if found, None otherwise.
        """
        pass


class ScraperFactory:
    """Factory for creating scraper backends."""

    @staticmethod
    def create_scraper(
        backend: str = "playwright",
    ) -> ScraperBackend:
        """Create a scraper backend instance.

        Args:
            backend: The name of the scraper backend to create.

        Returns:
            An instance of a ScraperBackend.

        Raises:
            ValueError: If the backend is not supported.
        """
        backend = backend.lower()

        if backend == "playwright":
            from scraper_backends.playwright_backend import PlaywrightBackend
            return PlaywrightBackend()
        elif backend == "rss":
            from scraper_backends.rss_backend import RSSBackend
            return RSSBackend()
        else:
            raise ValueError(
                f"Unsupported scraper backend: {backend}"
            )


async def get_latest_release(
    backend: str | None = None,
) -> Release | None:
    """Get the latest release.

    Args:
        backend: Override backend type from environment

    Returns:
        Release object if found, None otherwise
    """
    if backend is None:
        backend = os.getenv("SCRAPER_BACKEND", "playwright")

    try:
        scraper = ScraperFactory.create_scraper(backend)
        return await scraper.get_latest_release()
    except Exception as e:
        logging.error(
            f"Error with {backend} scraper: {e}"
        )
        return None
