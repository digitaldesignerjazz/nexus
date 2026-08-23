# Alias for Docker users (same content as Containerfile)
# nxmesh — Nexus Mesh Substrate (Noise + QUIC / libp2p)

FROM rust:1.75-bookworm AS builder

WORKDIR /build
COPY Cargo.toml ./
RUN mkdir src && echo "fn main() {}" > src/lib.rs && \
    cargo build --release 2>/dev/null || true
COPY src ./src
COPY examples ./examples
COPY Cargo.toml ./
RUN cargo build --release --example basic_node

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libssl3 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /build/target/release/examples/basic_node /app/nxmesh-node
VOLUME ["/data"]
ENV RUST_LOG=nxmesh=info,libp2p=info
ENV NXMESH_IDENTITY=/data/node-identity.key
ENTRYPOINT ["/app/nxmesh-node"]
