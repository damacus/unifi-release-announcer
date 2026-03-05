import re

with open("release_parser.py", "r") as f:
    content = f.read()

content = content.replace("def parse_release(release: dict) -> dict:", "def parse_release(release: dict[str, Any]) -> dict[str, Any]:")
content = content.replace("def filter_releases(\n    releases: list[dict],", "def filter_releases(\n    releases: list[dict[str, Any]],")
content = content.replace(") -> list[dict]:", ") -> list[dict[str, Any]]:")

with open("release_parser.py", "w") as f:
    f.write(content)
