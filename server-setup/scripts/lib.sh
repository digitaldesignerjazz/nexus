#!/usr/bin/env bash
# Shared helpers for Nexus server-setup scripts. Source, do not exec.

nexus_log() { printf '[nexus] %s\n' "$*"; }
nexus_ok()  { printf '[OK] %s\n' "$*"; }
nexus_warn(){ printf '[WARN] %s\n' "$*" >&2; }
nexus_err() { printf '[ERR] %s\n' "$*" >&2; }

die() {
  nexus_err "${1:-unbekannter Fehler}"
  exit "${2:-1}"
}

have() { command -v "$1" >/dev/null 2>&1; }

require_cmd() {
  have "$1" || die "Pflichtbefehl fehlt: $1 — bitte installieren und PATH prüfen." 2
}

is_int() { [[ "${1:-}" =~ ^[0-9]+$ ]]; }

port_in_use() {
  local port="$1"
  if have ss; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]${port}$"
    return $?
  fi
  if have lsof; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

assert_setup_root() {
  local root="$1"
  [[ -n "$root" && -d "$root" ]] || die "SETUP_ROOT ungültig: ${root:-leer}" 3
  [[ -d "$root/scripts" ]] || die "Kein scripts/ unter $root — falsches Verzeichnis?" 3
  [[ -f "$root/control/nexus_control.py" ]] || die "control/nexus_control.py fehlt unter $root" 3
  [[ -f "$root/.env.example" ]] || die ".env.example fehlt unter $root" 3
}
