#!/usr/bin/env bash
# Nexus Doctor — prüft Pflicht- und Optional-Werkzeuge, bricht bei Pflichtlücken ab.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib.sh"

trap 'nexus_err "Doctor abgebrochen in Zeile $LINENO"; exit 1' ERR

ROOT="$(cd "$SELF/.." && pwd)"
echo "=== Nexus Doctor ==="
echo "Root: $ROOT"
echo "CWD : $(pwd)"
echo "Host: $(hostname)  User: ${USER:-unknown}"
echo

required_missing=0
optional_missing=0

check_required() {
  local name="$1" cmd="$2"
  if have "$cmd"; then
    nexus_ok "$name ($cmd → $(command -v "$cmd"))"
  else
    nexus_err "$name fehlt ($cmd) — Pflicht"
    required_missing=$((required_missing + 1))
  fi
}

check_optional() {
  local name="$1" cmd="$2"
  if have "$cmd"; then
    nexus_ok "$name ($cmd → $(command -v "$cmd"))"
  else
    nexus_warn "$name fehlt ($cmd) — optional"
    optional_missing=$((optional_missing + 1))
  fi
}

if [[ ! -f "$ROOT/control/nexus_control.py" ]]; then
  nexus_err "Dieses Skript muss aus einem vollständigen server-setup laufen."
  nexus_err "Gefundenes Root: $ROOT"
  nexus_err "Tipp: git clone https://github.com/digitaldesignerjazz/nexus.git ~/nexus-hub"
  nexus_err "      cd ~/nexus-hub/server-setup && bash scripts/00-doctor.sh"
  exit 3
fi

check_required "Python 3" python3
check_required "Git" git
check_optional "Go (go-nexus CLI)" go
check_optional "Docker (compose stack)" docker
check_optional "Yggdrasil (mesh companion)" yggdrasil
check_optional "Cargo/Rust (Grok Launcher)" cargo

if have python3; then
  if ! python3 - <<'PY'
import sys
ver = sys.version_info
print(f"[OK] Python runtime {sys.version.split()[0]}")
if ver < (3, 9):
    raise SystemExit(4)
PY
  then
    nexus_err "Python >= 3.9 erforderlich"
    required_missing=$((required_missing + 1))
  fi
fi

echo
if [[ -d "$HOME/nexus" && ! -d "$HOME/nexus/server-setup" ]]; then
  nexus_warn "~/nexus existiert, enthält aber kein server-setup — nicht überschreiben."
  nexus_warn "Earth-Node-Hub: ~/nexus-hub  (bash scripts/earth-node-bootstrap.sh)"
fi

if have ss || have lsof; then
  if port_in_use 8787; then
    nexus_warn "Port 8787 ist bereits belegt — 02-start wird ablehnen, bis der alte Prozess weg ist."
  else
    nexus_ok "Port 8787 frei"
  fi
fi

echo
if (( required_missing > 0 )); then
  nexus_err "Doctor FEHLGESCHLAGEN — $required_missing Pflichtlücke(n), $optional_missing optional fehlend."
  echo "Nächste Schritte: fehlende Pflichtpakete installieren, dann erneut doctor."
  exit 2
fi

nexus_ok "Doctor bestanden ($optional_missing optionale Lücken)."
echo "Nächste Schritte: bash scripts/01-bootstrap.sh"
exit 0
