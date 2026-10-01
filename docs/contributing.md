# Contributing

Use the pinned Rust toolchain and locked dependencies.

```sh
cargo fmt --all --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
mdbook build
```

Captured fixtures in `tests/fixtures/parity.json` preserve the legacy behaviour. The former implementation is available in Git history. Record intentional behaviour changes in OpenSpec and add Rust regression tests; do not silently change fixture expectations to hide a mismatch.

Normal tests use mocked HTTP servers. The ignored `discord_live` test writes one labelled message to the explicitly configured existing channel, reads it back, then removes only its own message. Run it only for authorised live validation.

```sh
cargo test --locked --test discord_live -- --ignored
```

Use conventional commits. Keep credentials and memory evidence outside Git. Production deployment remains gated on the complete memory test and GitOps checks.

Live verification bounds send, read-back and deletion to 30 seconds each (90 seconds total). Cleanup retains its own budget after a failed read. A cleanup timeout reports the exact returned message ID for manual removal.
