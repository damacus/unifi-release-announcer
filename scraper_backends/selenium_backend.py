"""Selenium backend for scraping UniFi releases (legacy support)."""

import asyncio
import logging
import os

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from scraper_interface import Release, ScraperBackend


class SeleniumBackend(ScraperBackend):
    """Selenium-based scraper backend (legacy)."""

    async def get_latest_release(self) -> Release | None:
        """Fetches the latest release via a thread-safe Selenium scraper."""
        return await asyncio.to_thread(self._scrape_releases)

    def _scrape_releases(self) -> Release | None:
        """
        Fetches the latest release matching the keywords using Selenium.

        Returns:
            Release object if found, None otherwise.
        """
        keywords_str = os.environ.get("RELEASE_KEYWORDS", "UniFi Protect")
        release_keywords = [k.strip() for k in keywords_str.split(",")]
        logging.info("Scraping releases via Selenium...")

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            service = Service(ChromeDriverManager().install())
            with webdriver.Chrome(service=service, options=options) as driver:
                driver.get("https://community.ui.com/releases")
                driver.implicitly_wait(10)

                release_links = driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='/releases/']"
                )

                for link in release_links:
                    try:
                        title_element = link.find_element(
                            By.CSS_SELECTOR, "span"
                        )
                        title = title_element.text.strip()
                    except Exception:
                        logging.warning(
                            "Could not find title span, "
                            "falling back to link text."
                        )
                        title = link.text.strip()

                    if not title:
                        continue

                    if any(
                        k.strip().lower() in title.lower()
                        for k in release_keywords
                    ):
                        if "access" in title.lower() and "access" not in (
                            k.lower() for k in release_keywords
                        ):
                            continue

                        url = link.get_attribute("href") or ""
                        logging.info(f"Found matching release: {title}")
                        return Release(title=title, url=url)

                logging.warning("No matching release found on the page.")
                return None

        except WebDriverException as e:
            logging.error(f"Selenium scraping failed: {e}")
        except Exception as e:
            logging.error(
                f"An unexpected error occurred during Selenium scraping: {e}"
            )

        return None
