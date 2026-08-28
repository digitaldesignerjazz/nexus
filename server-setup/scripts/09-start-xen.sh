#!/usr/bin/env bash
# Xen Protocol 1.0 — start the technical-exploratory swarm agent.
# Runs on the Hannover host. Requires: yggdrasil up, control plane on :8787.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONF="${XEN_CONF:-$ROOT/configs/xen-protocol-1.0.yaml}"
CTRL="${NEXUS_CTRL:-http://127.0.0.1:8787}"

echo "=== Xen Protocol 1.0 ==="
echo "Config: $CONF"

if [ ! -f "$CONF" ]; then
  echo "FEHLER: $CONF fehlt."
  exit 1
fi

# 1) Mesh muss stehen — sonst kein Overlay für Xen.
if ! command -v yggdrasilctl >/dev/null 2>&1; then
  echo "yggdrasilctl nicht gefunden — Xen braucht den Yggdrasil-Daemon."
  exit 1
fi
PEER_COUNT=$(yggdrasilctl getPeers 2>/dev/null | grep -c 'Up' || true)
echo "Yggdrasil-Peers Up: ${PEER_COUNT:-0}"
if [ "${PEER_COUNT:-0}" -lt 1 ]; then
  echo "WARNUNG: keine Peers Up. Xen startet trotzdem (STANDBY)."
fi

# 2) Control Plane: Swarm-Schicht anwerfen.
if command -v curl >/dev/null 2>&1; then
  echo "→ POST $CTRL/swarm/spawn"
  curl -s -X POST "$CTRL/swarm/spawn" || echo "(Control Plane nicht erreichbar)"
  echo
else
  echo "curl fehlt — Swarm manuell über /swarm/spawn starten."
fi

# 3) Protokoll-Status schreiben.
STATUS_DIR="$ROOT/status"
mkdir -p "$STATUS_DIR"
cat > "$STATUS_DIR/xen_presence.json" <<EOF
{
  "protocol": "xen",
  "version": "1.0",
  "node_id": "xen-hannover-01",
  "status": "OPERATIONAL",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ygg_peers_up": ${PEER_COUNT:-0}
}
EOF
echo "Presence: $STATUS_DIR/xen_presence.json"
echo "Xen Protocol 1.0 — gestartet."
