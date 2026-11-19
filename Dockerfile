# syntax=docker/dockerfile:1
FROM rust:1.100.0-alpine@sha256:8d0e82abfdf9a38071e07cabc5afba4ddbe077631a80e4e742a760c38beadc33 AS builder
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
