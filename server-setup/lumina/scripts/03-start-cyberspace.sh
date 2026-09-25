#!/usr/bin/env bash
# Start LuminaCyberspace from the public snapshot (relocatable via LUMINA_ROOT).
# Actually starts: nexus_orchestrator.py, optional overlay prototype, optional yggdrasil.
# Does NOT start (unless ENABLE_HANNOVER_EXTRAS=1): onyx-listen, actions-runner, dockerd.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib-lumina.sh"

PKG="$(cd "$SELF/.." && pwd)"
assert_lumina_root "$PKG"
load_dotenv "$PKG/.env"

# Relocatable root: package dir by default
export LUMINA_ROOT="${LUMINA_ROOT:-$PKG}"
ensure_runtime "$PKG"

STACK="$PKG/runtime/stack"
STATUS="$PKG/runtime/status"
LOGS="$PKG/runtime/logs"
PY="$(python_bin)"
CTRL="${NEXUS_CONTROL_URL:-http://127.0.0.1:8787}"
ENABLE_HANNOVER_EXTRAS="${ENABLE_HANNOVER_EXTRAS:-0}"
ENABLE_YGGDRASIL="${ENABLE_YGGDRASIL:-0}"

echo "=== Lumina · start-cyberspace (nexus-lumina $(cat "$PKG/VERSION")) ==="
echo "Pkg   : $PKG"
echo "Root  : $LUMINA_ROOT"
echo "Python: $PY"
echo "Extras: ENABLE_HANNOVER_EXTRAS=$ENABLE_HANNOVER_EXTRAS ENABLE_YGGDRASIL=$ENABLE_YGGDRASIL"
echo

started=0
failed=0
skipped=0

start_bg() {
  local name="$1"
  local pattern="$2"
  shift 2
  if running_pat "$pattern"; then
    lumina_ok "$name bereits aktiv"
    local pid
    pid="$(pgrep -f "$pattern" | head -n1 || true)"
    write_status "$STATUS" "$name" "${pid:-0}" "state=already_running"
    return 0
  fi
  local logf="$LOGS/${name}.log"
  nohup "$@" >>"$logf" 2>&1 &
  local pid=$!
  sleep 0.6
  if kill -0 "$pid" 2>/dev/null || running_pat "$pattern"; then
    [[ -n "$pid" ]] || pid="$(pgrep -f "$pattern" | head -n1 || true)"
    write_status "$STATUS" "$name" "${pid:-0}" "state=started"$'\n'"log=$logf"
    lumina_ok "gestartet $name (pid=${pid:-?})"
    started=$((started + 1))
    return 0
  fi
  write_status "$STATUS" "$name" "0" "state=failed"$'\n'"log=$logf"
  lumina_err "FAILED $name (siehe $logf)"
  failed=$((failed + 1))
  return 1
}

# 1) Ensure snapshot
if [[ ! -f "$STACK/nexus/python/nexus_orchestrator.py" ]]; then
  lumina_log "Snapshot fehlt — hole ihn …"
  bash "$SELF/01-fetch-snapshot.sh"
fi
[[ -f "$STACK/nexus/python/nexus_orchestrator.py" ]] || die "Snapshot unvollständig: nexus_orchestrator.py fehlt" 3

# 2) Keys (best-effort)
if [[ ! -d "$PKG/runtime/keys/overlay" ]] || [[ -z "$(ls -A "$PKG/runtime/keys/overlay" 2>/dev/null || true)" ]]; then
  bash "$SELF/02-gen-keys.sh" || lumina_warn "gen-keys hatte Warnungen"
fi

# 3) Nexus orchestrator (always — this is the verifiable core)
ORCH="$STACK/nexus/python/nexus_orchestrator.py"
# Prefer repo python/ if newer and present next to package
REPO_ORCH="$(cd "$PKG/../.." && pwd)/python/nexus_orchestrator.py"
if [[ -f "$REPO_ORCH" ]]; then
  ORCH="$REPO_ORCH"
  lumina_log "nutze Repo-Orchestrator: $ORCH"
else
  lumina_log "nutze Snapshot-Orchestrator: $ORCH"
fi

start_bg "nexus-orchestrator" "nexus_orchestrator.py" \
  "$PY" -u "$ORCH" || true

# 4) Overlay prototype (if present + PyNaCl)
OVERLAY_OK=0
if "$PY" -c 'import nacl' 2>/dev/null; then
  OVERLAY_OK=1
fi

