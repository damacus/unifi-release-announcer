# syntax=docker/dockerfile:1
FROM rust:1.98.1-alpine@sha256:7cc1c22d77d9432f7fe012a70e6d3e555af54c2a6832700ed7d553f1769ae89f AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml Cargo.lock rust-toolchain.toml ./
COPY src/ src/
# An explicit target keeps static CRT flags away from host procedural macros.
RUN rust_target="$(rustc -vV | sed -n 's/^host: //p')" \
    && RUSTFLAGS="-C target-feature=+crt-static" cargo build --release --locked --bins --target "$rust_target" \
    && mkdir /out \
    && cp "target/$rust_target/release/unifi-release-announcer" "target/$rust_target/release/release-parser" /out/

FROM scratch AS runtime
COPY --from=builder /out/ /usr/local/bin/
USER 1000:1000
ENTRYPOINT ["/usr/local/bin/unifi-release-announcer"]
