#!/usr/bin/env bash
# enroll_peers.sh — Nexus Mesh: 47 Peers per reusable Setup Key
# Conductor: Lumia | Operator: Sir
#
# WICHTIG:
# - Keine Keys im Repo. Key kommt aus Env oder Datei.
# - NetBird API hat KEINEN POST /api/peers. Peers entstehen nur durch
#   netbird up --setup-key auf dem jeweiligen Host.
# - Dieses Skript erzeugt die Einladungs-Kommandos / Docker-Runs.

set -euo pipefail

TARGET=47
KEY_FILE="${NETBIRD_KEY_FILE:-$HOME/.config/netbird/setup.key}"
KEY_ENV="${NETBIRD_SETUP_KEY:-}"
OUT_DIR="${NEXUS_ENROLL_OUT:-./enroll_out}"
PREFIX="${NEXUS_PEER_PREFIX:-nexus-peer}"

mkdir -p "$OUT_DIR"

if [[ -n "$KEY_ENV" ]]; then
  KEY="$KEY_ENV"
elif [[ -f "$KEY_FILE" ]]; then
  KEY="$(tr -d '[:space:]' < "$KEY_FILE")"
else
  echo "Kein Key gefunden." >&2
  echo "Setze NETBIRD_SETUP_KEY oder lege den Key in $KEY_FILE ab." >&2
  echo "Rotiere alte Keys in der NetBird-Console — sie galten als kompromittiert." >&2
  exit 1
fi

# Sicherstellen, dass der Key nicht leer ist
if [[ -z "$KEY" ]]; then
  echo "Key ist leer." >&2
  exit 1
fi

cat > "$OUT_DIR/README.txt" <<EOF
Nexus Peer-Enrollment — $TARGET Peers
Erzeugt: $(date -Iseconds)
Methode: reusable Setup Key (Usage-Limit >= $TARGET)
Regel: kein Key im Repo, kein Key in Git-Historie.
EOF

# 1) Einladungs-Kommandos (für manuelle Hosts / SSH)
{
  echo "#!/usr/bin/env bash"
  echo "# Einladungen — je Host einmal ausführen"
  echo "set -euo pipefail"
  echo
  for i in $(seq -w 1 "$TARGET"); do
    name="${PREFIX}-${i}"
    echo "# Peer $i / $TARGET"
    echo "netbird up --setup-key '$KEY' --hostname '$name'"
    echo
  done
} > "$OUT_DIR/invite_commands.sh"
chmod +x "$OUT_DIR/invite_commands.sh"

# 2) Docker-Variante (für Container-Peers)
{
  echo "#!/usr/bin/env bash"
  echo "set -euo pipefail"
  echo
  for i in $(seq -w 1 "$TARGET"); do
    name="${PREFIX}-${i}"
    echo "docker run -d --name '$name' --hostname '$name' \\"
    echo "  --cap-add=NET_ADMIN --cap-add=SYS_ADMIN \\"
    echo "  -e NB_SETUP_KEY='$KEY' \\"
    echo "  -v netbird-client:/var/lib/netbird \\"
    echo "  netbirdio/netbird:latest"
    echo
  done
} > "$OUT_DIR/docker_enroll.sh"
chmod +x "$OUT_DIR/docker_enroll.sh"

# 3) Status-Check nach Enrollment
cat > "$OUT_DIR/check_status.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "=== netbird status ==="
netbird status || true
echo
echo "=== Peers (API, falls Token gesetzt) ==="
if [[ -n "${NETBIRD_API_TOKEN:-}" ]]; then
  curl -sS -H "Authorization: Token $NETBIRD_API_TOKEN" \
    https://api.netbird.io/api/peers | python3 -c \
    'import sys,json; d=json.load(sys.stdin); print(len(d),"peers")' 2>/dev/null || echo "API-Abfrage fehlgeschlagen"
else
  echo "NETBIRD_API_TOKEN nicht gesetzt — überspringe API-Check."
fi
EOF
chmod +x "$OUT_DIR/check_status.sh"

echo "Fertig. Ausgabe in: $OUT_DIR"
echo "- invite_commands.sh   (SSH/manuelle Hosts)"
echo "- docker_enroll.sh      (Container)"
echo "- check_status.sh       (Status + API)"
echo
echo "Nächster Schritt:"
echo "  1. In der NetBird-Console einen reusable Key mit Usage-Limit >= $TARGET anlegen."
echo "  2. Key sicher hinterlegen (Env oder $KEY_FILE), NICHT committen."
echo "  3. ./$OUT_DIR/invite_commands.sh   ODER   ./$OUT_DIR/docker_enroll.sh"
echo "  4. ./$OUT_DIR/check_status.sh"
