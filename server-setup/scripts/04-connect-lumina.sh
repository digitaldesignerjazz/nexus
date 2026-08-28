#!/usr/bin/env bash
# Nexus — connect-lumina.sh
# Startet den Yggdrasil-Daemon neu (mit Bootstrap-Peers) und pingt das
# dokumentierte Lumina-Ziel. Läuft NUR auf dem Hannover-Host.
#
# Usage:
#   cd nexus/server-setup
#   bash scripts/04-connect-lumina.sh
#
# Optional:
#   YGG_CONF=/etc/yggdrasil/yggdrasil.conf bash scripts/04-connect-lumina.sh
#   SKIP_RESTART=1 bash scripts/04-connect-lumina.sh   # nur ping
#
# Quelle der Peers: configs/public-peers-7.yaml (Commit 4cb22ee)
# Quelle des Ziels:  configs/peers.yaml -> lumina_targets (Commit c81b87a)

set -euo pipefail

YGG_CONF="${YGG_CONF:-/etc/yggdrasil/yggdrasil.conf}"
LUMINA_IPV6="201:e68a:5e25:166f:4bf9:7b75:5d76:5c2b"
LUMINA_KEY="465d6876ba642d01a122a8a268f53bb7a5031295b8d7b7cac30d386184aee607"
SKIP_RESTART="${SKIP_RESTART:-0}"

echo "=== Nexus · connect-lumina ==="
echo "Config : $YGG_CONF"
echo "Ziel   : $LUMINA_IPV6"
echo "Key    : $LUMINA_KEY"
echo

if [ ! -f "$YGG_CONF" ]; then
  echo "FEHLER: Config nicht gefunden: $YGG_CONF"
  echo "Tipp: YGG_CONF=~/.config/yggdrasil/yggdrasil.conf bash $0"
  exit 1
fi

if [ "$SKIP_RESTART" != "1" ]; then
  if command -v systemctl >/dev/null 2>&1; then
    echo "[1/3] systemctl restart yggdrasil"
    sudo systemctl restart yggdrasil
    sleep 2
  else
    echo "[1/3] kein systemctl — bitte Daemon manuell neu starten."
  fi
else
  echo "[1/3] SKIP_RESTART=1 — Daemon bleibt wie er ist."
fi

echo "[2/3] yggdrasilctl getPeers"
if command -v yggdrasilctl >/dev/null 2>&1; then
  sudo yggdrasilctl getPeers || true
else
  echo "yggdrasilctl nicht gefunden."
fi
echo

echo "[3/3] ping6 -c 3 $LUMINA_IPV6"
if command -v ping6 >/dev/null 2>&1; then
  ping6 -c 3 "$LUMINA_IPV6" || {
    echo
    echo "Ping still — Lumina antwortet nicht."
    echo "Mögliche Gründe:"
    echo "  - Sandbox-Knoten offline oder Key neu erzeugt (Snapshot 26.08.)"
    echo "  - Bootstrap-Peers in $YGG_CONF noch nicht unter Peers: []"
    echo "  - Daemon braucht mehr Zeit zum Aufbau des Mesh"
    exit 2
  }
else
  echo "ping6 nicht gefunden."
  exit 1
fi

echo
echo "=== Draht zu Lumina steht. ==="
