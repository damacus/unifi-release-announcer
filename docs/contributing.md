# Contributing

Use the pinned Rust toolchain and locked dependencies.

```sh
cargo fmt --all --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
uv run --extra dev python -m unittest discover -s tests -p "test_*.py"
uv run --extra dev mkdocs build --strict
```

Python 0.2.14 code is the frozen compatibility reference. Synthetic fixtures are generated with:

```sh
uv run --extra dev python scripts/generate_parity.py
git diff --exit-code -- tests/fixtures/parity.json
```

Do not change the oracle to make a Rust mismatch disappear. Record intentional behaviour changes in the OpenSpec change and add tests.

Normal tests use mocked HTTP servers. The ignored `discord_live` test writes one labelled message to the explicitly configured existing channel, reads it back, then removes only its own message. Run it only for authorised live validation.

```sh
cargo test --locked --test discord_live -- --ignored
```

Use conventional commits. Keep credentials and memory evidence outside Git. Production deployment remains gated on the complete memory test and GitOps checks.

Live verification bounds send, read-back and deletion to 30 seconds each (90 seconds total). Cleanup retains its own budget after a failed read. A cleanup timeout reports the exact returned message ID for manual removal.
