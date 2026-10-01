# Installation

The preferred runtime is the published non-root Linux container. Images support amd64 and arm64.

For a source build, install the toolchain pinned in `rust-toolchain.toml` through rustup:

```sh
cargo build --locked --release --bins
```

The executables are `target/release/unifi-release-announcer` and `target/release/release-parser`.

Install the pinned mdBook with `mise install mdbook` to build or serve documentation. Development and operational tooling use Rust.

Use the pinned Rust toolchain locally for development. Production uses UID/GID 1000 and does not require a writable filesystem.
