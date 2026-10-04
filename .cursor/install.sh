#!/usr/bin/env bash
# Nexus Cloud Agent environment bootstrap.
# Idempotent: safe to re-run and to run against a warm snapshot.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Python reference-layer dependencies (networkx, matplotlib, numpy) + dev tools"
# Deps land in the invoking user's site (~/.local); --break-system-packages keeps
# the system python3 usable directly, which the server-setup scripts rely on.
python3 -m pip install --break-system-packages --upgrade pip
python3 -m pip install --break-system-packages -r requirements.txt pytest ruff

echo "==> Rust toolchain"
# The base image ships Rust 1.83, but the dependency tree (via clap_builder)
# pulls crates that require the edition2024 cargo feature (Rust >= 1.85).
# Match CI's `rust-toolchain@stable` by installing the current stable toolchain.
rustup toolchain install stable --profile minimal
rustup default stable
rustup component add clippy rustfmt

echo "==> Server-setup control plane bootstrap (.env, data/, logs/, python vendor)"
bash server-setup/scripts/01-bootstrap.sh

echo "==> Warm Rust build caches (orchestration core + mesh substrate)"
cargo build --manifest-path orchestration/core/Cargo.toml
cargo build --manifest-path mesh/noise-quic/Cargo.toml

echo "==> Nexus environment ready"
