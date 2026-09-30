#!/usr/bin/env bash
# Xara Prototype 1.0 — start the experimental overlay agent.
# Runs on the Hannover host. Requires: Xen substrate up (09-start-xen.sh).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONF="${XARA_CONF:-$ROOT/configs/xara-prototype-1.0.yaml}"
CTRL="${NEXUS_CTRL:-http://127.0.0.1:8787}"
XEN_PRESENCE="$ROOT/status/xen_presence.json"

echo "=== Xara Prototype 1.0 ==="
echo "Config: $CONF"

if [ ! -f "$CONF" ]; then
  echo "FEHLER: $CONF fehlt."
  exit 1
fi

# 1) Xen-Substrat muss stehen — Xara erbt, es baut nichts Eigenes.
if [ ! -f "$XEN_PRESENCE" ]; then
  echo "WARNUNG: Xen-Presence fehlt ($XEN_PRESENCE)."
  echo "         Xara startet trotzdem (STANDBY) — ohne Substrat kein Overlay."
else
  echo "Xen-Substrat: $(grep -o '"status": "[^"]*"' "$XEN_PRESENCE" | head -1)"
fi

# 2) Yggdrasil-Peers als Gesundheitscheck.
if command -v yggdrasilctl >/dev/null 2>&1; then
  PEER_COUNT=$(yggdrasilctl getPeers 2>/dev/null | grep -c 'Up' || true)
  echo "Yggdrasil-Peers Up: ${PEER_COUNT:-0}"
  if [ "${PEER_COUNT:-0}" -lt 1 ]; then
    echo "WARNUNG: keine Peers Up. Xara bleibt STANDBY."
  fi
else
  echo "yggdrasilctl nicht gefunden — Xara braucht den Yggdrasil-Daemon."
  exit 1
fi

# 3) Control Plane: Swarm-Schicht (Xara als experimenteller Agent).
if command -v curl >/dev/null 2>&1; then
  echo "→ POST $CTRL/swarm/spawn (xara)"
  curl -s -X POST "$CTRL/swarm/spawn" \
    -H 'Content-Type: application/json' \
    -d '{"agent":"xara","version":"1.0"}' || echo "(Control Plane nicht erreichbar)"
  echo
else
  echo "curl fehlt — Swarm manuell über /swarm/spawn starten."
fi

# 4) Prototype-Status schreiben.
STATUS_DIR="$ROOT/status"
mkdir -p "$STATUS_DIR"
cat > "$STATUS_DIR/xara_presence.json" <<EOF
{
  "prototype": "xara",
  "version": "1.0",
  "node_id": "xara-hannover-01",
  "status": "STANDBY",
  "maturity": "experimental",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ygg_peers_up": ${PEER_COUNT:-0},
  "substrate": "xen-protocol-1.0"
}
EOF
echo "Presence: $STATUS_DIR/xara_presence.json"
echo "Xara Prototype 1.0 — gestartet (STANDBY)."
