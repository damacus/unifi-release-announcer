"""Tests for the main.py application functions."""

import unittest

from main import format_release_message
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


if __name__ == "__main__":
    unittest.main()
