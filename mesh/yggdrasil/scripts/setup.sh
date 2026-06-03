#!/bin/bash
#
# Nexus Yggdrasil Quick Setup Script
# Automates the initial configuration and launch of a Yggdrasil mesh node
# as part of the Nexus ecosystem.
#
# Usage (from repo root):
#   chmod +x mesh/yggdrasil/scripts/setup.sh
#   ./mesh/yggdrasil/scripts/setup.sh
#
# This script:
#   - Creates the config directory
#   - Copies the example config if none exists
#   - Launches the Docker Compose stack
#   - Tails the logs
#
# After first run, edit mesh/yggdrasil/config/yggdrasil.conf for your Peers,
# AllowedPublicKeys (strongly recommended for private Nexus meshes),
# and MulticastInterfaces (for hardware node discovery).
#
# Then re-run or manually restart the container.

set -e

echo "========================================"
echo "  Nexus Yggdrasil Mesh Node Setup"
echo "========================================"
echo

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
YGG_DIR="${REPO_ROOT}/mesh/yggdrasil"
CONFIG_DIR="${YGG_DIR}/config"
EXAMPLE_CONF="${YGG_DIR}/yggdrasil.example.conf"
TARGET_CONF="${CONFIG_DIR}/yggdrasil.conf"
COMPOSE_FILE="${YGG_DIR}/docker-compose.yml"

# Ensure we are in the right place
if [ ! -f "${COMPOSE_FILE}" ]; then
  echo "Error: Could not find docker-compose.yml at ${COMPOSE_FILE}"
  echo "Please run this script from the Nexus repository root."
  exit 1
fi

# 1. Create config directory
echo "[1/4] Creating config directory..."
mkdir -p "${CONFIG_DIR}"

# 2. Copy example config if it doesn't exist
if [ ! -f "${TARGET_CONF}" ]; then
  echo "[2/4] No existing config found. Copying example..."
  cp "${EXAMPLE_CONF}" "${TARGET_CONF}"
  echo "   -> Created ${TARGET_CONF}"
  echo "   IMPORTANT: Edit this file before or after first launch:"
  echo "      - Add trusted Peers (or use public peers for testing)"
  echo "      - Set AllowedPublicKeys for private Nexus meshes (recommended)"
  echo "      - Enable MulticastInterfaces for LAN hardware discovery (Tenda Nova etc.)"
  echo "      - Customize NodeInfo if desired"
else
  echo "[2/4] Existing config found at ${TARGET_CONF} — skipping copy."
fi

# 3. Launch Docker Compose
echo "[3/4] Starting Yggdrasil container..."
cd "${YGG_DIR}"
docker compose up -d

echo

echo "[4/4] Yggdrasil node is starting."
echo "To follow logs: docker compose logs -f yggdrasil"
echo "To check status inside container:"
echo "  docker compose exec yggdrasil yggdrasil -useconffile /etc/yggdrasil/yggdrasil.conf -status"
echo

echo "After editing the config, restart with: docker compose restart yggdrasil"
echo

echo "========================================"
echo "Setup complete. Your Nexus Yggdrasil node is running."
echo "Next: Configure QNET integration, AI agents, or hardware peers."
echo "See docs/yggdrasil-mesh-integration.md for full details."
echo "========================================"

# Optional: tail logs automatically (comment out if you prefer not to)
echo "Tailing logs (press Ctrl+C to stop)..."
docker compose logs -f yggdrasil