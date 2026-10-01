# UniFi Release Announcer

An HTTP-only Rust service that announces the latest eligible UniFi releases in Discord text channels or forums. It polls every ten minutes and uses existing Discord history to suppress duplicate release URLs.

The bot does not connect to the Discord Gateway and can appear offline while posting successfully.

## Run

Set `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` and optionally `TAGS`. The tag default is `unifi-protect`.

```sh
cargo run --locked --release -- --once --dry-run
cargo run --locked --release
```

Or create a private `.env` file and use `docker compose up --build announcer`.

## Behaviour

Application tags such as Network, Protect and Drive require the product name and “Application” in the title. Other tags use the preserved mobile/advisory deny-list. The newest eligible item per tag is selected from a 50-item GraphQL response. Existing announcement text and Markdown escaping match Python 0.2.14.

The service reads 200 recent text messages, or active forum starters and 50 archived forum starters. If required history cannot be read, it skips posting. Duplicate URLs within a poll are sent once. Uncertain sends are not blindly retried.

These bounded history windows do not guarantee exactly-once delivery for old announcements. The process remembers up to 200 recently seen or uncertain URLs; that memory is lost on restart.

## Development

```sh
cargo fmt --all --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
uv run --locked --python 3.14 zensical build
```

Captured compatibility fixtures preserve the legacy behaviour. The former implementation is available in Git history. Documentation uses Zensical; runtime containers contain only the two statically linked Rust executables.

Use `release-parser <json-file> --tags unifi-protect --stage GA --limit 1` to filter a saved GraphQL response. It prints one pretty-printed JSON object per release.

See [configuration](docs/configuration.md), [migration and deployment](docs/deployment.md) and [contributing](docs/contributing.md).

The runtime image uses FROM scratch with static musl binaries and UID 1000. CI runs both amd64 and arm64 images and enforces a 32 MiB image-size limit. Rust formatting, Clippy, tests and release builds run in a dedicated CI job. Renovate maintains Cargo dependencies and the pinned toolchain; minor updates auto-merge only after passing CI and a minimum release age of 24 hours. Updates without release timestamps stay pending.
