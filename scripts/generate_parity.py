"""Generate committed synthetic fixtures with the preserved Python 0.2.14 oracle."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import format_release_message
from scraper_backends.graphql_backend import GraphQLBackend
from scraper_interface import Release
from release_parser import parse_release, filter_releases

items = [{"id":"a","title":"UniFi Protect Application","version":"6.0","createdAt":"2026-09-01T10:00:00Z","tags":["unifi-protect"],"slug":"release-a","stage":"GA"},{"id":"b","title":"UniFi Protect AI Key","version":"2.0","createdAt":"2026-09-03T10:00:00Z","tags":["unifi-protect"],"slug":"release-b","stage":"GA"},{"id":"c","title":"UniFi Network Application Beta","version":"9.0-rc1","createdAt":"2026-09-02T10:00:00Z","tags":["unifi-network","unifi-cloud-gateway"],"slug":"release-c","stage":"GA"},{"id":"d","title":"UniFi Network iOS","version":"9.1","createdAt":"2026-09-04T10:00:00Z","tags":["unifi-network"],"slug":"release-d","stage":"GA"},{"id":"e","title":"UniFi Drive Application","version":"4.0","createdAt":"2026-09-01T10:00:00Z","tags":["unifi-drive"],"slug":"release-e","stage":"GA"},{"id":"f","title":"AmpliFi Alien","version":"3.7","createdAt":"2026-09-01T10:00:00Z","tags":["amplifi"],"slug":"release-f","stage":"GA"},{"id":"g","title":"AmpliFi Android","version":"3.8","createdAt":"2026-09-05T10:00:00Z","tags":["amplifi"],"slug":"release-g","stage":"GA"},{"id":"h","title":"UniFi Protect Application","version":"6.1","createdAt":"2026-09-02T10:00:00Z","tags":["unifi-protect"],"slug":"release-h","stage":"GA"},{"id":"i","title":"UniFi Protect Application tie","version":"6.1","createdAt":"2026-09-02T10:00:00Z","tags":["unifi-protect"],"slug":"release-i","stage":"GA"},{"id":"j","title":"UniFi Talk Application","version":"2.0candidate","createdAt":"2026-09-03T10:00:00Z","tags":["unifi-talk"],"slug":"release-j","stage":"GA"}]
tags = ["unifi-protect", "unifi-network", "unifi-drive", "amplifi", "unifi-talk"]
backend = GraphQLBackend()
selected = backend._process_releases_response(items, tags)
releases = [backend._format_release_dict(tag, raw) for tag, raw in selected.items()]
titles = ["UniFi Protect Application 6.0 (GA)","UniFi **Network** [Application] _9_","UniFi Application [release](https://example.test/a_b)","## Application\n> quote\n- release","UniFi Application https://example.test/a_b","UniFi iOS","ANDROID desktop","UniFi desktop","UniFi \\ ~ | * `"]
formats = []
for title in titles:
    release = Release(title, "https://community.ui.com/releases/example/id", "unifi-network")
    formats.append({"release": release.__dict__, "message": format_release_message(release)})
parsed = [parse_release(raw) for raw in items]
data = {
    "items": items, "tags": tags, "releases": releases, "formats": formats,
    "payload": backend._build_latest_releases_payload(tags),
    "parsed": parsed,
    "parser_filtered": filter_releases(parsed, ["unifi-protect"], "GA", 1),
}
Path("tests/fixtures/parity.json").parent.mkdir(parents=True, exist_ok=True)
Path("tests/fixtures/parity.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
