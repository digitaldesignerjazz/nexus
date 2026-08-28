#!/usr/bin/env bash
# Nexus — backup.sh
# Reines Backup der laufenden Configs — OHNE Daemon-Neustart.
# Läuft NUR auf dem Hannover-Host.
#
# Usage:
#   cd nexus/server-setup
#   bash scripts/08-backup.sh
#
# Optional:
#   YGG_CONF=/etc/yggdrasil/yggdrasil.conf bash scripts/08-backup.sh
#   BACKUP_DIR=/mnt/nas/nexus-backups bash scripts/08-backup.sh
#   KEEP_DAYS=30 bash scripts/08-backup.sh
#
# Was gesichert wird:
#   - /etc/yggdrasil/yggdrasil.conf  ->  backups/yggdrasil.conf.<ts>
#   - server-setup/.env              ->  backups/.env.<ts>
#   - server-setup/configs/          ->  backups/configs.<ts>.tar.gz
#   - docker-compose.yml + systemd unit -> backups/
#
# Danach: Rotation — Backups älter als KEEP_DAYS (default 14) werden gelöscht.
#
# Hinweis: Dieses Skript startet KEINEN Daemon. Für Backup + Neustart in
# einem Rutsch: bash scripts/07-restart-backup.sh

set -euo pipefail

YGG_CONF="${YGG_CONF:-/etc/yggdrasil/yggdrasil.conf}"
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
TS="$(date +%Y%m%d-%H%M%S)"

echo "=== Nexus · backup ==="
echo "Zeit    : $(date -Iseconds)"
echo "Backup  : $BACKUP_DIR"
echo "Config  : $YGG_CONF"
echo "Rotation: >${KEEP_DAYS} Tage"
echo

mkdir -p "$BACKUP_DIR"
COPIED=0

backup_file() {
  local src="$1" label="$2"
  if [ -f "$src" ]; then
    cp -a "$src" "$BACKUP_DIR/${label}.$TS"
    echo "  ok  $src -> ${label}.$TS"
    COPIED=$((COPIED + 1))
  else
    echo "  --  $src (fehlt, übersprungen)"
  fi
}

echo "[1/4] Einzeldateien"
backup_file "$YGG_CONF" "yggdrasil.conf"
backup_file ".env" ".env"
backup_file "docker-compose.yml" "docker-compose.yml"
backup_file "systemd/nexus-control.service" "nexus-control.service"
echo

echo "[2/4] configs/ (tar.gz)"
if [ -d configs ]; then
  tar -czf "$BACKUP_DIR/configs.$TS.tar.gz" configs
  echo "  ok  configs/ -> configs.$TS.tar.gz"
  COPIED=$((COPIED + 1))
else
  echo "  --  configs/ (fehlt, übersprungen)"
fi
echo

echo "[3/4] Rotation"
DELETED=0
while IFS= read -r -d '' old; do
  rm -f "$old"
  DELETED=$((DELETED + 1))
done < <(find "$BACKUP_DIR" -type f -mtime +"$KEEP_DAYS" -print0 2>/dev/null)
if [ "$DELETED" -gt 0 ]; then
  echo "  $DELETED alte Datei(en) entfernt (>${KEEP_DAYS}d)"
else
  echo "  nichts zu entfernen"
fi
echo

echo "[4/4] Inventar"
mapfile -t ENTRIES < <(ls -1t "$BACKUP_DIR" 2>/dev/null | head -n 8)
if [ "${#ENTRIES[@]}" -eq 0 ]; then
  echo "  (Backup-Verzeichnis leer)"
else
  for e in "${ENTRIES[@]}"; do
    echo "  $e"
  done
fi
echo

echo "=== $COPIED Objekt(e) gesichert. Daemon unberührt. ==="
