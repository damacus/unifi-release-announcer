# Design

## Context

See proposal.md. Production is Python 0.2.14, one replica in Ironstone default, image digest 19ef75ff3c21473a49e07c91ed19aefa9187cd286b8e595d783eb2148cb4a552. It posts to the existing unifi text channel. HTTP reads of 100 bot-authored announcements succeeded. The current deployment is Recreate with a 100M request and limit.

## Goals / Non-Goals

**Goals:** Preserve useful behaviour and reduce memory; explicit recoverable failures and safe rollout.
**Non-Goals:** Add RSS, databases, commands, a Gateway connection, unbounded history, new monitoring infrastructure or remove the PVC.

## Decisions

One Rust 2024 Cargo package; Tokio current-thread runtime; Reqwest/Rustls for GraphQL; Serenity HTTP-only for Discord; Serde, Clap, tracing and Chrono. Pin the toolchain and lock dependencies. Disable Gateway, cache and voice features. A Gateway was rejected because no inbound events are needed.

Reuse the deployed GraphQL payload, headers, timeout and 50-item window. Keep selection/formatting pure and fixture-testable. Use deterministic configured-tag ordering where Python's set ordering was unspecified.

Discord history remains authoritative across restarts. Read 200 text messages using before pagination. Read starter messages from active forum threads and 50 archived public threads. Any history failure aborts posting for that poll. Deduplicate candidate URLs before sends. Retain uncertain and confirmed URLs in a bounded process-local set to protect subsequent polls during this process lifetime; no persistent state migration. Never blindly replay an uncertain send.

Normal invocation polls immediately, then every ten minutes with skipped missed ticks. --once performs one poll; --dry-run prints JSON decisions without sending. All calls are bounded; SIGTERM/SIGINT allows up to 30 seconds for an in-flight operation before cancellation.

Preserve parser filters, field names and pretty-printed JSON objects. Port the detail query as a library method. Remove the former source and tooling; Git history retains the reference implementation. Captured fixtures verify compatibility, mdBook builds documentation, and a Rust binary collects memory acceptance evidence.

## Risks / Trade-offs

- Bounded history can miss old announcements -> document the 200-message/50-archive limit; do not promise exactly-once delivery.
- POST timeout can occur after delivery -> do not immediately replay; retain URL locally and reconcile history.
- Forum starter deleted -> fail the poll rather than infer empty history.
- No Gateway -> bot may appear offline; authorised by user.
- Memory measurement depends on workload -> sample Docker working set from the host every 15 seconds for 24 hours with production tags and live history, including polls and startup; record poll states for idle classification.
- Container needs credentials -> mount a restricted env file from outside Git; no token logging.

## Migration Plan

Land independently verifiable source changes in order. Validate both container architectures, live posting through one labelled verification message in the existing channel, and 24-hour local dry-run memory measurements. Prepare the home-ops change with a pinned release digest and unchanged resource limits/PVC. Deployment is last: an isolated dry-run canary, then Recreate production replacement. Verify Flux revision, image, one writer, history, restart deduplication and 24-hour memory. Roll back through GitOps to the recorded Python digest on failure. Do not archive before production acceptance.

## Runtime image and update automation

Build static musl binaries using the digest-pinned Rust Alpine builder, then copy only the two binaries into scratch. Run as UID 1000. Verify both supported architectures and enforce a 32 MiB uncompressed image limit in CI. A dedicated Rust job runs fmt, Clippy, tests and release builds. Renovate minor updates require passing CI through the existing main ruleset; its required build-and-push check now waits for Rust tests and both container checks and at least 24 hours since release; missing release timestamps stay pending. Major and unaged update types remain manual. Restart local memory acceptance when changing the runtime image.

## Review corrections

Filter GraphQL items to configured tags before validating release fields, so unrelated incomplete items cannot block announcements. Preserve JSON field insertion order and Python ASCII escaping in parser output. Observe Docker directly from the portable memory sampler and record startup failures. Live verification reserves separate 30-second send, read and cleanup budgets. Release image publishing depends on the complete reusable CI checks for the exact release tag; local 24-hour memory evidence is required before merging the migration and deployment.
