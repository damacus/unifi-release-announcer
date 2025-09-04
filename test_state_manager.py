"""Tests for the state manager module."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from state_manager import StateManager


class TestStateManager(unittest.TestCase):
    """Test suite for state management functionality."""

    def setUp(self) -> None:
        """Set up test environment with temporary state file."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")
        self.state_manager = StateManager(self.state_file)

    def tearDown(self) -> None:
        """Clean up test environment."""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        os.rmdir(self.temp_dir)

    def test_get_last_url_empty_state(self) -> None:
        """Test getting last URL when no state file exists."""
        url = self.state_manager.get_last_url("unifi-protect")
        self.assertIsNone(url)

    def test_set_and_get_last_url(self) -> None:
        """Test setting and getting last URL for a tag."""
        test_url = "https://example.com/release/123"
        self.state_manager.set_last_url("unifi-protect", test_url)
        
        retrieved_url = self.state_manager.get_last_url("unifi-protect")
        self.assertEqual(retrieved_url, test_url)

    def test_multiple_tags_independent_state(self) -> None:
        """Test that different tags maintain independent state."""
        protect_url = "https://example.com/protect/123"
        network_url = "https://example.com/network/456"
        
        self.state_manager.set_last_url("unifi-protect", protect_url)
        self.state_manager.set_last_url("unifi-network", network_url)
        
        self.assertEqual(self.state_manager.get_last_url("unifi-protect"), protect_url)
        self.assertEqual(self.state_manager.get_last_url("unifi-network"), network_url)

    def test_update_existing_tag(self) -> None:
        """Test updating URL for existing tag."""
        old_url = "https://example.com/old/123"
        new_url = "https://example.com/new/456"
        
        self.state_manager.set_last_url("unifi-protect", old_url)
        self.state_manager.set_last_url("unifi-protect", new_url)
        
        retrieved_url = self.state_manager.get_last_url("unifi-protect")
        self.assertEqual(retrieved_url, new_url)

    def test_state_persistence(self) -> None:
        """Test that state persists across StateManager instances."""
        test_url = "https://example.com/persistent/123"
        
        # Set URL with first instance
        self.state_manager.set_last_url("unifi-protect", test_url)
        
        # Create new instance and verify URL persists
        new_state_manager = StateManager(self.state_file)
        retrieved_url = new_state_manager.get_last_url("unifi-protect")
        self.assertEqual(retrieved_url, test_url)

    def test_has_seen_url_false_for_new_tag(self) -> None:
        """Test has_seen_url returns False for new tag."""
        test_url = "https://example.com/new/123"
        result = self.state_manager.has_seen_url("unifi-protect", test_url)
        self.assertFalse(result)

    def test_has_seen_url_false_for_different_url(self) -> None:
        """Test has_seen_url returns False for different URL."""
        stored_url = "https://example.com/stored/123"
        test_url = "https://example.com/different/456"
        
        self.state_manager.set_last_url("unifi-protect", stored_url)
        result = self.state_manager.has_seen_url("unifi-protect", test_url)
        self.assertFalse(result)

    def test_has_seen_url_true_for_same_url(self) -> None:
        """Test has_seen_url returns True for same URL."""
        test_url = "https://example.com/same/123"
        
        self.state_manager.set_last_url("unifi-protect", test_url)
        result = self.state_manager.has_seen_url("unifi-protect", test_url)
        self.assertTrue(result)

    def test_corrupted_state_file_handled_gracefully(self) -> None:
        """Test that corrupted state file is handled gracefully."""
        # Write invalid JSON to state file
        with open(self.state_file, 'w') as f:
            f.write("invalid json content")
        
        # Should not raise exception and should return None
        url = self.state_manager.get_last_url("unifi-protect")
        self.assertIsNone(url)
        
        # Should be able to set new URL after corruption
        test_url = "https://example.com/recovery/123"
        self.state_manager.set_last_url("unifi-protect", test_url)
        
        retrieved_url = self.state_manager.get_last_url("unifi-protect")
        self.assertEqual(retrieved_url, test_url)

    def test_get_all_tags(self) -> None:
        """Test getting all tags from state."""
        self.state_manager.set_last_url("unifi-protect", "url1")
        self.state_manager.set_last_url("unifi-network", "url2")
        self.state_manager.set_last_url("amplifi", "url3")
        
        tags = self.state_manager.get_all_tags()
        expected_tags = {"unifi-protect", "unifi-network", "amplifi"}
        self.assertEqual(set(tags), expected_tags)

    def test_get_all_tags_empty_state(self) -> None:
        """Test getting all tags when state is empty."""
        tags = self.state_manager.get_all_tags()
        self.assertEqual(tags, [])


if __name__ == "__main__":
    unittest.main()
