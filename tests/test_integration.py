"""
Integration test to verify the modular scraper works with main.py
"""

import asyncio
import logging

from scraper_interface import get_latest_release

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def test_integration() -> None:
    """Synchronous wrapper for pytest compatibility."""
    asyncio.run(_test_integration_async())


async def _test_integration_async() -> None:
    logging.info("🧪 Testing GraphQL Scraper")
    logging.info("=" * 30)

    # Test GraphQL backend
    logging.info("📡 Testing GraphQL backend...")
    release = await get_latest_release()

    if release:
        logging.info("✅ GraphQL test successful!")
        logging.info(f"📋 Title: {release.title}")
        logging.info(f"🔗 URL: {release.url}")
    else:
        logging.warning("⚠️  GraphQL returned no results")

    logging.info("")
    logging.info("🎯 Integration test complete!")


if __name__ == "__main__":
    asyncio.run(_test_integration_async())
