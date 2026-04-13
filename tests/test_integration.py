"""Integration tests for the full announcement pipeline (fully mocked, no network calls)."""

import unittest
from unittest.mock import AsyncMock, patch

import discord

import main
from main import check_for_updates
from scraper_interface import Release


class TestBotPipeline(unittest.IsolatedAsyncioTestCase):
    """End-to-end pipeline tests: scraper → deduplication → Discord post."""

    def _make_release(self) -> Release:
        return Release(
            title="UniFi Network 8.0.28 (GA)",
            url="https://community.ui.com/releases/network-8-0-28/abc123",
            tag="unifi-network",
        )

    @patch("main.DISCORD_CHANNEL_ID", "999")
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    @patch("main.get_announced_message_contents", new_callable=AsyncMock)
    async def test_full_pipeline_new_release_gets_posted(self, mock_announced, mock_get_releases) -> None:
        """A new, unseen release should result in a Discord message being sent."""
        release = self._make_release()
        mock_get_releases.return_value = [release]
        mock_announced.return_value = set()

        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_channel.name = "releases"

        with patch.object(main.client, "get_channel", return_value=mock_channel):
            await check_for_updates.coro()

        mock_channel.send.assert_awaited_once()
        sent_message = mock_channel.send.call_args[0][0]
        self.assertIn(release.title, sent_message)
        self.assertIn(release.url, sent_message)

    @patch("main.DISCORD_CHANNEL_ID", "999")
    @patch("main.get_latest_releases", new_callable=AsyncMock)
    @patch("main.get_announced_message_contents", new_callable=AsyncMock)
    async def test_full_pipeline_already_announced_not_reposted(self, mock_announced, mock_get_releases) -> None:
        """A release that was already announced should not be posted again."""
        release = self._make_release()
        mock_get_releases.return_value = [release]
        mock_announced.return_value = {release.url}

        mock_channel = AsyncMock(spec=discord.TextChannel)

        with patch.object(main.client, "get_channel", return_value=mock_channel):
            await check_for_updates.coro()

        mock_channel.send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
