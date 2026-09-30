#!/usr/bin/env bash
# Nexus — restart-backup.sh
# Morgen-Routine: sicheres Backup der laufenden Configs, dann Neustart.
# Läuft NUR auf dem Hannover-Host.
#
# Usage:
#   cd nexus/server-setup
#   bash scripts/07-restart-backup.sh
#
# Optional:
#   YGG_CONF=/etc/yggdrasil/yggdrasil.conf bash scripts/07-restart-backup.sh
#   SKIP_BACKUP=1 bash scripts/07-restart-backup.sh   # nur Neustart
#   SKIP_RESTART=1 bash scripts/07-restart-backup.sh  # nur Backup
#
# Was gesichert wird:
#   - /etc/yggdrasil/yggdrasil.conf  ->  backups/yggdrasil.conf.<ts>
#   - server-setup/.env              ->  backups/.env.<ts>
#   - server-setup/configs/          ->  backups/configs.<ts>.tar.gz
#   - systemd unit + docker-compose  ->  backups/
#
# Danach: systemctl restart yggdrasil, Status, Lumina-Ping.

set -euo pipefail

YGG_CONF="${YGG_CONF:-/etc/yggdrasil/yggdrasil.conf}"
SKIP_BACKUP="${SKIP_BACKUP:-0}"
SKIP_RESTART="${SKIP_RESTART:-0}"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups}"
LUMINA_IPV6="201:e68a:5e25:166f:4bf9:7b75:5d76:5c2b"

echo "=== Nexus · restart-backup ==="
echo "Zeit   : $(date -Iseconds)"
echo "Backup : $BACKUP_DIR"
echo "Config : $YGG_CONF"
echo

mkdir -p "$BACKUP_DIR"

if [ "$SKIP_BACKUP" != "1" ]; then
  echo "[1/5] Backup der Configs"
  if [ -f "$YGG_CONF" ]; then
    cp -a "$YGG_CONF" "$BACKUP_DIR/yggdrasil.conf.$TS"
    echo "      $YGG_CONF -> yggdrasil.conf.$TS"
  else
    echo "      (Yggdrasil-Config fehlt — übersprungen)"
  fi

  if [ -f .env ]; then
    cp -a .env "$BACKUP_DIR/.env.$TS"
    echo "      .env -> .env.$TS"
  fi

  if [ -d configs ]; then
    tar -czf "$BACKUP_DIR/configs.$TS.tar.gz" configs
    echo "      configs/ -> configs.$TS.tar.gz"
  fi

  if [ -f docker-compose.yml ]; then
    cp -a docker-compose.yml "$BACKUP_DIR/docker-compose.yml.$TS"
  fi
  if [ -f systemd/nexus-control.service ]; then
    cp -a systemd/nexus-control.service "$BACKUP_DIR/nexus-control.service.$TS"
  fi

  # Alte Backups älter als 14 Tage entfernen
  find "$BACKUP_DIR" -type f -mtime +14 -delete 2>/dev/null || true
  echo "      alte Backups (>14d) bereinigt"
  echo
else
  echo "[1/5] SKIP_BACKUP=1 — kein Backup."
  echo
fi

if [ "$SKIP_RESTART" != "1" ]; then
  echo "[2/5] systemctl restart yggdrasil"
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl restart yggdrasil
    echo "      Daemon neu — warte 3s"
    sleep 3
  else
    echo "      kein systemctl — bitte manuell neu starten."
  fi
else
  echo "[2/5] SKIP_RESTART=1 — Daemon bleibt."
fi

echo "[3/5] yggdrasilctl getSelf"
if command -v yggdrasilctl >/dev/null 2>&1; then
  sudo yggdrasilctl getSelf || true
else
  echo "      yggdrasilctl nicht gefunden."
fi
echo

echo "[4/5] yggdrasilctl getPeers"
if command -v yggdrasilctl >/dev/null 2>&1; then
  sudo yggdrasilctl getPeers || true
else
  echo "      yggdrasilctl nicht gefunden."
fi
echo

echo "[5/5] ping6 -c 3 $LUMINA_IPV6"
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
  echo "      ping6 nicht gefunden."
  exit 1
fi

echo
echo "=== Backup liegt in $BACKUP_DIR. Hof ist wach. ==="
