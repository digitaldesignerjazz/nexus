#!/usr/bin/env bash
set -euo pipefail
echo "=== Yggdrasil Hannover Node ==="
if ! command -v yggdrasil >/dev/null 2>&1; then
  echo "Yggdrasil ist nicht installiert."
  echo "Debian/Ubuntu: sudo apt install yggdrasil"
  echo "Oder: https://yggdrasil-network.github.io/installation.html"
  exit 1
fi
CONF="${YGGDRASIL_CONF:-$HOME/.config/yggdrasil/yggdrasil.conf}"
mkdir -p "$(dirname "$CONF")"
if [ ! -f "$CONF" ]; then
  echo "→ Erzeuge frische Config (Private Key bleibt lokal)"
  yggdrasil -genconf > "$CONF"
  chmod 600 "$CONF"
  echo "Config: $CONF"
  echo "Öffentliche Adresse:"
  yggdrasil -useconffile "$CONF" -address || true
else
  echo "Bestehende Config: $CONF"
fi
echo
echo "Start (User-Session):"
echo "  yggdrasil -useconffile $CONF"
echo "oder systemd:"
echo "  sudo systemctl enable --now yggdrasil"
