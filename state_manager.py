"""State management for tracking last posted releases per tag."""

import asyncio
import json
import logging


class StateManager:
    """Manages per-tag state for tracking last posted release URLs."""

    def __init__(self, state_file: str = "/cache/release_state.json") -> None:
        """
        Initialize state manager.

        Args:
            state_file: Path to JSON file for storing state
        """
        self.state_file = state_file
        self._state: dict[str, str] = {}
        self._load_state()
        self._lock = asyncio.Lock()

    def _load_state(self) -> None:
        """Load state from JSON file."""
        try:
            with open(self.state_file) as f:
                self._state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if isinstance(e, json.JSONDecodeError):
                logging.warning(f"Corrupted state file {self.state_file}, starting fresh")
            self._state = {}

    def _sync_save(self) -> None:
        """Synchronous save state to JSON file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save state to {self.state_file}: {e}")

    def get_last_url(self, tag: str) -> str | None:
        """
        Get the last posted URL for a tag.

        Args:
            tag: The tag to get URL for

        Returns:
            Last posted URL or None if not found
        """
        return self._state.get(tag)

    async def set_last_url(self, tag: str, url: str) -> None:
        """
        Set the last posted URL for a tag.

        Args:
            tag: The tag to set URL for
            url: The URL to store
        """
        async with self._lock:
            self._state[tag] = url
            await asyncio.to_thread(self._sync_save)

    def has_seen_url(self, tag: str, url: str) -> bool:
        """
        Check if we've already seen this URL for this tag.

        Args:
            tag: The tag to check
            url: The URL to check

        Returns:
            True if URL has been seen for this tag, False otherwise
        """
        return self._state.get(tag) == url

    def get_all_tags(self) -> list[str]:
        """
        Get all tags that have state.

        Returns:
            List of all tags with stored state
        """
        return list(self._state.keys())
