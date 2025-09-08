"""
GraphQL Backend for UniFi Release Scraper

Uses the UniFi Community GraphQL API to fetch release data directly.
More efficient and reliable than web scraping.
"""

import json
import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    pass

class GraphQLBackend:
    """GraphQL-based scraper for UniFi releases."""

    # All valid tags from the UniFi Community API
    ALLOWED_TAGS = [
        "60GHz",
        "aircontrol",
        "airfiber",
        "airfiber-ltu",
        "airmax",
        "airmax-aircube",
        "amplifi",
        "community-feedback",
        "edgemax",
        "edgeswitch",
        "general",
        "gigabeam",
        "innerspace",
        "isp",
        "isp-design-center",
        "routing",
        "security",
        "site-manager",
        "solar",
        "switching",
        "ufiber",
        "uid",
        "uisp-app",
        "uisp-power",
        "unifi",
        "unifi-access",
        "unifi-cloud-gateway",
        "unifi-connect",
        "unifi-design-center",
        "unifi-drive",
        "unifi-gateway-cloudkey",
        "unifi-led",
        "unifi-mobility",
        "unifi-network",
        "unifi-play",
        "unifi-portal",
        "unifi-protect",
        "unifi-routing-switching",
        "unifi-switching",
        "unifi-talk",
        "unifi-video",
        "unifi-voip",
        "unifi-wireless",
        "unms",
        "wave",
        "wifiman",
    ]

    def __init__(self) -> None:
        self.api_url = "https://community.svc.ui.com/"
        self.headers = {
            "accept": "application/graphql-response+json, application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://community.ui.com",
            "referer": "https://community.ui.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
        }

    def get_allowed_tags(self) -> list[str]:
        """Get the list of all allowed tags."""
        return self.ALLOWED_TAGS.copy()

    def get_configured_tags(self) -> list[str]:
        """
        Get configured tags from TAGS environment variable.

        Returns:
            List of configured tags, defaults to ["unifi-protect"] if not set

        Raises:
            ValueError: If any configured tag is not in the allowed list
        """
        tags_env = os.environ.get("TAGS", "").strip()

        if not tags_env:
            return ["unifi-protect"]

        # Parse comma-separated tags and clean them up
        tags = [tag.strip() for tag in tags_env.split(",") if tag.strip()]

        # Validate all tags are in the allowed list
        for tag in tags:
            if tag not in self.ALLOWED_TAGS:
                raise ValueError(f"Invalid tag '{tag}'. Allowed tags are: {', '.join(self.ALLOWED_TAGS)}")

        return tags

    async def get_latest_releases(self) -> list[dict[str, str]]:
        """
        Get the latest releases for all configured tags in a single query.

        Returns:
            List of Release objects for each configured tag
        """
        try:
            tags = self.get_configured_tags()
            logging.info(f"Searching for releases with tags: {tags}")
            if not tags:
                logging.warning("No tags configured for searching!")
                return []

            query = """
            query ReleaseFeedListQuery(
                $tags: [String!],
                $betas: [String!],
                $alphas: [String!],
                $offset: Int,
                $limit: Int,
                $sortBy: ReleasesSortBy,
                $userIsFollowing: Boolean,
                $featuredOnly: Boolean,
                $searchTerm: String,
                $filterTags: [String!],
                $filterEATags: [String!],
                $statuses: [ReleaseStatus!]
            ) {
              releases(
                tags: $tags
                betas: $betas
                alphas: $alphas
                offset: $offset
                limit: $limit
                sortBy: $sortBy
                userIsFollowing: $userIsFollowing
                featuredOnly: $featuredOnly
                searchTerm: $searchTerm
                filterTags: $filterTags
                filterEATags: $filterEATags
                statuses: $statuses
              ) {
                items {
                  id
                  title
                  version
                  slug
                  createdAt
                  tags
                }
              }
            }
            """

            variables = {
                "tags": tags,
                "betas": [],
                "alphas": [],
                "offset": 0,
                "limit": 50,
                "sortBy": None,
                "userIsFollowing": False,
                "featuredOnly": False,
                "searchTerm": "",
                "filterTags": [],
                "filterEATags": [],
                "statuses": ["PUBLISHED"],
            }

            payload = {"query": query, "variables": variables}

            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            all_releases = data.get("data", {}).get("releases", {}).get("items", [])

            if not all_releases:
                logging.warning("No releases found in API response")
                logging.info(f"Full API response: {data}")
                if data and "data" in data:
                    logging.info(f"Data keys: {list(data['data'].keys())}")
                    if "releases" in data["data"]:
                        logging.info(f"Releases structure: {data['data']['releases']}")
                return []

            logging.info(f"Found {len(all_releases)} total releases from API")

            # Group releases by tag and get the latest for each
            releases_by_tag = {}
            for release_data in all_releases:
                release_tags = release_data.get("tags", [])
                release_title = release_data.get("title", "").lower()

                # Find which of our configured tags this release belongs to
                for tag in tags:
                    if tag in release_tags:
                        # Filter out Android and iOS releases from unifi-network
                        if tag == "unifi-network":
                            if ("android" in release_title or
                                "ios" in release_title or
                                "iphone" in release_title or
                                "ipad" in release_title):
                                continue
                        if tag not in releases_by_tag:
                            releases_by_tag[tag] = release_data
                        else:
                            # Keep the most recent (releases are sorted by createdAt DESC)
                            current_date = releases_by_tag[tag]["createdAt"]
                            new_date = release_data["createdAt"]
                            if new_date > current_date:
                                releases_by_tag[tag] = release_data

            # Convert to Release objects
            releases = []
            for tag, release_data in releases_by_tag.items():
                # Determine GA/Beta status
                version = release_data['version'].lower()
                title = release_data['title'].lower()
                
                status_indicator = ""
                if ("beta" in version or "beta" in title or
                    "rc" in version or "candidate" in version):
                    status_indicator = " (Beta)"
                else:
                    status_indicator = " (GA)"
                
                # Create release dict that matches Release dataclass structure
                release_dict = {
                    "title": (f"{release_data['title']} "
                             f"{release_data['version']}{status_indicator}"),
                    "url": (f"https://community.ui.com/releases/"
                           f"{release_data['slug']}/{release_data['id']}"),
                    "tag": tag,
                }
                releases.append(release_dict)

            return releases

        except Exception as e:
            logging.error(f"Error fetching latest releases: {e}")
            return []

    async def get_latest_release(self) -> "Release | None":
        """
        Get the latest UniFi Protect release using GraphQL API.

        Returns:
            Latest Release object or None if not found
        """
        try:
            tags = self.get_configured_tags()

            query = """
            query ReleaseFeedListQuery(
                $tags: [String!],
                $betas: [String!],
                $alphas: [String!],
                $offset: Int,
                $limit: Int,
                $sortBy: ReleasesSortBy,
                $userIsFollowing: Boolean,
                $featuredOnly: Boolean,
                $searchTerm: String,
                $filterTags: [String!],
                $filterEATags: [String!],
                $statuses: [ReleaseStatus!]
            ) {
              releases(
                tags: $tags
                betas: $betas
                alphas: $alphas
                offset: $offset
                limit: $limit
                sortBy: $sortBy
                userIsFollowing: $userIsFollowing
                featuredOnly: $featuredOnly
                searchTerm: $searchTerm
                filterTags: $filterTags
                filterEATags: $filterEATags
                statuses: $statuses
              ) {
                pageInfo {
                  offset
                  limit
                }
                totalCount
                items {
                  id
                  title
                  slug
                  tags
                  betas
                  alphas
                  stage
                  version
                  userStatus {
                    isFollowing
                    lastViewedAt
                  }
                  author {
                    id
                    username
                    isEmployee
                    avatar {
                      color
                      content
                      image
                    }
                  }
                  createdAt
                  lastActivityAt
                  hasUiEngagement
                  isLocked
                  stats {
                    comments
                    views
                  }
                }
              }
            }
            """

            variables = {
                "limit": 1,
                "offset": 0,
                "sortBy": "LATEST",
                "tags": tags,
                "betas": [],
                "alphas": [],
                "searchTerm": "",
            }

            payload = {"query": query, "variables": variables, "operationName": "ReleaseFeedListQuery"}

            logging.info("Fetching latest UniFi Protect release")

            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "errors" in data:
                logging.error(f"GraphQL errors: {data['errors']}")
                return None

            releases = data.get("data", {}).get("releases", {}).get("items", [])

            if not releases:
                logging.info("No releases found")
                return None

            # Return the latest release as Release object
            latest = releases[0]
            from scraper_interface import Release

            return Release(
                title=f"{latest['title']} {latest['version']}",
                url=f"https://community.ui.com/releases/{latest['slug']}/{latest['id']}",
            )

        except requests.RequestException as e:
            logging.error(f"Network error fetching releases: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in GraphQL backend: {e}")
            return None

    def _parse_release(self, release: dict) -> dict:
        """Parse a single release into structured format."""
        return {
            "title": release["title"],
            "slug": release["slug"],
            "url": f"https://community.ui.com/releases/{release['slug']}",
            "tags": release["tags"],
            "stage": release["stage"],
            "version": release["version"],
            "created_at": release["createdAt"],
            "created_date": datetime.fromisoformat(release["createdAt"].replace("Z", "+00:00")).strftime("%Y-%m-%d"),
            "stats": release.get("stats", {}),
            "has_engagement": release.get("hasUiEngagement", False),
            "author": release.get("author"),
            "last_activity": release.get("lastActivityAt"),
        }

    def get_release_details(self, release_id: str) -> dict | None:
        """
        Get detailed information for a specific release.

        Args:
            release_id: The release ID to fetch details for

        Returns:
            Detailed release information or None if not found
        """
        try:
            query = """
            query ReleaseDetailQuery($id: ID!) {
              release(id: $id) {
                id
                title
                slug
                tags
                betas
                alphas
                stage
                version
                createdAt
                lastActivityAt
                author {
                  id
                  username
                  isEmployee
                  avatar {
                    color
                    content
                    image
                  }
                }
                stats {
                  comments
                  views
                }
              }
            }
            """

            payload = {"query": query, "variables": {"id": release_id}, "operationName": "ReleaseDetailQuery"}

            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "errors" in data:
                logging.error(f"GraphQL errors: {data['errors']}")
                return None

            release = data.get("data", {}).get("release")
            if release:
                return self._parse_release(release)

            return None

        except Exception as e:
            logging.error(f"Error fetching release details for {release_id}: {e}")
            return None
