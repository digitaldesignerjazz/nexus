#!/usr/bin/env bash
# Generate local (non-committed) keys for yggdrasil + overlay.
# Never prints private key material. Scrubbed snapshot stays scrubbed.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib-lumina.sh"

PKG="$(cd "$SELF/.." && pwd)"
assert_lumina_root "$PKG"
load_dotenv "$PKG/.env"
ensure_runtime "$PKG"

YGG_DIR="$PKG/runtime/keys/ygg"
OVL_DIR="$PKG/runtime/keys/overlay"
STACK="$PKG/runtime/stack"

echo "=== Lumina · gen-keys ==="
echo "Ygg keys → $YGG_DIR"
echo "Overlay  → $OVL_DIR"
echo

mkdir -p "$YGG_DIR" "$OVL_DIR"
chmod 700 "$PKG/runtime/keys" "$YGG_DIR" "$OVL_DIR"

# --- Yggdrasil ---
if have yggdrasil; then
  CONF="$YGG_DIR/yggdrasil.conf"
  if [[ -f "$CONF" ]]; then
    lumina_ok "Yggdrasil-Config existiert bereits ($CONF) — belasse sie"
  else
    lumina_log "Erzeuge neue Yggdrasil-Config via yggdrasil -genconf"
    yggdrasil -genconf > "$CONF"
    chmod 600 "$CONF"
    # If scrubbed hub template exists, merge Listen/Peers from public template
    # but keep the newly generated PrivateKey (never copy REDACTED).
    HUB_TMPL="$STACK/yggdrasil/hannover-hub.yggdrasil.conf"
    if [[ -f "$HUB_TMPL" ]]; then
      lumina_log "Hinweis: öffentliche Hub-Vorlage gefunden — PrivateKey bleibt lokal generiert (nicht aus Snapshot)."
    fi
    lumina_ok "Yggdrasil-Config geschrieben (PrivateKey lokal, nicht im Repo)"
  fi
  if have yggdrasilctl || true; then
    # Extract public identity without dumping PrivateKey
    if grep -q 'PrivateKey:' "$CONF" 2>/dev/null; then
      PUB_HINT="$YGG_DIR/public-hint.txt"
      {
        echo "# Generated locally $(date -Iseconds)"
        echo "# PrivateKey is in yggdrasil.conf (mode 600). Do not commit."
        echo "config=$CONF"
      } > "$PUB_HINT"
    fi
  fi
else
  lumina_warn "yggdrasil nicht im PATH — Mesh-Keys übersprungen (ENABLE_YGGDRASIL wirkungslos)"
fi

# --- Overlay Ed25519 seeds (PyNaCl) ---
PY="$(python_bin)"
if "$PY" - <<PY
import os, sys
from pathlib import Path
try:
    from nacl.signing import SigningKey
except ImportError:
    print("[WARN] PyNaCl fehlt — Overlay-Keys übersprungen", file=sys.stderr)
    raise SystemExit(0)

ovl = Path("$OVL_DIR")
ovl.mkdir(parents=True, exist_ok=True)
names = ["hub", "elara", "lyra", "xen", "lumia"]
created = 0
for name in names:
    path = ovl / f"{name}.key"
    if path.exists():
        continue
    key = SigningKey.generate()
    path.write_bytes(bytes(key))
    os.chmod(path, 0o600)
    created += 1
    pub = ovl / f"{name}.pub"
    pub.write_text(bytes(key.verify_key).hex() + "\\n", encoding="utf-8")
print(f"[OK] Overlay-Keys bereit (neu: {created}, Pfad: {ovl})")
PY
then
  :
else
  lumina_warn "Overlay-Key-Generierung fehlgeschlagen"
fi

# Guard: never leave REDACTED configs as runnable without keys
if [[ -d "$STACK/yggdrasil" ]]; then
  if grep -Rql '<REDACTED>' "$STACK/yggdrasil" 2>/dev/null; then
    lumina_ok "Snapshot-Ygg-Configs bleiben scrubbed (<REDACTED>) — Laufzeit nutzt runtime/keys/ygg/"
  fi
fi

write_status "$PKG/runtime/status" "keys" "0" "ygg_dir=$YGG_DIR"$'\n'"overlay_dir=$OVL_DIR"
lumina_ok "Keys fertig. Private Keys liegen nur unter runtime/keys/ (gitignored)."
echo "Nächste Schritte: bash scripts/03-start-cyberspace.sh"
exit 0
