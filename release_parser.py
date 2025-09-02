#!/usr/bin/env python3
"""
UniFi Release Parser

Extracts and filters UniFi release data from the GraphQL API response.
Provides structured data with URLs, filtering by tags and stage.
"""

import json
import sys
from datetime import datetime
from typing import List, Dict, Optional


def load_releases(file_path: str) -> List[Dict]:
    """Load releases from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data['data']['releases']['items']


def format_title_from_slug(slug: str) -> str:
    """Convert slug to readable title if needed."""
    # Replace hyphens with spaces and handle version numbers
    return slug.replace('-', ' ')


def parse_release(release: Dict) -> Dict:
    """Parse a single release into structured format."""
    return {
        'title': release['title'],
        'slug': release['slug'],
        'url': f"https://community.ui.com/releases/{release['slug']}",
        'tags': release['tags'],
        'stage': release['stage'],
        'version': release['version'],
        'created_at': release['createdAt'],
        'created_date': datetime.fromisoformat(release['createdAt'].replace('Z', '+00:00')).strftime('%Y-%m-%d'),
        'stats': release.get('stats', {}),
        'has_engagement': release.get('hasUiEngagement', False)
    }


def filter_releases(releases: List[Dict], 
                   tags: Optional[List[str]] = None,
                   stage: Optional[str] = None,
                   limit: Optional[int] = None) -> List[Dict]:
    """Filter releases by tags and stage."""
    filtered = releases
    
    if tags:
        filtered = [r for r in filtered if any(tag in r['tags'] for tag in tags)]
    
    if stage:
        filtered = [r for r in filtered if r['stage'] == stage]
    
    if limit:
        filtered = filtered[:limit]
    
    return filtered


def main():
    """Main function with CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: python release_parser.py <json_file> [--tags tag1,tag2] [--stage GA|EA] [--limit N]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Parse command line arguments
    tags = None
    stage = None
    limit = None
    
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == '--tags' and i + 1 < len(sys.argv):
            tags = sys.argv[i + 1].split(',')
        elif arg == '--stage' and i + 1 < len(sys.argv):
            stage = sys.argv[i + 1]
        elif arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    
    # Load and process releases
    raw_releases = load_releases(file_path)
    parsed_releases = [parse_release(r) for r in raw_releases]
    filtered_releases = filter_releases(parsed_releases, tags, stage, limit)
    
    # Output results
    print(json.dumps(filtered_releases, indent=2))


if __name__ == '__main__':
    main()
