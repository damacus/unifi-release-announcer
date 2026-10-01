# Proposal

## Why

The deployed Python bot has a 100 MB container limit and was observed at 43 MiB working-set memory. Move to an HTTP-only Rust runtime with less overhead and explicit handling of history and send failures.

## What Changes

- Preserve Python 0.2.14 release selection, Markdown escaping and configuration.
- Prevent duplicate URLs within a poll and stop posting when history cannot be read.
- Replace the Gateway connection with HTTP; the bot can appear offline.
- Add dry-run and single-poll commands, and port the standalone release parser.
- Build locked, non-root images for amd64 and arm64.
- Require <=32 MiB idle and <=64 MiB peak memory for 24 hours before cutover.
- **BREAKING**: Python import interfaces are replaced by Rust interfaces.

## Capabilities

### New Capabilities

- release-announcements: Select and format eligible releases and deliver text or forum posts.
- announcement-reliability: Deduplicate URLs and handle unavailable history or uncertain sends.
- announcer-runtime: Poll through HTTP, shut down cleanly, support dry-run and meet memory limits.

### Modified Capabilities

None; this repository has no existing capability specs.

## Impact

Rust application, parser, CI, containers, release tooling and documentation. Final deployment updates the existing home-ops HelmRelease while retaining secrets, tags, PVC and Recreate strategy.
