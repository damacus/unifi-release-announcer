"""Playwright backend for scraping UniFi releases."""

import logging
import os

from playwright.async_api import async_playwright

from scraper_interface import Release, ScraperBackend


class PlaywrightBackend(ScraperBackend):
    """Playwright-based scraper for JavaScript-rendered content."""

    async def get_latest_release(self) -> Release | None:
        """
        Scrapes the UniFi community releases page using Playwright.

        Returns:
            Release object if a matching release is found, None otherwise.
        """
        try:
            # Get keywords from environment or use default
            keywords_str = os.getenv("RELEASE_KEYWORDS", "Protect")
            keywords = [k.strip() for k in keywords_str.split(",")]

            async with async_playwright() as p:
                # Launch browser with realistic settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )

                # Create page with realistic user agent
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/91.0.4472.124 Safari/537.36"
                    )
                )

                # Set shorter timeout and try different wait strategy
                page.set_default_timeout(15000)  # 15 seconds

                # Navigate to releases page
                await page.goto(
                    "https://community.ui.com/releases",
                    wait_until="domcontentloaded",
                )

                # Wait for content to load (React app needs time)
                await page.wait_for_timeout(5000)  # 5s for React to render

                # Find all release links after JavaScript has rendered
                release_links = await page.locator(
                    "a[href*='/releases/']"
                ).all()

                logging.info(
                    f"Found {len(release_links)} release links on page"
                )

                for link in release_links:
                    try:
                        text_content = await link.text_content()
                        if not text_content:
                            continue
                        raw_title = text_content.strip()
                        if not raw_title:
                            continue

                        # Clean up title by removing extra metadata
                        title_parts = raw_title.split("Official")
                        title = (
                            title_parts[0].strip()
                            if title_parts
                            else raw_title
                        )

                        # Further cleanup - remove common suffixes
                        for suffix in ["Activity", "Follow", "Released"]:
                            if suffix in title:
                                title = title.split(suffix)[0].strip()

                        if not title:
                            continue

                        # Check if any keyword matches the title
                        if any(k.lower() in title.lower() for k in keywords):
                            # Exclude 'Access' if not an explicit keyword
                            if "access" in title.lower() and "access" not in (
                                k.lower() for k in keywords
                            ):
                                continue

                            href = await link.get_attribute("href")
                            if href and href.startswith("/"):
                                url = f"https://community.ui.com{href}"
                            else:
                                url = href or ""

                            logging.info(f"Found matching release: {title}")
                            await browser.close()
                            return Release(title=title, url=url)

                    except Exception as e:
                        logging.warning(f"Error processing link: {e}")
                        continue

                await browser.close()
                logging.info("No matching releases found")
                return None

        except Exception as e:
            logging.error(
                f"Error scraping releases with Playwright: {e}"
            )
            return None
