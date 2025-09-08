"""Tests for the GraphQL backend module."""

import os
import unittest
from unittest.mock import MagicMock, patch
from scraper_backends.graphql_backend import GraphQLBackend


class TestGraphQLBackendBase(unittest.TestCase):
    """Base test class with common setup and teardown."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Clear any existing TAGS environment variable
        if "TAGS" in os.environ:
            del os.environ["TAGS"]

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Clear any TAGS environment variable set during tests
        if "TAGS" in os.environ:
            del os.environ["TAGS"]

    def create_mock_response(self, releases_data: list) -> MagicMock:
        """Create a mock response with given releases data."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": releases_data
                }
            }
        }
        return mock_response


class TestGraphQLBackendTags(TestGraphQLBackendBase):
    """Test suite for GraphQL backend configurable tags functionality."""

    def test_default_tags_when_no_env_var(self) -> None:
        """Test that default tags are used when TAGS environment variable is not set."""
        backend = GraphQLBackend()
        tags = backend.get_configured_tags()
        self.assertEqual(tags, ["unifi-protect"])

    def test_single_tag_from_env_var(self) -> None:
        """Test parsing single tag from TAGS environment variable."""
        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()
        tags = backend.get_configured_tags()
        self.assertEqual(tags, ["unifi-network"])

    def test_multiple_tags_from_env_var_comma_separated(self) -> None:
        """Test parsing multiple comma-separated tags from TAGS environment variable."""
        os.environ["TAGS"] = "unifi-protect,unifi-network,unifi-access"
        backend = GraphQLBackend()
        tags = backend.get_configured_tags()
        self.assertEqual(tags, ["unifi-protect", "unifi-network", "unifi-access"])

    def test_multiple_tags_with_spaces_are_trimmed(self) -> None:
        """Test that spaces around tags are trimmed."""
        os.environ["TAGS"] = " unifi-protect , unifi-network , unifi-access "
        backend = GraphQLBackend()
        tags = backend.get_configured_tags()
        self.assertEqual(tags, ["unifi-protect", "unifi-network", "unifi-access"])

    def test_empty_tags_filtered_out(self) -> None:
        """Test that empty tags are filtered out."""
        os.environ["TAGS"] = "unifi-protect,,unifi-network,"
        backend = GraphQLBackend()
        tags = backend.get_configured_tags()
        self.assertEqual(tags, ["unifi-protect", "unifi-network"])

    def test_invalid_tag_raises_error(self) -> None:
        """Test that invalid tags raise ValueError."""
        os.environ["TAGS"] = "invalid-tag"
        backend = GraphQLBackend()
        with self.assertRaises(ValueError) as context:
            backend.get_configured_tags()
        self.assertIn("Invalid tag 'invalid-tag'", str(context.exception))

    def test_mixed_valid_and_invalid_tags_raises_error(self) -> None:
        """Test that mix of valid and invalid tags raises ValueError."""
        os.environ["TAGS"] = "unifi-protect,invalid-tag,unifi-network"
        backend = GraphQLBackend()
        with self.assertRaises(ValueError) as context:
            backend.get_configured_tags()
        self.assertIn("Invalid tag 'invalid-tag'", str(context.exception))

    def test_case_sensitive_tag_validation(self) -> None:
        """Test that tag validation is case-sensitive."""
        os.environ["TAGS"] = "UNIFI-PROTECT"  # Wrong case
        backend = GraphQLBackend()
        with self.assertRaises(ValueError) as context:
            backend.get_configured_tags()
        self.assertIn("Invalid tag 'UNIFI-PROTECT'", str(context.exception))

    def test_all_valid_tags_accepted(self) -> None:
        """Test that all valid tags from the API are accepted."""
        # Test a selection of valid tags
        valid_tags = [
            "unifi-protect",
            "unifi-network",
            "unifi-access",
            "unifi-talk",
            "edgemax",
            "amplifi",
            "general",
            "security",
        ]
        os.environ["TAGS"] = ",".join(valid_tags)
        backend = GraphQLBackend()
        tags = backend.get_configured_tags()
        self.assertEqual(tags, valid_tags)

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_get_latest_releases_for_multiple_tags(self, mock_post: MagicMock) -> None:
        """Test that get_latest_releases queries all tags in single request."""
        # Mock successful API response with releases for multiple tags
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": [
                        {
                            "id": "123",
                            "title": "Network Release",
                            "version": "1.0.0",
                            "slug": "network-release",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-01T00:00:00Z",
                        },
                        {
                            "id": "456",
                            "title": "Protect Release",
                            "version": "2.0.0",
                            "slug": "protect-release",
                            "tags": ["unifi-protect"],
                            "createdAt": "2023-01-02T00:00:00Z",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        # Set multiple tags
        os.environ["TAGS"] = "unifi-network,unifi-protect"
        backend = GraphQLBackend()

        # Call the method
        import asyncio

        results = asyncio.run(backend.get_latest_releases())

        # Verify we got results for both tags
        self.assertEqual(len(results), 2)

        # Verify API was called only once (single query for all tags)
        self.assertEqual(mock_post.call_count, 1)

        # Verify the call used all configured tags
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(set(payload["variables"]["tags"]), {"unifi-network", "unifi-protect"})

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_get_latest_releases_handles_empty_results(self, mock_post: MagicMock) -> None:
        """Test that get_latest_releases handles tags with no releases."""
        # Mock response with no items
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": {"releases": {"items": []}}}
        mock_post.return_value = mock_response

        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()

        import asyncio

        results = asyncio.run(backend.get_latest_releases())

        # Should return empty list when no releases found
        self.assertEqual(results, [])

    def test_get_allowed_tags_returns_complete_list(self) -> None:
        """Test that get_allowed_tags returns the complete list of valid tags."""
        backend = GraphQLBackend()
        allowed_tags = backend.get_allowed_tags()

        # Should include all 46 tags we discovered
        self.assertEqual(len(allowed_tags), 46)
        self.assertIn("unifi-protect", allowed_tags)
        self.assertIn("unifi-network", allowed_tags)
        self.assertIn("edgemax", allowed_tags)
        self.assertIn("amplifi", allowed_tags)


class TestGraphQLBackendFiltering(TestGraphQLBackendBase):
    """Test suite for GraphQL backend filtering functionality."""

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_filters_android_releases_from_unifi_network(
        self, mock_post: MagicMock
    ) -> None:
        """Test that Android releases are filtered out from unifi-network tag."""
        releases_data = [
            {
                "id": "123",
                "title": "UniFi Network Android",
                "version": "1.0.0",
                "slug": "network-android",
                "tags": ["unifi-network"],
                "createdAt": "2023-01-01T00:00:00Z",
            },
            {
                "id": "456",
                "title": "UniFi Network",
                "version": "2.0.0",
                "slug": "network-base",
                "tags": ["unifi-network"],
                "createdAt": "2023-01-02T00:00:00Z",
            },
        ]
        mock_post.return_value = self.create_mock_response(releases_data)

        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()

        import asyncio
        results = asyncio.run(backend.get_latest_releases())

        # Should only return the base network release, not Android
        self.assertEqual(len(results), 1)
        self.assertIn("UniFi Network 2.0.0", results[0]["title"])
        self.assertNotIn("Android", results[0]["title"])

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_filters_ios_releases_from_unifi_network(
        self, mock_post: MagicMock
    ) -> None:
        """Test that iOS releases are filtered out from unifi-network tag."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": [
                        {
                            "id": "123",
                            "title": "UniFi Network iOS",
                            "version": "1.0.0",
                            "slug": "network-ios",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-01T00:00:00Z",
                        },
                        {
                            "id": "456",
                            "title": "UniFi Network iPhone",
                            "version": "1.1.0",
                            "slug": "network-iphone",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-02T00:00:00Z",
                        },
                        {
                            "id": "789",
                            "title": "UniFi Network iPad",
                            "version": "1.2.0",
                            "slug": "network-ipad",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-03T00:00:00Z",
                        },
                        {
                            "id": "101",
                            "title": "UniFi Network",
                            "version": "2.0.0",
                            "slug": "network-base",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-04T00:00:00Z",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()

        import asyncio
        results = asyncio.run(backend.get_latest_releases())

        # Should only return the base network release
        self.assertEqual(len(results), 1)
        self.assertIn("UniFi Network 2.0.0", results[0]["title"])

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_does_not_filter_mobile_releases_from_other_tags(
        self, mock_post: MagicMock
    ) -> None:
        """Test that mobile releases are not filtered from non-unifi-network tags."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": [
                        {
                            "id": "123",
                            "title": "UniFi Protect Android",
                            "version": "1.0.0",
                            "slug": "protect-android",
                            "tags": ["unifi-protect"],
                            "createdAt": "2023-01-01T00:00:00Z",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        os.environ["TAGS"] = "unifi-protect"
        backend = GraphQLBackend()

        import asyncio
        results = asyncio.run(backend.get_latest_releases())

        # Should return the Android release for protect tag
        self.assertEqual(len(results), 1)
        self.assertIn("UniFi Protect Android", results[0]["title"])

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_adds_ga_status_to_stable_releases(
        self, mock_post: MagicMock
    ) -> None:
        """Test that GA status is added to stable releases."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": [
                        {
                            "id": "123",
                            "title": "UniFi Network",
                            "version": "8.0.28",
                            "slug": "network-stable",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-01T00:00:00Z",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()

        import asyncio
        results = asyncio.run(backend.get_latest_releases())

        self.assertEqual(len(results), 1)
        self.assertIn("(GA)", results[0]["title"])
        self.assertEqual(results[0]["title"], "UniFi Network 8.0.28 (GA)")

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_adds_beta_status_to_beta_releases(
        self, mock_post: MagicMock
    ) -> None:
        """Test that Beta status is added to beta releases."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": [
                        {
                            "id": "123",
                            "title": "UniFi Network",
                            "version": "8.1.0-beta.1",
                            "slug": "network-beta",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-01T00:00:00Z",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()

        import asyncio
        results = asyncio.run(backend.get_latest_releases())

        self.assertEqual(len(results), 1)
        self.assertIn("(Beta)", results[0]["title"])
        self.assertEqual(results[0]["title"], "UniFi Network 8.1.0-beta.1 (Beta)")

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_adds_beta_status_to_rc_releases(
        self, mock_post: MagicMock
    ) -> None:
        """Test that Beta status is added to release candidate versions."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": [
                        {
                            "id": "123",
                            "title": "UniFi Network",
                            "version": "8.1.0-rc.1",
                            "slug": "network-rc",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-01T00:00:00Z",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()

        import asyncio
        results = asyncio.run(backend.get_latest_releases())

        self.assertEqual(len(results), 1)
        self.assertIn("(Beta)", results[0]["title"])
        self.assertEqual(results[0]["title"], "UniFi Network 8.1.0-rc.1 (Beta)")

    @patch("scraper_backends.graphql_backend.requests.post")
    def test_detects_beta_in_title(self, mock_post: MagicMock) -> None:
        """Test that Beta status is detected when 'beta' appears in title."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "releases": {
                    "items": [
                        {
                            "id": "123",
                            "title": "UniFi Network Beta",
                            "version": "8.1.0",
                            "slug": "network-beta-title",
                            "tags": ["unifi-network"],
                            "createdAt": "2023-01-01T00:00:00Z",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        os.environ["TAGS"] = "unifi-network"
        backend = GraphQLBackend()

        import asyncio
        results = asyncio.run(backend.get_latest_releases())

        self.assertEqual(len(results), 1)
        self.assertIn("(Beta)", results[0]["title"])


if __name__ == "__main__":
    unittest.main()
