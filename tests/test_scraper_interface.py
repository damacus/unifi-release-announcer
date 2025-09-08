"""Tests for the scraper interface module."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from scraper_interface import Release, get_latest_release


class TestScraperInterface(unittest.TestCase):
    """Test suite for the GraphQL scraper interface."""

    def test_release_dataclass(self) -> None:
        """Test Release dataclass creation."""
        release = Release(title="Test Release", url="https://example.com")
        self.assertEqual(release.title, "Test Release")
        self.assertEqual(release.url, "https://example.com")

    @patch("scraper_interface.GraphQLBackend")
    def test_get_latest_release_success(self, mock_backend_class: MagicMock) -> None:
        """Test get_latest_release returns release successfully."""
        mock_backend = AsyncMock()
        mock_backend.get_latest_release.return_value = Release("Test Release", "https://test.com")
        mock_backend_class.return_value = mock_backend

        result = asyncio.run(get_latest_release())

        mock_backend_class.assert_called_once()
        mock_backend.get_latest_release.assert_called_once()
        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        self.assertEqual(result.title, "Test Release")
        self.assertEqual(result.url, "https://test.com")

    @patch("scraper_interface.GraphQLBackend")
    def test_get_latest_release_handles_exception(self, mock_backend_class: MagicMock) -> None:
        """Test get_latest_release handles exceptions gracefully."""
        mock_backend_class.side_effect = Exception("Backend error")

        result = asyncio.run(get_latest_release())

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