if [[ "$OVERLAY_OK" -eq 1 ]]; then
  # Relocatable overlay launcher (avoids hardcoded /workspace paths)
  OVL_LAUNCHER="$PKG/layouts/run-overlay-relocatable.py"
  if [[ -f "$OVL_LAUNCHER" ]]; then
    export LUMINA_STACK="$STACK"
    export LUMINA_OVERLAY_KEYS="$PKG/runtime/keys/overlay"
    export LUMINA_STATUS_DIR="$STATUS"
    start_bg "overlay" "run-overlay-relocatable.py" \
      "$PY" -u "$OVL_LAUNCHER" || true
  elif [[ -f "$STACK/lumina-state/overlay_daemon.py" ]]; then
    lumina_warn "overlay_daemon.py im Snapshot hat hartcodierte /workspace-Pfade — nutze Relocatable-Launcher"
    skipped=$((skipped + 1))
  fi
else
  lumina_warn "PyNaCl fehlt — Overlay übersprungen"
  skipped=$((skipped + 1))
  write_status "$STATUS" "overlay" "0" "state=skipped"$'\n'"reason=no_pynacl"
fi

# 5) Optional yggdrasil
if [[ "${ENABLE_YGGDRASIL}" == "1" ]]; then
  YGG_CONF="${YGGDRASIL_CONF:-$PKG/runtime/keys/ygg/yggdrasil.conf}"
  if ! have yggdrasil; then
    lumina_warn "ENABLE_YGGDRASIL=1 aber yggdrasil fehlt"
    skipped=$((skipped + 1))
  elif [[ ! -f "$YGG_CONF" ]]; then
    lumina_warn "Keine Ygg-Config unter $YGG_CONF — erst 02-gen-keys.sh"
    skipped=$((skipped + 1))
  elif grep -q '<REDACTED>' "$YGG_CONF" 2>/dev/null; then
    die "Ygg-Config enthält <REDACTED> — darf nicht gestartet werden. Nutze runtime/keys/ygg/." 3
  elif running_pat "yggdrasil -useconffile"; then
    lumina_ok "yggdrasil bereits aktiv"
  else
    # Prefer user-mode if no TUN privileges; still attempt
    lumina_log "starte yggdrasil mit $YGG_CONF"
    if start_bg "yggdrasil" "yggdrasil -useconffile $YGG_CONF" \
        yggdrasil -useconffile "$YGG_CONF"; then
      :
    else
      lumina_warn "yggdrasil Start fehlgeschlagen (oft: fehlende TUN/Root-Rechte) — weiter ohne Mesh"
    fi
  fi
else
  lumina_log "yggdrasil optional (ENABLE_YGGDRASIL=0) — übersprungen"
  write_status "$STATUS" "yggdrasil" "0" "state=skipped"$'\n'"reason=ENABLE_YGGDRASIL=0"
fi

# 6) Hannover extras via min layout
if [[ "$ENABLE_HANNOVER_EXTRAS" == "1" ]]; then
  lumina_warn "ENABLE_HANNOVER_EXTRAS=1 — rufe layouts/start-stack-min.sh (Hannover-only)"
  bash "$PKG/layouts/start-stack-min.sh" || lumina_warn "start-stack-min meldete Fehler"
else
  lumina_log "Hannover-Extras aus (onyx-listen / actions-runner / dockerd bleiben aus)"
fi

# 7) Smoke
echo
echo "=== Smoke ==="
smoke_ok=0
if running_pat "nexus_orchestrator.py"; then
  lumina_ok "Prozess nexus_orchestrator.py lebt"
  smoke_ok=1
else
  lumina_err "Prozess nexus_orchestrator.py nicht gefunden"
fi

if have curl; then
  if curl -fsS --max-time 2 "$CTRL/health" >/dev/null 2>&1; then
    lumina_ok "Control Plane antwortet ($CTRL/health) — Info only, spawnt nicht"
  else
    lumina_warn "Control Plane nicht erreichbar ($CTRL) — ok für alpha.2 (Skript-Start)"
  fi
fi

{
  echo "version=$(cat "$PKG/VERSION")"
  echo "started_at=$(date -Iseconds)"
  echo "started_count=$started"
  echo "failed_count=$failed"
  echo "skipped_count=$skipped"
  echo "smoke_orchestrator=$smoke_ok"
  echo "enable_hannover_extras=$ENABLE_HANNOVER_EXTRAS"
  echo "enable_yggdrasil=$ENABLE_YGGDRASIL"
} > "$STATUS/cyberspace.status"

echo
echo "Status-Dateien: $STATUS/"
ls -1 "$STATUS" | sed 's/^/  /' || true
echo
if [[ "$smoke_ok" -eq 1 && "$failed" -eq 0 ]]; then
  lumina_ok "Cyberspace-Start ok (started=$started skipped=$skipped)"
  echo "Prüfen: bash scripts/04-status.sh"
  exit 0
elif [[ "$smoke_ok" -eq 1 ]]; then
  lumina_warn "Teilweise ok (started=$started failed=$failed skipped=$skipped)"
  exit 0
fi
die "Start fehlgeschlagen (orchestrator tot, failed=$failed)" 1
