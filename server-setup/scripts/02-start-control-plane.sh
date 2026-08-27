#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
set -a
[ -f .env ] && source .env
set +a
export NEXUS_BIND="${NEXUS_BIND:-127.0.0.1}"
export NEXUS_PORT="${NEXUS_PORT:-8787}"
export NEXUS_DATA_DIR="${NEXUS_DATA_DIR:-$ROOT/data}"
export NEXUS_LOG_DIR="${NEXUS_LOG_DIR:-$ROOT/logs}"
mkdir -p "$NEXUS_DATA_DIR" "$NEXUS_LOG_DIR"
echo "Starte Nexus Control Plane auf http://${NEXUS_BIND}:${NEXUS_PORT}"
exec python3 "$ROOT/control/nexus_control.py"
