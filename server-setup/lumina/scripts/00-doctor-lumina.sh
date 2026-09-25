#!/usr/bin/env bash
# Lumina Doctor — prüft Werkzeuge für den Nexus→LuminaCyberspace-Start.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib-lumina.sh"

trap 'lumina_err "Doctor abgebrochen in Zeile $LINENO"; exit 1' ERR

PKG="$(cd "$SELF/.." && pwd)"
assert_lumina_root "$PKG"
load_dotenv "$PKG/.env"

echo "=== Lumina Doctor (nexus-lumina $(cat "$PKG/VERSION")) ==="
echo "Pkg : $PKG"
echo "Host: $(hostname)  User: ${USER:-unknown}"
echo "Zeit: $(date -Iseconds)"
echo

required_missing=0
optional_missing=0

check_required() {
  local name="$1" cmd="$2"
  if have "$cmd"; then
    lumina_ok "$name ($cmd → $(command -v "$cmd"))"
  else
    lumina_err "$name fehlt ($cmd) — Pflicht"
    required_missing=$((required_missing + 1))
  fi
}

check_optional() {
  local name="$1" cmd="$2"
  if have "$cmd"; then
    lumina_ok "$name ($cmd → $(command -v "$cmd"))"
  else
    lumina_warn "$name fehlt ($cmd) — optional"
    optional_missing=$((optional_missing + 1))
  fi
}

check_required "Python 3" python3
check_required "curl" curl
check_required "tar" tar
check_required "sha256sum" sha256sum
check_optional "Git" git
check_optional "Yggdrasil (mesh)" yggdrasil
check_optional "yggdrasilctl" yggdrasilctl
check_optional "Docker (Hannover extras)" docker
check_optional "ss (port check)" ss

PY="$(python_bin)"
if "$PY" - <<'PY'
import sys
ver = sys.version_info
print(f"[OK] Python runtime {sys.version.split()[0]} via {sys.executable}")
if ver < (3, 9):
    raise SystemExit(4)
try:
    import nacl  # noqa: F401
    print("[OK] PyNaCl verfügbar (Overlay möglich)")
except ImportError:
    print("[WARN] PyNaCl fehlt — Overlay-Prototyp wird übersprungen (pip install pynacl)")
PY
then
  :
else
  lumina_err "Python >= 3.9 erforderlich"
  required_missing=$((required_missing + 1))
fi

echo
if [[ -f "$PKG/pins/SNAPSHOT_URL.txt" ]]; then
  lumina_ok "Snapshot-Pin: $(tr -d '\n' < "$PKG/pins/SNAPSHOT_URL.txt")"
else
  lumina_err "pins/SNAPSHOT_URL.txt fehlt"
  required_missing=$((required_missing + 1))
fi

CTRL="${NEXUS_CONTROL_URL:-http://127.0.0.1:8787}"
if have curl; then
  if curl -fsS --max-time 2 "$CTRL/health" >/dev/null 2>&1; then
    lumina_ok "Control Plane erreichbar ($CTRL/health)"
  else
    lumina_warn "Control Plane nicht erreichbar unter $CTRL — Start braucht sie nicht (Skript startet Orchestrator direkt)"
  fi
fi

echo
echo "Ehrlich alpha.2:"
echo "  • Startet: nexus_orchestrator.py + optional Overlay-Prototyp + optional yggdrasil"
echo "  • Startet NICHT (ohne ENABLE_HANNOVER_EXTRAS=1): onyx-listen, actions-runner, dockerd"
echo "  • Control Plane :8787 spawnt weiterhin keine Prozesse — Hook ist dünn/optional"
echo

if (( required_missing > 0 )); then
  lumina_err "Doctor FEHLGESCHLAGEN — $required_missing Pflichtlücke(n), $optional_missing optional fehlend."
  exit 2
fi

lumina_ok "Doctor bestanden ($optional_missing optionale Lücken)."
echo "Nächste Schritte: bash scripts/01-fetch-snapshot.sh"
exit 0
