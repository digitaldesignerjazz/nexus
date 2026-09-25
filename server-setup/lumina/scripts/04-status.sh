#!/usr/bin/env bash
# Show LuminaCyberspace runtime status / PIDs / optional control-plane health.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib-lumina.sh"

PKG="$(cd "$SELF/.." && pwd)"
assert_lumina_root "$PKG"
load_dotenv "$PKG/.env"
STATUS="$PKG/runtime/status"
CTRL="${NEXUS_CONTROL_URL:-http://127.0.0.1:8787}"

echo "=== Lumina · status (nexus-lumina $(cat "$PKG/VERSION")) ==="
echo "Pkg : $PKG"
echo "Zeit: $(date -Iseconds)"
echo

check_one() {
  local name="$1" pattern="$2"
  local pidfile="$STATUS/${name}.pid"
  local stfile="$STATUS/${name}.status"
  # Prefer our own bookkeeping: intentional skip wins over unrelated host processes.
  if [[ -f "$stfile" ]] && grep -q 'state=skipped' "$stfile" 2>/dev/null; then
    local why
    why="$(grep '^reason=' "$stfile" 2>/dev/null | head -n1 | cut -d= -f2- || true)"
    printf '  [SKIP] %-22s %s\n' "$name" "${why:+($why)}"
    return 0
  fi
  local alive=0 pid="-"
  if [[ -f "$pidfile" ]]; then
    pid="$(tr -d '[:space:]' < "$pidfile")"
    if [[ -n "$pid" && "$pid" != "0" ]] && kill -0 "$pid" 2>/dev/null; then
      alive=1
    fi
  fi
  if [[ "$alive" -eq 0 ]] && running_pat "$pattern"; then
    alive=1
    pid="$(pgrep -f "$pattern" | head -n1 || echo "?")"
  fi
  if [[ "$alive" -eq 1 ]]; then
    printf '  [UP]   %-22s pid=%s\n' "$name" "$pid"
  else
    printf '  [DOWN] %-22s\n' "$name"
  fi
}

echo "Prozesse:"
check_one "nexus-orchestrator" "nexus_orchestrator.py"
check_one "overlay" "run-overlay-relocatable.py|overlay_daemon.py"
check_one "yggdrasil" "yggdrasil -useconffile"

echo
echo "Status-Dateien:"
if [[ -d "$STATUS" ]]; then
  for f in "$STATUS"/*; do
    [[ -f "$f" ]] || continue
    echo "  --- $(basename "$f") ---"
    sed 's/^/    /' "$f"
  done
else
  echo "  (keine — noch nicht gestartet?)"
fi

echo
echo "Control Plane ($CTRL):"
if have curl && curl -fsS --max-time 2 "$CTRL/health" 2>/dev/null; then
  echo
else
  echo "  nicht erreichbar (ok wenn nur Skript-Start genutzt wird)"
fi

echo
if running_pat "nexus_orchestrator.py"; then
  lumina_ok "Kernprozess lebt"
  exit 0
fi
lumina_warn "Kernprozess nexus_orchestrator.py nicht aktiv"
exit 1
