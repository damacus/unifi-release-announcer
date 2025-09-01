"""
Modular scraper interface for UniFi release announcements.
Allows swapping between different scraping backends (Playwright, Selenium, etc.).
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Release:
    """Represents a UniFi release with title and URL."""
    title: str
    url: str


class ScraperBackend(ABC):
    """Abstract base class for scraper backends."""

    @abstractmethod
    async def get_latest_release(self) -> Optional[Release]:
        """
        Fetch the latest release matching configured keywords.

        Returns:
            Release object if found, None otherwise.
        """
        pass


class ScraperFactory:
    """Factory for creating scraper backends."""

    @staticmethod
    def create_scraper(backend: str = "playwright") -> ScraperBackend:
        """
        Create a scraper backend instance.

        Args:
            backend: Backend type ("playwright")

        Returns:
            ScraperBackend instance

        Raises:
            ValueError: If backend type is not supported
        """
        backend = backend.lower()

        if backend == "playwright":
            from scraper_backends.playwright_backend import PlaywrightBackend
            return PlaywrightBackend()
        else:
            raise ValueError(f"Unsupported scraper backend: {backend}")


async def get_latest_release(backend: Optional[str] = None) -> Optional[Release]:
    """
    Convenience function to get the latest release using configured backend.

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
        logging.error(f"Error with {backend} scraper: {e}")
        return None
