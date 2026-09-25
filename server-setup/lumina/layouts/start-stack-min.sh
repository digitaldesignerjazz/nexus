#!/usr/bin/env bash
# Relocatable minimal stack starter (fork of live start-stack.sh).
# Uses LUMINA_ROOT. NEVER starts onyx-listen / actions-runner / dockerd
# unless ENABLE_HANNOVER_EXTRAS=1.
set -u

SELF="$(cd "$(dirname "$0")" && pwd)"
PKG="$(cd "$SELF/.." && pwd)"
LUMINA_ROOT="${LUMINA_ROOT:-$PKG}"
STACK="${LUMINA_STACK:-$PKG/runtime/stack}"
STATE="${LUMINA_STATE:-$STACK/lumina-state}"
LOG="${LUMINA_ROOT}/runtime/logs/start-stack-min.log"
ENABLE_HANNOVER_EXTRAS="${ENABLE_HANNOVER_EXTRAS:-0}"

mkdir -p "$(dirname "$LOG")" "$LUMINA_ROOT/runtime/status"
log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

started=0
failed=0
skipped=0

running() { pgrep -f "$1" >/dev/null 2>&1; }

start_bg() {
  local name="$1"
  shift
  nohup "$@" >/dev/null 2>&1 &
  sleep 0.4
  if running "$name"; then
    log "started $name"
    started=$((started + 1))
  else
    log "FAILED $name"
    failed=$((failed + 1))
  fi
}

log "start-stack-min LUMINA_ROOT=$LUMINA_ROOT ENABLE_HANNOVER_EXTRAS=$ENABLE_HANNOVER_EXTRAS"

# Nexus orchestrator from snapshot or env
ORCH="${NEXUS_ORCHESTRATOR:-}"
if [[ -z "$ORCH" ]]; then
  if [[ -f "$STACK/nexus/python/nexus_orchestrator.py" ]]; then
    ORCH="$STACK/nexus/python/nexus_orchestrator.py"
  fi
fi
if [[ -n "$ORCH" ]]; then
  if running "nexus_orchestrator.py"; then
    log "ok nexus"
  else
    start_bg "nexus_orchestrator.py" python3 -u "$ORCH"
  fi
else
  log "SKIP nexus (no orchestrator path)"
  skipped=$((skipped + 1))
fi

# Overlay relocatable launcher if present
OVL="$PKG/layouts/run-overlay-relocatable.py"
if [[ -f "$OVL" ]]; then
  if running "run-overlay-relocatable.py"; then
    log "ok overlay"
  else
    export LUMINA_STACK="$STACK"
    export LUMINA_OVERLAY_KEYS="${LUMINA_OVERLAY_KEYS:-$PKG/runtime/keys/overlay}"
    export LUMINA_STATUS_DIR="$LUMINA_ROOT/runtime/status"
    start_bg "run-overlay-relocatable.py" python3 -u "$OVL"
  fi
else
  log "SKIP overlay (launcher missing)"
  skipped=$((skipped + 1))
fi

# Optional agent scripts from snapshot (harmless if missing deps)
if [[ -d "$STATE" ]]; then
  for agent in elara lyra xen orchestrator; do
    script="$STATE/${agent}.sh"
    if [[ -x "$script" ]] || [[ -f "$script" ]]; then
      if running "$script"; then
        log "ok $agent"
      else
        # Agents often need ollama / hardcoded paths — best-effort only
        start_bg "$script" bash "$script" || true
      fi
    else
      log "SKIP $agent (missing)"
      skipped=$((skipped + 1))
    fi
  done
fi

# --- Hannover extras: OFF by default ---
if [[ "$ENABLE_HANNOVER_EXTRAS" != "1" ]]; then
  log "SKIP onyx-listen (ENABLE_HANNOVER_EXTRAS!=1)"
  log "SKIP actions-runner (ENABLE_HANNOVER_EXTRAS!=1)"
  log "SKIP dockerd (ENABLE_HANNOVER_EXTRAS!=1)"
  skipped=$((skipped + 3))
else
  log "WARN Hannover extras enabled — only meaningful on Hannover host"
  # Intentionally minimal stubs: we refuse to auto-start secrets-bearing runners
  # from this public package. Operator must use live /workspace start-stack.sh.
  log "SKIP onyx-listen (public package will not spawn it — use live start-stack on Hannover)"
  log "SKIP actions-runner (credentials not in package)"
  log "SKIP dockerd (not managed by public package)"
  skipped=$((skipped + 3))
fi

log "done started=$started failed=$failed skipped=$skipped"
if [[ "$failed" -gt 0 ]]; then
  exit 1
fi
exit 0
