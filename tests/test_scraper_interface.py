"""Tests for the scraper interface module."""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from scraper_interface import Release, get_latest_release


class TestScraperInterface(unittest.TestCase):
    """Test suite for the GraphQL scraper interface."""

    def test_release_dataclass(self) -> None:
        """Test Release dataclass creation."""
        release = Release(title="Test Release", url="https://example.com")
        self.assertEqual(release.title, "Test Release")
        self.assertEqual(release.url, "https://example.com")

    @patch("scraper_interface._backend")
    def test_get_latest_release_success(self, mock_backend: AsyncMock) -> None:
        """Test get_latest_release returns release successfully."""
        mock_backend.get_latest_release = AsyncMock(return_value={"title": "Test Release", "url": "https://test.com", "tag": ""})

        result = asyncio.run(get_latest_release())

        mock_backend.get_latest_release.assert_called_once()
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result.title, "Test Release")
            self.assertEqual(result.url, "https://test.com")

    @patch("scraper_interface._backend")
    def test_get_latest_release_handles_exception(self, mock_backend: AsyncMock) -> None:
        """Test get_latest_release handles exceptions gracefully."""
        mock_backend.get_latest_release = AsyncMock(side_effect=Exception("Backend error"))

        result = asyncio.run(get_latest_release())

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
