# Rust interfaces

The crate exposes configuration, release selection/formatting, GraphQL, parser, Discord and polling modules.

`GraphQl::latest(tags)` returns the newest eligible release per tag. `GraphQl::details(id)` returns a parsed detail object or None when the API explicitly reports no release. Network, GraphQL and invalid-data failures return Result errors.

`Release` has title, url and tag fields. `RawRelease` represents the fields used for feed selection. `parse_feed` provides saved-file parsing and filtering.

`Source` and `Destination` separate fetching from history/posting for tests. `PollState::poll` coordinates selection, deduplication and delivery. Send outcomes are Confirmed, Rejected and Uncertain.

The command-line interfaces are:

```text
unifi-release-announcer [--once] [--dry-run]
release-parser <json-file> [--tags tag1,tag2] [--stage GA] [--limit N]
```

There is no public HTTP server or Gateway event interface. Captured fixtures test compatibility; the former implementation is available in Git history.
