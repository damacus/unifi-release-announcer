"""Tests for the scraper interface module."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from scraper_interface import Release, get_latest_release, get_latest_releases


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
        mock_backend.get_latest_release = AsyncMock(
            return_value={"title": "Test Release", "url": "https://test.com", "tag": ""}
        )

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

    @patch("scraper_interface._backend")
    def test_get_latest_releases_returns_list(self, mock_backend) -> None:
        """Test get_latest_releases returns a list of Release objects."""
        mock_backend.get_latest_releases = AsyncMock(
            return_value=[
                {"title": "T1", "url": "https://u.com/1", "tag": "unifi-protect"},
            ]
        )

        result = asyncio.run(get_latest_releases())

        mock_backend.get_latest_releases.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "T1")
        self.assertEqual(result[0].url, "https://u.com/1")
        self.assertEqual(result[0].tag, "unifi-protect")

    @patch("scraper_interface._backend")
    def test_get_latest_releases_returns_empty_list(self, mock_backend) -> None:
        """Test get_latest_releases returns [] when backend returns no results."""
        mock_backend.get_latest_releases = AsyncMock(return_value=[])

        result = asyncio.run(get_latest_releases())

        self.assertEqual(result, [])

    @patch("scraper_interface._backend")
    def test_get_latest_releases_handles_exception(self, mock_backend) -> None:
        """Test get_latest_releases returns [] and swallows exceptions."""
        mock_backend.get_latest_releases = AsyncMock(side_effect=Exception("backend failure"))

        result = asyncio.run(get_latest_releases())

        self.assertEqual(result, [])

    @patch("scraper_interface.GraphQLBackend")
    def test_get_latest_releases_with_session_creates_new_backend(self, mock_cls) -> None:
        """Test that passing a session creates a fresh GraphQLBackend instance."""
        mock_session = MagicMock()
        mock_instance = MagicMock()
        mock_instance.get_latest_releases = AsyncMock(return_value=[])
        mock_cls.return_value = mock_instance

        asyncio.run(get_latest_releases(session=mock_session))

        mock_cls.assert_called_once_with(session=mock_session)


if __name__ == "__main__":
    unittest.main()
