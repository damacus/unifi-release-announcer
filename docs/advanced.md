# Advanced usage

## Read-only operation

```sh
unifi-release-announcer --once --dry-run
```

Each selected release produces a JSON decision with `tag`, `title`, `url` and `action`. Actions are `would-post`, `already-announced` or `suppressed-local`. Normal posting logs `posted`, `rejected` or `uncertain`.

Dry-run still validates credentials and reads Discord history. It makes no Discord writes.

## Parse saved releases

```sh
release-parser releases.json --tags unifi-network,unifi-protect --stage GA --limit 2
```

Tags match with OR semantics. Stage comparison is exact. Zero limit means no limit; a negative limit removes that many items from the end, matching the Python parser. Output is a sequence of pretty-printed JSON objects, not a JSON array.

## Memory acceptance

```sh
python3 scripts/memory_acceptance.py unifi-rust-memory /private/tmp/unifi-memory-evidence
```

The script observes an already running Docker container; it does not start or restart the bot. Its default duration is 24 hours. It writes samples.ndjson and summary.json. Shorter runs cannot pass the 24-hour gate.

No Redis, JSON state manager or health HTTP server is implemented.
