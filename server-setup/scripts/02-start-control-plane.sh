#!/usr/bin/env bash
# Startet die Nexus Control Plane auf 127.0.0.1:8787 (Default).
# Usage:
#   bash scripts/02-start-control-plane.sh
#   bash scripts/02-start-control-plane.sh --background
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib.sh"

ROOT="$(cd "$SELF/.." && pwd)"
cd "$ROOT"
assert_setup_root "$ROOT"

BACKGROUND=0
for arg in "$@"; do
  case "$arg" in
    --background|-d|--daemon) BACKGROUND=1 ;;
    -h|--help)
      echo "Usage: $0 [--background]"
      exit 0
      ;;
    *)
      die "Unbekanntes Argument: $arg" 2
      ;;
  esac
done

require_cmd python3
[[ -f "$ROOT/control/nexus_control.py" ]] || die "control/nexus_control.py fehlt." 3

if [[ -f .env ]]; then
  load_dotenv "$ROOT/.env"
else
  nexus_warn ".env fehlt — Defaults. Erst bash scripts/01-bootstrap.sh ausführen."
fi

export NEXUS_BIND="${NEXUS_BIND:-127.0.0.1}"
export NEXUS_PORT="${NEXUS_PORT:-8787}"
export NEXUS_DATA_DIR="${NEXUS_DATA_DIR:-$ROOT/data}"
export NEXUS_LOG_DIR="${NEXUS_LOG_DIR:-$ROOT/logs}"

is_int "$NEXUS_PORT" || die "NEXUS_PORT ist keine Zahl: $NEXUS_PORT" 2
mkdir -p "$NEXUS_DATA_DIR" "$NEXUS_LOG_DIR" || die "Kann data/logs nicht anlegen." 1

PIDFILE="$NEXUS_LOG_DIR/control-plane.pid"
OUTLOG="$NEXUS_LOG_DIR/control-plane.out"

if port_in_use "$NEXUS_PORT"; then
  nexus_err "Port $NEXUS_PORT ist belegt."
  if have ss; then ss -ltnp | grep -E "[:.]${NEXUS_PORT}\\b" || true; fi
  if [[ -f "$PIDFILE" ]]; then
    nexus_err "PID-Datei: $PIDFILE ($(cat "$PIDFILE" 2>/dev/null || echo '?'))"
  fi
  die "Alten Prozess beenden oder NEXUS_PORT ändern." 6
fi

echo "Starte Nexus Control Plane auf http://${NEXUS_BIND}:${NEXUS_PORT}"

wait_health() {
  local url="http://${NEXUS_BIND}:${NEXUS_PORT}/health"
  local i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if have curl && curl -fsS --max-time 1 "$url" >/dev/null 2>&1; then
      nexus_ok "Health antwortet ($url)"
      return 0
    fi
    sleep 0.3
  done
  return 1
}

if (( BACKGROUND == 1 )); then
  nohup python3 "$ROOT/control/nexus_control.py" >>"$OUTLOG" 2>&1 &
  echo $! >"$PIDFILE"
  nexus_log "PID $(cat "$PIDFILE")  log $OUTLOG"
  if wait_health; then
    if have curl; then curl -sS "http://${NEXUS_BIND}:${NEXUS_PORT}/health"; echo; fi
    exit 0
  fi
  nexus_err "Control Plane startete nicht rechtzeitig."
  tail -n 40 "$OUTLOG" >&2 || true
  exit 7
fi

echo $$ >"$PIDFILE"
exec python3 "$ROOT/control/nexus_control.py"
