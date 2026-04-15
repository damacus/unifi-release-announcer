"""Tests for the main.py application functions."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

import main
from main import (
    _post_to_forum,
    _post_to_generic_channel,
    _post_to_text_channel,
    check_for_updates,
    format_release_message,
    get_announced_message_contents,
    process_new_release,
)
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


class TestGetAnnouncedMessageContents(unittest.IsolatedAsyncioTestCase):
    """Test suite for get_announced_message_contents()."""

    TARGET_URL = "https://community.ui.com/releases/unifi-protect/abc123"

    def _make_message(self, content: str) -> MagicMock:
        msg = MagicMock(spec=discord.Message)
        msg.content = content
        return msg

    # --- TextChannel tests ---

    async def test_empty_text_channel_returns_empty_set(self) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        channel.history = MagicMock(return_value=_make_async_iter([]))
        result = await get_announced_message_contents(channel)
        self.assertEqual(result, set())

    async def test_text_channel_returns_contents(self) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        content_str = f"🎉 Release posted\n🔗 [{self.TARGET_URL}]({self.TARGET_URL})"
        msg = self._make_message(content_str)
        channel.history = MagicMock(return_value=_make_async_iter([msg]))
        result = await get_announced_message_contents(channel)
        self.assertEqual(result, {content_str})

    # --- ForumChannel tests ---

    async def test_forum_channel_active_thread_returns_contents(self) -> None:
        channel = MagicMock(spec=discord.ForumChannel)
        thread = MagicMock(spec=discord.Thread)
        msg = self._make_message(self.TARGET_URL)
        thread.history = MagicMock(return_value=_make_async_iter([msg]))
        channel.threads = [thread]
        channel.archived_threads = MagicMock(return_value=_make_async_iter([]))
        result = await get_announced_message_contents(channel)
        self.assertEqual(result, {self.TARGET_URL})

    async def test_forum_channel_archived_thread_returns_contents(self) -> None:
        channel = MagicMock(spec=discord.ForumChannel)
        channel.threads = []
        archived_thread = MagicMock(spec=discord.Thread)
        msg = self._make_message(self.TARGET_URL)
        archived_thread.history = MagicMock(return_value=_make_async_iter([msg]))
        channel.archived_threads = MagicMock(return_value=_make_async_iter([archived_thread]))
        result = await get_announced_message_contents(channel)
        self.assertEqual(result, {self.TARGET_URL})

    # --- Error / edge-case tests ---

    async def test_http_exception_returns_empty_set(self) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        channel.history = MagicMock(side_effect=discord.HTTPException(MagicMock(), "error"))
        result = await get_announced_message_contents(channel)
        self.assertEqual(result, set())

    async def test_channel_without_history_returns_empty_set(self) -> None:
        channel = MagicMock(spec=[])  # no attributes at all
        del channel.history  # ensure hasattr returns False
        result = await get_announced_message_contents(channel)
        self.assertEqual(result, set())


class TestPostingHelpers(unittest.IsolatedAsyncioTestCase):
    """Test suite for _post_to_forum, _post_to_text_channel, _post_to_generic_channel."""

    async def test_post_to_forum_creates_thread_with_correct_name(self) -> None:
        release = Release(title="UniFi Network 8.0.28", url="https://example.com/network")
        message = "🎉 **New UniFi Release Posted**\n\n🔗 [UniFi Network 8.0.28](https://example.com/network) 🔧"
        channel = AsyncMock(spec=discord.ForumChannel)
        thread_result = MagicMock()
        thread_result.thread.name = "UniFi Release: UniFi Network 8.0.28"
        channel.create_thread = AsyncMock(return_value=thread_result)

        await _post_to_forum(channel, release, message)

        channel.create_thread.assert_awaited_once_with(
            name="UniFi Release: UniFi Network 8.0.28",
            content=message,
        )

    async def test_post_to_text_channel_sends_message(self) -> None:
        channel = AsyncMock(spec=discord.TextChannel)
        channel.name = "releases"
        message = "🎉 test message"

        await _post_to_text_channel(channel, message)

        channel.send.assert_awaited_once_with(message)

    async def test_post_to_generic_channel_with_send_returns_true(self) -> None:
        channel = MagicMock()
        channel.send = AsyncMock()

        result = await _post_to_generic_channel(channel, "test message")

        self.assertTrue(result)
        channel.send.assert_awaited_once_with("test message")

    async def test_post_to_generic_channel_without_send_returns_false(self) -> None:
        channel = MagicMock(spec=[])  # no attributes at all

        result = await _post_to_generic_channel(channel, "test message")

        self.assertFalse(result)


class TestProcessNewRelease(unittest.IsolatedAsyncioTestCase):
    """Test suite for process_new_release()."""

    def _make_release(self) -> Release:
        return Release(title="UniFi Network 8.0.28", url="https://example.com/network")

    @patch("main.DISCORD_CHANNEL_ID", "123456")
    @patch("main._post_to_text_channel", new_callable=AsyncMock)
    @patch("main._post_to_forum", new_callable=AsyncMock)
    async def test_dispatches_to_forum_channel(self, mock_forum, mock_text) -> None:
        channel = MagicMock(spec=discord.ForumChannel)
        with patch.object(main.client, "get_channel", return_value=channel):
            await process_new_release(self._make_release())

        mock_forum.assert_awaited_once()
        mock_text.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "123456")
    @patch("main._post_to_forum", new_callable=AsyncMock)
    @patch("main._post_to_text_channel", new_callable=AsyncMock)
    async def test_dispatches_to_text_channel(self, mock_text, mock_forum) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        with patch.object(main.client, "get_channel", return_value=channel):
            await process_new_release(self._make_release())

        mock_text.assert_awaited_once()
        mock_forum.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "123456")
    @patch("main._post_to_generic_channel", new_callable=AsyncMock)
    async def test_dispatches_to_generic_channel(self, mock_generic) -> None:
        channel = MagicMock()  # neither ForumChannel nor TextChannel
        channel.__class__ = type("SomeOtherChannel", (), {})
        with patch.object(main.client, "get_channel", return_value=channel):
            await process_new_release(self._make_release())

        mock_generic.assert_awaited_once()

    @patch("main.DISCORD_CHANNEL_ID", "123456")
    @patch("main._post_to_generic_channel", new_callable=AsyncMock)
    @patch("main._post_to_text_channel", new_callable=AsyncMock)
    @patch("main._post_to_forum", new_callable=AsyncMock)
    async def test_returns_early_when_channel_not_found(self, mock_forum, mock_text, mock_generic) -> None:
        with patch.object(main.client, "get_channel", return_value=None):
            await process_new_release(self._make_release())

        mock_forum.assert_not_awaited()
        mock_text.assert_not_awaited()
        mock_generic.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "123456")
    @patch("main._post_to_text_channel", new_callable=AsyncMock)
    async def test_handles_discord_forbidden(self, mock_text) -> None:
        channel = MagicMock(spec=discord.TextChannel)
        channel.id = 123456
        mock_text.side_effect = discord.Forbidden(MagicMock(), "missing permissions")
        with patch.object(main.client, "get_channel", return_value=channel):
            # Should not raise
            await process_new_release(self._make_release())


class TestCheckForUpdates(unittest.IsolatedAsyncioTestCase):
    """Test suite for the check_for_updates background task."""

    @patch("main.DISCORD_CHANNEL_ID", None)
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    async def test_skips_when_channel_id_not_set(self, mock_get_releases) -> None:
        await check_for_updates.coro()
        mock_get_releases.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "not-an-integer")
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    async def test_skips_when_channel_id_invalid(self, mock_get_releases) -> None:
        await check_for_updates.coro()
        mock_get_releases.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "123")
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    async def test_skips_when_channel_not_found(self, mock_get_releases) -> None:
        with patch.object(main.client, "get_channel", return_value=None):
            await check_for_updates.coro()
        mock_get_releases.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "123")
    @patch("main.process_new_release", new_callable=AsyncMock)
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    async def test_skips_when_no_releases_returned(self, mock_get_releases, mock_process) -> None:
        mock_get_releases.return_value = []
        channel = MagicMock(spec=discord.TextChannel)
        with patch.object(main.client, "get_channel", return_value=channel):
            await check_for_updates.coro()
        mock_process.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "123")
    @patch("main.process_new_release", new_callable=AsyncMock)
    @patch("main.get_announced_message_contents", new_callable=AsyncMock)
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    async def test_posts_new_release(self, mock_get_releases, mock_announced_contents, mock_process) -> None:
        release = Release(title="UniFi Network 8.0.28", url="https://example.com/1")
        mock_get_releases.return_value = [release]
        mock_announced_contents.return_value = set()
        channel = MagicMock(spec=discord.TextChannel)
        with patch.object(main.client, "get_channel", return_value=channel):
            await check_for_updates.coro()
        mock_process.assert_awaited_once_with(release)

    @patch("main.DISCORD_CHANNEL_ID", "123")
    @patch("main.process_new_release", new_callable=AsyncMock)
    @patch("main.get_announced_message_contents", new_callable=AsyncMock)
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    async def test_skips_already_announced_release(
        self, mock_get_releases, mock_announced_contents, mock_process
    ) -> None:
        release = Release(title="UniFi Network 8.0.28", url="https://example.com/1")
        mock_get_releases.return_value = [release]
        mock_announced_contents.return_value = {f"Link: {release.url}"}
        channel = MagicMock(spec=discord.TextChannel)
        with patch.object(main.client, "get_channel", return_value=channel):
            await check_for_updates.coro()
        mock_process.assert_not_awaited()

    @patch("main.DISCORD_CHANNEL_ID", "123")
    @patch("main.process_new_release", new_callable=AsyncMock)
    @patch("main.get_announced_message_contents", new_callable=AsyncMock)
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    async def test_posts_only_unannounced_in_mixed_batch(
        self, mock_get_releases, mock_announced_contents, mock_process
    ) -> None:
        releases = [
            Release(title="Release A", url="https://example.com/a"),
            Release(title="Release B", url="https://example.com/b"),
            Release(title="Release C", url="https://example.com/c"),
        ]
        mock_get_releases.return_value = releases
        mock_announced_contents.return_value = {"Link: https://example.com/b"}
        channel = MagicMock(spec=discord.TextChannel)
        with patch.object(main.client, "get_channel", return_value=channel):
            await check_for_updates.coro()
        self.assertEqual(mock_process.await_count, 2)
        mock_process.assert_any_await(releases[0])
        mock_process.assert_any_await(releases[2])


if __name__ == "__main__":
    unittest.main()
