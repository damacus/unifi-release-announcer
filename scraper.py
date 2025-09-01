import logging
import os
from typing import List, NamedTuple, Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- Constants ---
BASE_URL = "https://community.ui.com"
RELEASES_URL = f"{BASE_URL}/releases"
# --- Data Structures ---
class Release(NamedTuple):
    """Represents a software release announcement."""

    title: str
    url: str


# --- Core Scraping Logic ---
def get_latest_release() -> Optional[Release]:
    """Fetches the latest release matching the keywords using Selenium."""
    release_keywords: List[str] = [
        k.strip() for k in os.environ.get("RELEASE_KEYWORDS", "UniFi Protect").split(",")
    ]
    logging.info(f"Scraping {RELEASES_URL} for new releases via Selenium...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        service = Service(ChromeDriverManager().install())
        with webdriver.Chrome(service=service, options=options) as driver:
            driver.get(RELEASES_URL)
            driver.implicitly_wait(10)  # seconds

            release_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/releases/']")

            for link in release_links:
                # Find the title span within the link and get its text
                try:
                    title_element = link.find_element(By.CSS_SELECTOR, "span")
                    title = title_element.text.strip()
                except Exception:
                    # If the span isn't found, fall back to the link's text but log a warning
                    logging.warning("Could not find title span, falling back to link text.")
                    title = link.text.strip()
                if not title:
                    continue

                # Check if the title contains any of the specified keywords
                if any(k.strip().lower() in title.lower() for k in release_keywords):
                    # Exclude 'Access' if not an explicit keyword
                    if "access" in title.lower() and "access" not in (
                        k.lower() for k in release_keywords
                    ):
                        continue

                    url = link.get_attribute('href') or ""
                    logging.info(f"Found matching release: {title}")
                    return Release(title=title, url=url)

            logging.warning("No matching release found on the page.")
            return None

    except WebDriverException as e:
        logging.error(f"Selenium scraping failed: {e}")
    except Exception as e:
        # Catching broader exceptions to handle unexpected errors
        logging.error(f"An unexpected error occurred during Selenium scraping: {e}")

    return None
