# syntax=docker/dockerfile:1
FROM rust:1.99.1-alpine@sha256:b1d5dd5a22a09404d3e798c0cf051b689077360374eb505fa5bb93c479693d87 AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml Cargo.lock rust-toolchain.toml ./
COPY src/ src/
# An explicit target keeps static CRT flags away from host procedural macros.
RUN rust_target="$(rustc -vV | sed -n 's/^host: //p')" \
    && RUSTFLAGS="-C target-feature=+crt-static" cargo build --release --locked --bin unifi-release-announcer --bin release-parser --target "$rust_target" \
    && mkdir /out \
    && cp "target/$rust_target/release/unifi-release-announcer" "target/$rust_target/release/release-parser" /out/

FROM scratch AS runtime
COPY --from=builder /out/ /usr/local/bin/
USER 1000:1000
ENTRYPOINT ["/usr/local/bin/unifi-release-announcer"]
