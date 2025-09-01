import os
import unittest
from unittest.mock import MagicMock, patch

from selenium.common.exceptions import WebDriverException

from scraper import Release, get_latest_release


class TestScraper(unittest.TestCase):
    """Test suite for the UniFi release scraper."""

    @patch("scraper.webdriver.Chrome")
    def test_get_latest_release_success_default_keyword(
        self, mock_chrome: MagicMock
    ) -> None:
        """Test scraping with the default keyword."""
        mock_driver = MagicMock()
        mock_chrome.return_value.__enter__.return_value = mock_driver

        mock_link = MagicMock()
        mock_link.text = "UniFi Protect Application 6.1.65"
        url = (
            "https://community.ui.com/releases/"
            "UniFi-Protect-Application-6-1-65/short-pro-url"
        )
        mock_link.get_attribute.return_value = url
        mock_driver.find_elements.return_value = [mock_link]

        expected = Release(title="UniFi Protect Application 6.1.65", url=url)
        latest_release = get_latest_release()

        self.assertEqual(latest_release, expected)

    @patch.dict(os.environ, {"RELEASE_KEYWORDS": "UniFi Network"})
    @patch("scraper.webdriver.Chrome")
    def test_get_latest_release_with_custom_keyword(
        self, mock_chrome: MagicMock
    ) -> None:
        """Test scraping respects the RELEASE_KEYWORDS env var."""
        mock_driver = MagicMock()
        mock_chrome.return_value.__enter__.return_value = mock_driver

        mock_link = MagicMock()
        mock_link.text = "UniFi Network Application 8.0.7"
        url = (
            "https://community.ui.com/releases/"
            "UniFi-Network-Application-8-0-7/short-net-url"
        )
        mock_link.get_attribute.return_value = url
        mock_driver.find_elements.return_value = [mock_link]

        expected = Release(title="UniFi Network Application 8.0.7", url=url)
        latest_release = get_latest_release()

        self.assertEqual(latest_release, expected)

    @patch("scraper.webdriver.Chrome")
    def test_get_latest_release_no_matching_release(
        self, mock_chrome: MagicMock
    ) -> None:
        """Test that None is returned when no releases match keywords."""
        mock_driver = MagicMock()
        mock_chrome.return_value.__enter__.return_value = mock_driver

        mock_link = MagicMock()
        mock_link.text = "Some Other App"
        mock_driver.find_elements.return_value = [mock_link]

        latest_release = get_latest_release()

        self.assertIsNone(latest_release)

    @patch("scraper.webdriver.Chrome")
    def test_get_latest_release_webdriver_exception(
        self, mock_chrome: MagicMock
    ) -> None:
        """Test that None is returned on a WebDriverException."""
        mock_chrome.side_effect = WebDriverException("Test Exception")

        latest_release = get_latest_release()

        self.assertIsNone(latest_release)


if __name__ == "__main__":
    unittest.main()
