# Tasks

## 1. Reference and specification

- [x] 1.1 Obtain Python 0.2.14 source and run baseline tests; verify 79 tests pass.
- [x] 1.2 Create proposal, design and capability specs; verify strict OpenSpec validation.

## 2. Rust release behaviour

- [x] 2.1 Add configuration and pure selection/formatting with shared fixtures; verify Python/Rust parity.
- [x] 2.2 Port GraphQL, parser and details; verify malformed/error responses and CLI fixtures.

## 3. HTTP announcements

- [x] 3.1 Implement history, posting and deduplication; verify pagination, forum, failures and uncertain sends.
- [x] 3.2 Add sequential polling, dry-run and shutdown; verify no writes in dry-run and bounded termination.

## 4. Packaging and acceptance

- [x] 4.1 Update CI, Taskfile, release tooling, containers and docs; verify fmt, Clippy, tests and docs build.
- [x] 4.2 Build non-root amd64/arm64 release images; verify both run.
- [x] 4.3 Verify one labelled message in the existing channel; read back and delete only its ID.
- [ ] 4.4 Run 24-hour memory acceptance with live history; verify <=32 MiB idle and <=64 MiB peak.
- [ ] 4.5 Publish an immutable release image; verify its digest and completed CI.

## 5. GitOps preparation

- [x] 5.1 Create a dedicated home-ops worktree and failing rollout contract test; verify the pre-change assertion fails.
- [ ] 5.2 Pin the release digest with unchanged secrets, tags, PVC, replicas and Recreate; verify task k8s:yayamlls and reviewable deployment PR.

## 6. Final cluster deployment

- [ ] 6.1 Deploy an isolated dry-run canary; verify history and memory without writes.
- [ ] 6.2 Replace production through Flux; verify exact revision/digest and one writer.
- [ ] 6.3 Restart once and observe for 24 hours; verify deduplication, thresholds and no unexplained errors.
- [ ] 6.4 Archive only after production acceptance; verify OpenSpec archival or rollback to Python on failure.

## 7. Remove the legacy toolchain

- [x] 7.1 Remove Python source, tests, dependencies and fixture generator; retain captured JSON fixtures and Git history.
- [x] 7.2 Replace the memory sampler with Rust and documentation with mdBook; verify regression tests, documentation build and workflow lint.
