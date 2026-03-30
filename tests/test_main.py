"""Tests for the main.py application functions."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from main import format_release_message, has_announced_url
from scraper_interface import Release


class TestMain(unittest.TestCase):
    """Test suite for functions in main.py."""

    def test_format_release_message_default(self) -> None:
        """Test formatting with a generic title (default emoji)."""
        release = Release(title="UniFi Network 8.0.28", url="https://example.com/network")
        message = format_release_message(release)
        self.assertIn("🎉 **New UniFi Release Posted**", message)
        self.assertIn("🔗 [UniFi Network 8.0.28](https://example.com/network)", message)
        self.assertTrue(message.endswith("🔧"))

    def test_format_release_message_ios(self) -> None:
        """Test formatting with an iOS title."""
        release = Release(title="UniFi Protect iOS 2.13.1", url="https://example.com/ios")
        message = format_release_message(release)
        self.assertTrue(message.endswith("📱"))

    def test_format_release_message_ios_case_insensitive(self) -> None:
        """Test formatting with an iOS title case-insensitively."""
        release = Release(title="UniFi Protect IOS 2.13.1", url="https://example.com/ios")
        message = format_release_message(release)
        self.assertTrue(message.endswith("📱"))

    def test_format_release_message_android(self) -> None:
        """Test formatting with an Android title."""
        release = Release(title="UniFi Network Android 4.14.2", url="https://example.com/android")
        message = format_release_message(release)
        self.assertTrue(message.endswith("🤖"))

    def test_format_release_message_android_case_insensitive(self) -> None:
        """Test formatting with an Android title case-insensitively."""
        release = Release(title="UniFi Network aNdRoId 4.14.2", url="https://example.com/android")
        message = format_release_message(release)
        self.assertTrue(message.endswith("🤖"))

    def test_format_release_message_desktop(self) -> None:
        """Test formatting with a Desktop title."""
        release = Release(title="UniFi Protect Desktop 1.5.0", url="https://example.com/desktop")
        message = format_release_message(release)
        self.assertTrue(message.endswith("💻"))

    def test_format_release_message_application(self) -> None:
        """Test formatting with an Application title."""
        release = Release(title="UniFi Network Application 8.0.28", url="https://example.com/app")
        message = format_release_message(release)
        self.assertTrue(message.endswith("💻"))

    def test_format_release_message_application_case_insensitive(self) -> None:
        """Test formatting with an Application title case-insensitively."""
        release = Release(title="UniFi Network ApPlIcAtIoN 8.0.28", url="https://example.com/app")
        message = format_release_message(release)
        self.assertTrue(message.endswith("💻"))


def _make_async_iter(items):
    """Return an object that supports 'async for' over the given items."""
    async def _aiter():
        for item in items:
            yield item
    return _aiter()


class TestHasAnnouncedUrl(unittest.IsolatedAsyncioTestCase):
    """Test suite for has_announced_url()."""

    TARGET_URL = "https://community.ui.com/releases/unifi-protect/abc123"

    def _make_message(self, content: str) -> MagicMock:
        msg = MagicMock(spec=discord.Message)
        msg.content = content
        return msg

    # --- TextChannel tests ---

    async def test_empty_text_channel_returns_false(self) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        channel.history = MagicMock(return_value=_make_async_iter([]))
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertFalse(result)

    async def test_text_channel_url_found_returns_true(self) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        msg = self._make_message(f"🎉 Release posted\n🔗 [{self.TARGET_URL}]({self.TARGET_URL})")
        channel.history = MagicMock(return_value=_make_async_iter([msg]))
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertTrue(result)

    async def test_text_channel_url_not_in_history_returns_false(self) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        msg = self._make_message("https://community.ui.com/releases/other/xyz")
        channel.history = MagicMock(return_value=_make_async_iter([msg]))
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertFalse(result)

    # --- ForumChannel tests ---

    async def test_forum_channel_active_thread_url_found(self) -> None:
        channel = MagicMock(spec=discord.ForumChannel)
        thread = MagicMock(spec=discord.Thread)
        msg = self._make_message(self.TARGET_URL)
        thread.history = MagicMock(return_value=_make_async_iter([msg]))
        channel.threads = [thread]
        channel.archived_threads = MagicMock(return_value=_make_async_iter([]))
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertTrue(result)

    async def test_forum_channel_archived_thread_url_found(self) -> None:
        channel = MagicMock(spec=discord.ForumChannel)
        channel.threads = []
        archived_thread = MagicMock(spec=discord.Thread)
        msg = self._make_message(self.TARGET_URL)
        archived_thread.history = MagicMock(return_value=_make_async_iter([msg]))
        channel.archived_threads = MagicMock(return_value=_make_async_iter([archived_thread]))
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertTrue(result)

    async def test_forum_channel_no_match_returns_false(self) -> None:
        channel = MagicMock(spec=discord.ForumChannel)
        thread = MagicMock(spec=discord.Thread)
        msg = self._make_message("https://community.ui.com/releases/other/xyz")
        thread.history = MagicMock(return_value=_make_async_iter([msg]))
        channel.threads = [thread]
        channel.archived_threads = MagicMock(return_value=_make_async_iter([]))
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertFalse(result)

    # --- Error / edge-case tests ---

    async def test_http_exception_returns_false(self) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        channel.history = MagicMock(side_effect=discord.HTTPException(MagicMock(), "error"))
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertFalse(result)

    async def test_channel_without_history_returns_false(self) -> None:
        channel = MagicMock(spec=[])  # no attributes at all
        del channel.history  # ensure hasattr returns False
        result = await has_announced_url(channel, self.TARGET_URL)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
