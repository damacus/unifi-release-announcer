# Installation

The preferred runtime is the published non-root Linux container. Images support amd64 and arm64.

For a source build, install the toolchain pinned in `rust-toolchain.toml` through rustup:

```sh
cargo build --locked --release --bins
```

The executables are `target/release/unifi-release-announcer` and `target/release/release-parser`.

Install the pinned uv with `mise install uv`. Documentation uses Zensical and a locked Python environment: `uv run --locked --python 3.14 zensical build`. The application and memory acceptance tooling use Rust.

Use the pinned Rust toolchain locally for development. Production uses UID/GID 1000 and does not require a writable filesystem.
