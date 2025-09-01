"""Tests for the scraper interface module."""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from scraper_interface import Release, ScraperFactory, get_latest_release


class TestScraperInterface(unittest.TestCase):
    """Test suite for the modular scraper interface."""

    def test_release_dataclass(self) -> None:
        """Test Release dataclass creation."""
        release = Release(title="Test Release", url="https://example.com")
        self.assertEqual(release.title, "Test Release")
        self.assertEqual(release.url, "https://example.com")

    def test_scraper_factory_playwright(self) -> None:
        """Test ScraperFactory creates Playwright backend."""
        with patch('scraper_backends.playwright_backend.PlaywrightBackend') as mock_backend:
            ScraperFactory.create_scraper("playwright")
            mock_backend.assert_called_once()

    def test_scraper_factory_unsupported_backend(self) -> None:
        """Test ScraperFactory raises error for unsupported backends."""
        with self.assertRaises(ValueError) as context:
            ScraperFactory.create_scraper("selenium")
        self.assertIn("Unsupported scraper backend: selenium", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            ScraperFactory.create_scraper("httpx")
        self.assertIn("Unsupported scraper backend: httpx", str(context.exception))

    def test_scraper_factory_invalid_backend(self) -> None:
        """Test ScraperFactory raises error for invalid backend."""
        with self.assertRaises(ValueError) as context:
            ScraperFactory.create_scraper("invalid")
        self.assertIn("Unsupported scraper backend: invalid", str(context.exception))

    @patch.dict(os.environ, {"SCRAPER_BACKEND": "playwright"})
    @patch('scraper_interface.ScraperFactory.create_scraper')
    def test_get_latest_release_uses_env_backend(self, mock_create: MagicMock) -> None:
        """Test get_latest_release uses environment variable for backend."""
        mock_scraper = AsyncMock()
        mock_scraper.get_latest_release.return_value = Release("Test", "https://test.com")
        mock_create.return_value = mock_scraper

        result = asyncio.run(get_latest_release())

        mock_create.assert_called_once_with("playwright")
        self.assertIsNotNone(result)

    @patch('scraper_interface.ScraperFactory.create_scraper')
    def test_get_latest_release_override_backend(self, mock_create: MagicMock) -> None:
        """Test get_latest_release can override backend."""
        mock_scraper = AsyncMock()
        mock_scraper.get_latest_release.return_value = Release("Test", "https://test.com")
        mock_create.return_value = mock_scraper

        result = asyncio.run(get_latest_release("selenium"))

        mock_create.assert_called_once_with("selenium")
        self.assertIsNotNone(result)

    @patch('scraper_interface.ScraperFactory.create_scraper')
    def test_get_latest_release_handles_exception(self, mock_create: MagicMock) -> None:
        """Test get_latest_release handles exceptions gracefully."""
        mock_create.side_effect = Exception("Backend error")

        result = asyncio.run(get_latest_release())

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
