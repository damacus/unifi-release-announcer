"""
GraphQL Backend for UniFi Release Scraper

Uses the UniFi Community GraphQL API to fetch release data directly.
More efficient and reliable than web scraping.
"""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from scraper_interface import Release


class GraphQLBackend:
    """GraphQL-based scraper for UniFi releases."""

    def __init__(self) -> None:
        self.api_url = "https://community.svc.ui.com/"
        self.headers = {
            'accept': 'application/graphql-response+json, application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://community.ui.com',
            'referer': 'https://community.ui.com/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }

    async def get_latest_release(self) -> "Release | None":
        """
        Get the latest UniFi Protect release using GraphQL API.

        Returns:
            Latest Release object or None if not found
        """
        try:
            tags = ["unifi-protect"]

            query = """
            query ReleaseFeedListQuery($tags: [String!], $betas: [String!], $alphas: [String!], $offset: Int, $limit: Int, $sortBy: ReleasesSortBy, $userIsFollowing: Boolean, $featuredOnly: Boolean, $searchTerm: String, $filterTags: [String!], $filterEATags: [String!], $statuses: [ReleaseStatus!]) {
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
                "searchTerm": ""
            }

            payload = {
                "query": query,
                "variables": variables,
                "operationName": "ReleaseFeedListQuery"
            }

            logging.info("Fetching latest UniFi Protect release")

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if 'errors' in data:
                logging.error(f"GraphQL errors: {data['errors']}")
                return None

            releases = data.get('data', {}).get('releases', {}).get('items', [])

            if not releases:
                logging.info("No releases found")
                return None

            # Return the latest release as Release object
            latest = releases[0]
            from scraper_interface import Release
            return Release(
                title=f"{latest['title']} {latest['version']}",
                url=f"https://community.ui.com/releases/{latest['slug']}/{latest['id']}"
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

    def _parse_release(self, release: Dict) -> Dict:
        """Parse a single release into structured format."""
        return {
            'title': release['title'],
            'slug': release['slug'],
            'url': f"https://community.ui.com/releases/{release['slug']}",
            'tags': release['tags'],
            'stage': release['stage'],
            'version': release['version'],
            'created_at': release['createdAt'],
            'created_date': datetime.fromisoformat(
                release['createdAt'].replace('Z', '+00:00')
            ).strftime('%Y-%m-%d'),
            'stats': release.get('stats', {}),
            'has_engagement': release.get('hasUiEngagement', False),
            'author': release.get('author'),
            'last_activity': release.get('lastActivityAt')
        }

    def get_release_details(self, release_id: str) -> Optional[Dict]:
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

            payload = {
                "query": query,
                "variables": {"id": release_id},
                "operationName": "ReleaseDetailQuery"
            }

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if 'errors' in data:
                logging.error(f"GraphQL errors: {data['errors']}")
                return None

            release = data.get('data', {}).get('release')
            if release:
                return self._parse_release(release)

            return None

        except Exception as e:
            logging.error(f"Error fetching release details for {release_id}: {e}")
            return None
