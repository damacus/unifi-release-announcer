"""
GraphQL Backend for UniFi Release Scraper

Uses the UniFi Community GraphQL API to fetch release data directly.
More efficient and reliable than web scraping.
"""

import contextlib
import logging
import os
from datetime import datetime

import aiohttp


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

    _ALLOWED_TAGS_SET = frozenset(ALLOWED_TAGS)

    # Pre-compiled unwanted patterns to avoid re-allocating on every release
    UNWANTED_PATTERNS = (
        "android",
        "ios",
        "iphone",
        "ipad",
        "sfp wizard",
        "ups",
    )

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        self.api_url = "https://community.svc.ui.com/"
        self.session = session
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

    @contextlib.asynccontextmanager
    async def _get_session(self):
        """Yields the injected session if it exists, otherwise a temporary one."""
        if self.session:
            yield self.session
        else:
            async with aiohttp.ClientSession() as session:
                yield session

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
            if tag not in self._ALLOWED_TAGS_SET:
                raise ValueError(f"Invalid tag '{tag}'. Allowed tags are: {', '.join(self.ALLOWED_TAGS)}")

        return tags

    def _format_release_dict(self, tag: str, release_data: dict) -> dict[str, str]:
        """Format a single release dictionary with title, url, and tag."""
        # Determine GA/Beta status
        version = release_data["version"].lower()
        title = release_data["title"].lower()

        status_indicator = ""
        if "beta" in version or "beta" in title or "rc" in version or "candidate" in version:
            status_indicator = " (Beta)"
        else:
            status_indicator = " (GA)"

        # Create release dict that matches Release dataclass structure
        return {
            "title": (f"{release_data['title']} {release_data['version']}{status_indicator}"),
            "url": (f"https://community.ui.com/releases/{release_data['slug']}/{release_data['id']}"),
            "tag": tag,
        }

    def _process_releases_response(self, all_releases: list[dict], tags: list[str]) -> dict[str, dict]:
        """Filter and group releases by tag, returning the latest for each."""
        releases_by_tag = {}
        for release_data in all_releases:
            release_tags = release_data.get("tags", [])
            release_title = release_data.get("title", "").lower()

            # Check if this release should be filtered out
            should_skip = False
            for pattern in self.UNWANTED_PATTERNS:
                if pattern in release_title:
                    should_skip = True
                    logging.debug(f"Filtering out release '{release_data.get('title')}' due to pattern '{pattern}'")
                    break

            if should_skip:
                continue

            # Find which of our configured tags this release belongs to
            for tag in tags:
                if tag in release_tags:
                    if tag not in releases_by_tag:
                        releases_by_tag[tag] = release_data
                    else:
                        # Keep the most recent (releases are sorted by createdAt DESC)
                        current_date = releases_by_tag[tag]["createdAt"]
                        new_date = release_data["createdAt"]
                        if new_date > current_date:
                            releases_by_tag[tag] = release_data

        return releases_by_tag

    def _build_latest_releases_payload(self, tags: list[str]) -> dict:
        """Build the GraphQL query payload for fetching latest releases."""
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

        return {"query": query, "variables": variables}

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

            payload = self._build_latest_releases_payload(tags)

            async with self._get_session() as session:
                async with session.post(
                    self.api_url, headers=self.headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            all_releases = data.get("data", {}).get("releases", {}).get("items", [])

            if not all_releases:
                logging.warning("No releases found in API response")
                logging.debug(f"Full API response: {data}")
                return []

            logging.info(f"Found {len(all_releases)} total releases from API")

            releases_by_tag = self._process_releases_response(all_releases, tags)

            # Convert to Release objects
            releases = []
            for tag, release_data in releases_by_tag.items():
                releases.append(self._format_release_dict(tag, release_data))

            return releases

        except Exception as e:
            logging.error(f"Error fetching latest releases: {e}")
            return []

    async def get_latest_release(self) -> dict | None:
        """
        Get the latest UniFi Protect release using GraphQL API.

        Returns:
            Dict with title, url, and tag keys, or None if not found
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

            async with self._get_session() as session:
                async with session.post(
                    self.api_url, headers=self.headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            if "errors" in data:
                logging.error(f"GraphQL errors: {data['errors']}")
                return None

            releases = data.get("data", {}).get("releases", {}).get("items", [])

            if not releases:
                logging.info("No releases found")
                return None

            latest = releases[0]
            return {
                "title": f"{latest['title']} {latest['version']}",
                "url": f"https://community.ui.com/releases/{latest['slug']}/{latest['id']}",
                "tag": "",
            }

        except aiohttp.ClientError as e:
            logging.error(f"Network error fetching releases: {e}")
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

    async def get_release_details(self, release_id: str) -> dict | None:
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

            async with self._get_session() as session:
                async with session.post(
                    self.api_url, headers=self.headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

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
