#!/usr/bin/env bash
# Nexus Bootstrap — legt data/logs/.env/vendor an. Kein Overlay, keine Secrets im Log.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib.sh"

ROOT="$(cd "$SELF/.." && pwd)"
cd "$ROOT"
assert_setup_root "$ROOT"

trap 'die "Bootstrap abgebrochen in Zeile $LINENO" 1' ERR

echo "=== Nexus Bootstrap ==="
echo "Root: $ROOT"

require_cmd python3
require_cmd git

mkdir -p data logs control/vendor || die "Kann data/logs/control/vendor nicht anlegen." 1

if [[ ! -f .env ]]; then
  [[ -f .env.example ]] || die ".env.example fehlt — Repo unvollständig." 3
  cp .env.example .env || die "Kopieren von .env.example nach .env fehlgeschlagen." 1
  chmod 600 .env || die "chmod 600 .env fehlgeschlagen." 1
  nexus_ok ".env angelegt (chmod 600) aus .env.example"
else
  nexus_ok ".env vorhanden — unangetastet"
  chmod 600 .env 2>/dev/null || nexus_warn "chmod 600 .env nicht möglich"
fi

vendor="$ROOT/control/vendor/nexus-python"
sibling_python="$(cd "$ROOT/.." && pwd)/python"

sync_python_vendor() {
  local src="$1"
  mkdir -p "$vendor"
  cp -a "$src"/. "$vendor"/ || die "Kopieren der Python-Referenz nach $vendor fehlgeschlagen." 1
}

if [[ ! -d "$vendor" ]] || [[ -z "$(ls -A "$vendor" 2>/dev/null || true)" ]]; then
  if [[ -d "$sibling_python" ]] && ls "$sibling_python"/*.py >/dev/null 2>&1; then
    nexus_log "Python-Referenz aus Sibling $sibling_python"
    sync_python_vendor "$sibling_python"
  else
    require_cmd git
    tmp="$(mktemp -d "${TMPDIR:-/tmp}/nexus-clone.XXXXXX")"
    cleanup_tmp() { rm -rf "$tmp"; }
    trap 'cleanup_tmp; die "Bootstrap abgebrochen in Zeile $LINENO" 1' ERR
    nexus_log "Klone Python-Referenz (depth 1) nach $tmp"
    if ! git clone --depth 1 https://github.com/digitaldesignerjazz/nexus.git "$tmp/repo"; then
      cleanup_tmp
      die "git clone digitaldesignerjazz/nexus fehlgeschlagen — Netz, Auth oder GitHub prüfen." 5
    fi
    if [[ ! -d "$tmp/repo/python" ]]; then
      cleanup_tmp
      die "Klon enthält kein python/ — falsches Repo oder unvollständiger Stand." 5
    fi
    sync_python_vendor "$tmp/repo/python"
    cleanup_tmp
    trap 'die "Bootstrap abgebrochen in Zeile $LINENO" 1' ERR
  fi
else
  nexus_ok "Python-Vendor bereits vorhanden: $vendor"
fi

shopt -s nullglob
scripts=(scripts/*.sh)
if ((${#scripts[@]} == 0)); then
  die "Keine scripts/*.sh gefunden." 3
fi
chmod +x scripts/*.sh || die "chmod +x scripts/*.sh fehlgeschlagen." 1
if [[ -f control/nexus_control.py ]]; then
  chmod +x control/nexus_control.py || nexus_warn "chmod +x control/nexus_control.py nicht möglich"
fi
shopt -u nullglob

nexus_ok "Bootstrap fertig."
echo "Start: bash scripts/02-start-control-plane.sh"
echo "Oder im Hintergrund: bash scripts/02-start-control-plane.sh --background"
exit 0
