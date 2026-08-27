#!/usr/bin/env bash
set -euo pipefail
echo "=== Nexus Doctor ==="
ok=0
check() {
  local name="$1" cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $name ($cmd → $(command -v "$cmd"))"
  else
    echo "[MISSING] $name ($cmd)"
    ok=1
  fi
}
check "Python 3" python3
check "Git" git
check "Go (optional, go-nexus CLI)" go || true
check "Docker (optional, compose stack)" docker || true
check "Yggdrasil (optional, mesh)" yggdrasil || true
check "Cargo/Rust (optional, daemon)" cargo || true
python3 - <<'PY'
import sys
print(f"[OK] Python runtime {sys.version.split()[0]}")
PY
echo
echo "Nächste Schritte: bash scripts/01-bootstrap.sh"
exit 0
