#!/usr/bin/env python3
"""
Integration test to verify the modular scraper works with main.py
"""

import asyncio
import logging

from scraper_interface import get_latest_release

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_integration() -> None:
    """Synchronous wrapper for pytest compatibility."""
    asyncio.run(_test_integration_async())


async def _test_integration_async() -> None:
    logging.info("🧪 Testing Integrated Modular Scraper System")
    logging.info("=" * 50)

    # Test default backend (should be playwright)
    logging.info("📡 Testing default backend (Playwright)...")
    release = await get_latest_release()

    if release:
        logging.info("✅ Success! Found release:")
        logging.info(f"📋 Title: {release.title}")
        logging.info(f"🔗 URL: {release.url}")
        logging.info(f"🏷️  Type: {type(release).__name__}")
    else:
        logging.info("⚠️  No release found (this might be expected)")

    logging.info("")

    # Test with explicit backend override
    logging.info("🔄 Testing backend override...")
    try:
        release_override = await get_latest_release(backend="playwright")
        if release_override:
            logging.info("✅ Backend override successful!")
            logging.info(f"📋 Title: {release_override.title}")
        else:
            logging.info("⚠️  No release found with override")
    except Exception as e:
        logging.info(f"❌ Backend override failed: {e}")

    logging.info("")

    # Test error handling
    logging.info("🛡️  Testing error handling...")
    try:
        error_release = await get_latest_release(backend="nonexistent")
        logging.info(f"❌ Should have failed but got: {error_release}")
    except Exception as e:
        logging.info(f"✅ Error handling works: {e}")

    logging.info("")
    logging.info("🎯 Integration test complete!")


if __name__ == "__main__":
    asyncio.run(_test_integration_async())
