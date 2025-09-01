"""httpx backend for scraping UniFi releases (static content only)."""

import logging
import os
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from scraper_interface import Release, ScraperBackend


class HttpxBackend(ScraperBackend):
    """httpx + BeautifulSoup backend for static HTML content."""
    
    def get_latest_release(self) -> Optional[Release]:
        """
        Scrapes the UniFi community releases page using httpx + BeautifulSoup.
        
        Note: This only works with static HTML content and won't work
        with JavaScript-rendered pages like the current UniFi site.
        
        Returns:
            Release object if found, None otherwise.
        """
        try:
            # Get keywords from environment or use default
            keywords = os.getenv("RELEASE_KEYWORDS", "UniFi Protect").split(",")
            keywords = [keyword.strip() for keyword in keywords]
            
            # Make HTTP request with proper headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            with httpx.Client(headers=headers, timeout=30.0) as client:
                response = client.get("https://community.ui.com/releases")
                response.raise_for_status()
                
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all release links
            release_links = soup.find_all("a", href=lambda x: x and "/releases/" in x)
            
            for link in release_links:
                # Get title from the link text or nested elements
                title = link.get_text(strip=True)
                if not title:
                    continue
                    
                # Check if any keyword matches the title
                if any(keyword.lower() in title.lower() for keyword in keywords):
                    # Exclude 'Access' if not an explicit keyword
                    if "access" in title.lower() and "access" not in (
                        k.lower() for k in keywords
                    ):
                        continue
                        
                    href = link.get("href")
                    if href and isinstance(href, str):
                        if href.startswith("/"):
                            url = f"https://community.ui.com{href}"
                        else:
                            url = href
                    else:
                        continue
                        
                    logging.info(f"Found matching release: {title}")
                    return Release(title=title, url=url)
            
            logging.info("No matching releases found")
            return None
            
        except httpx.RequestError as e:
            logging.error(f"Network error scraping releases: {e}")
            return None
        except Exception as e:
            logging.error(f"Error scraping releases with httpx: {e}")
            return None
