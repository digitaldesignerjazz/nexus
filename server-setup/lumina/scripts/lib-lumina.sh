#!/usr/bin/env bash
# Shared helpers for Nexus→LuminaCyberspace package scripts. Source, do not exec.

lumina_log() { printf '[lumina] %s\n' "$*"; }
lumina_ok()  { printf '[OK] %s\n' "$*"; }
lumina_warn(){ printf '[WARN] %s\n' "$*" >&2; }
lumina_err() { printf '[ERR] %s\n' "$*" >&2; }

die() {
  lumina_err "${1:-unbekannter Fehler}"
  exit "${2:-1}"
}

have() { command -v "$1" >/dev/null 2>&1; }

require_cmd() {
  have "$1" || die "Pflichtbefehl fehlt: $1 — bitte installieren und PATH prüfen." 2
}

# KEY=value loader that does not execute values with spaces
load_dotenv() {
  local file="$1" line key val
  [[ -n "$file" && -f "$file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" == *"="* ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    if [[ "$val" =~ ^\".*\"$ || "$val" =~ ^\'.*\'$ ]]; then
      val="${val:1:${#val}-2}"
    fi
    printf -v "$key" '%s' "$val"
    export "$key"
  done < "$file"
}

assert_lumina_root() {
  local root="$1"
  [[ -n "$root" && -d "$root" ]] || die "LUMINA_PKG ungültig: ${root:-leer}" 3
  [[ -f "$root/VERSION" ]] || die "VERSION fehlt unter $root" 3
  [[ -d "$root/scripts" ]] || die "Kein scripts/ unter $root" 3
  [[ -f "$root/pins/SNAPSHOT_URL.txt" ]] || die "pins/SNAPSHOT_URL.txt fehlt unter $root" 3
}

pkg_root_from_scripts() {
  # SELF is scripts/; package root is parent
  cd "$(dirname "$1")/.." && pwd
}

ensure_runtime() {
  local root="$1"
  mkdir -p "$root/runtime"/{downloads,stack,keys/overlay,keys/ygg,status,logs}
}

running_pat() {
  pgrep -f "$1" >/dev/null 2>&1
}

write_status() {
  local status_dir="$1" name="$2" pid="$3" extra="${4:-}"
  mkdir -p "$status_dir"
  {
    echo "name=$name"
    echo "pid=$pid"
    echo "ts=$(date -Iseconds)"
    [[ -n "$extra" ]] && echo "$extra"
  } > "$status_dir/${name}.status"
  if [[ -n "$pid" && "$pid" != "0" ]]; then
    echo "$pid" > "$status_dir/${name}.pid"
  fi
}

python_bin() {
  if [[ -n "${LUMINA_PYTHON:-}" ]] && have "$LUMINA_PYTHON"; then
    echo "$LUMINA_PYTHON"
    return
  fi
  if [[ -x /workspace/lumina-venv/bin/python ]]; then
    echo /workspace/lumina-venv/bin/python
    return
  fi
  echo python3
}
