"""Tests for the release parser module."""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from typing import Any
from unittest.mock import patch

from release_parser import (
    filter_releases,
    format_title_from_slug,
    load_releases,
    main,
    parse_release,
)


class TestReleaseParser(unittest.TestCase):
    """Test suite for release parser functionality."""

    def setUp(self) -> None:
        """Set up test data."""
        self.sample_releases: list[dict[str, Any]] = [
            {
                "title": "UniFi Protect Application 2.8.28",
                "slug": "unifi-protect-application-2-8-28",
                "tags": ["unifi-protect"],
                "stage": "GA",
                "version": "2.8.28",
                "createdAt": "2023-05-15T10:00:00Z",
                "stats": {"views": 1000},
                "hasUiEngagement": True,
                "author": {"username": "UI-Team"},
                "lastActivityAt": "2023-05-15T12:00:00Z",
            },
            {
                "title": "UniFi Network Application 7.4.156",
                "slug": "unifi-network-application-7-4-156",
                "tags": ["unifi-network", "unifi-cloud-gateway"],
                "stage": "EA",
                "version": "7.4.156",
                "createdAt": "2023-06-01T14:30:00Z",
                "stats": {},
            },
            {
                "title": "AmpliFi Alien 3.7.1",
                "slug": "amplifi-alien-3-7-1",
                "tags": ["amplifi"],
                "stage": "GA",
                "version": "3.7.1",
                "createdAt": "2023-04-20T08:15:00Z",
            },
        ]

        self.parsed_releases = [parse_release(r) for r in self.sample_releases]

    def test_load_releases(self) -> None:
        """Test loading releases from a JSON file."""
        data = {"data": {"releases": {"items": self.sample_releases}}}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            loaded = load_releases(temp_path)
            self.assertEqual(len(loaded), 3)
            self.assertEqual(loaded[0]["title"], "UniFi Protect Application 2.8.28")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_format_title_from_slug(self) -> None:
        """Test formatting title from slug."""
        self.assertEqual(format_title_from_slug("unifi-protect-application-2-8-28"), "unifi protect application 2 8 28")
        self.assertEqual(format_title_from_slug("amplifi"), "amplifi")

    def test_parse_release_complete(self) -> None:
        """Test parsing a complete release."""
        release = self.sample_releases[0]
        parsed = parse_release(release)

        self.assertEqual(parsed["title"], "UniFi Protect Application 2.8.28")
        self.assertEqual(parsed["slug"], "unifi-protect-application-2-8-28")
        self.assertEqual(parsed["url"], "https://community.ui.com/releases/unifi-protect-application-2-8-28")
        self.assertEqual(parsed["tags"], ["unifi-protect"])
        self.assertEqual(parsed["stage"], "GA")
        self.assertEqual(parsed["version"], "2.8.28")
        self.assertEqual(parsed["created_at"], "2023-05-15T10:00:00Z")
        self.assertEqual(parsed["created_date"], "2023-05-15")
        self.assertEqual(parsed["stats"], {"views": 1000})
        self.assertTrue(parsed["has_engagement"])
        self.assertEqual(parsed["author"], {"username": "UI-Team"})
        self.assertEqual(parsed["last_activity"], "2023-05-15T12:00:00Z")

    def test_parse_release_missing_optional(self) -> None:
        """Test parsing a release missing optional fields."""
        release = self.sample_releases[2]
        parsed = parse_release(release)

        self.assertEqual(parsed["stats"], {})
        self.assertFalse(parsed["has_engagement"])
        self.assertEqual(parsed["created_date"], "2023-04-20")
        self.assertIsNone(parsed["author"])
        self.assertIsNone(parsed["last_activity"])

    def test_filter_releases_by_tag(self) -> None:
        """Test filtering releases by a single tag."""
        filtered = filter_releases(self.parsed_releases, tags=["unifi-protect"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["slug"], "unifi-protect-application-2-8-28")

    def test_filter_releases_by_multiple_tags(self) -> None:
        """Test filtering releases by multiple tags (OR logic)."""
        filtered = filter_releases(self.parsed_releases, tags=["unifi-protect", "amplifi"])
        self.assertEqual(len(filtered), 2)
        slugs = [r["slug"] for r in filtered]
        self.assertIn("unifi-protect-application-2-8-28", slugs)
        self.assertIn("amplifi-alien-3-7-1", slugs)

    def test_filter_releases_by_stage(self) -> None:
        """Test filtering releases by stage."""
        filtered = filter_releases(self.parsed_releases, stage="EA")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["slug"], "unifi-network-application-7-4-156")

    def test_filter_releases_with_limit(self) -> None:
        """Test filtering releases with a limit."""
        filtered = filter_releases(self.parsed_releases, limit=2)
        self.assertEqual(len(filtered), 2)

    def test_filter_releases_combined(self) -> None:
        """Test filtering with multiple criteria."""
        # This tag exists but not with this stage
        filtered = filter_releases(self.parsed_releases, tags=["unifi-network"], stage="GA")
        self.assertEqual(len(filtered), 0)

        # Match both criteria
        filtered = filter_releases(self.parsed_releases, tags=["unifi-protect"], stage="GA")
        self.assertEqual(len(filtered), 1)

    def test_filter_releases_no_filters(self) -> None:
        """Test filtering with no criteria returns all."""
        filtered = filter_releases(self.parsed_releases)
        self.assertEqual(len(filtered), 3)

    @patch("sys.stdout", new_callable=StringIO)
    def test_main_cli_success(self, mock_stdout: StringIO) -> None:
        """Test main CLI function with valid arguments."""
        data = {"data": {"releases": {"items": self.sample_releases}}}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            # Test with filters
            test_args = ["release_parser.py", temp_path, "--tags", "unifi-protect", "--stage", "GA", "--limit", "1"]
            with patch.object(sys, "argv", test_args):
                main()

            output = mock_stdout.getvalue().strip()
            self.assertTrue(output.startswith("{"))
            # Output might have multiple JSON objects separated by newlines, but here limit=1
            output_json = json.loads(output)
            self.assertEqual(output_json["slug"], "unifi-protect-application-2-8-28")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @patch("sys.stderr", new_callable=StringIO)
    def test_main_cli_missing_args(self, mock_stderr: StringIO) -> None:
        """Test main CLI function fails correctly without arguments."""
        test_args = ["release_parser.py"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)

        self.assertIn("Usage: python release_parser.py", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
