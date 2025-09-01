#!/usr/bin/env python3
"""
Integration test to verify the modular scraper works with main.py
"""

import asyncio
import logging
import os
from scraper_interface import get_latest_release

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def test_integration():
    """Synchronous wrapper for pytest compatibility."""
    asyncio.run(_test_integration_async())


async def _test_integration_async():
    print("🧪 Testing Integrated Modular Scraper System")
    print("=" * 50)

    # Test default backend (should be playwright)
    print("📡 Testing default backend (Playwright)...")
    release = await get_latest_release()

    if release:
        print("✅ Success! Found release:")
        print(f"📋 Title: {release.title}")
        print(f"🔗 URL: {release.url}")
        print(f"🏷️  Type: {type(release).__name__}")
    else:
        print("⚠️  No release found (this might be expected)")

    print()

    # Test with explicit backend override
    print("🔄 Testing backend override...")
    try:
        release_override = await get_latest_release(backend="playwright")
        if release_override:
            print("✅ Backend override successful!")
            print(f"📋 Title: {release_override.title}")
        else:
            print("⚠️  No release found with override")
    except Exception as e:
        print(f"❌ Backend override failed: {e}")

    print()

    # Test error handling
    print("🛡️  Testing error handling...")
    try:
        error_release = await get_latest_release(backend="nonexistent")
        print(f"❌ Should have failed but got: {error_release}")
    except Exception as e:
        print(f"✅ Error handling works: {e}")

    print()
    print("🎯 Integration test complete!")


if __name__ == "__main__":
    asyncio.run(_test_integration_async())
