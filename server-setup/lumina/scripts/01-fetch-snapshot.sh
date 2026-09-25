#!/usr/bin/env bash
# Fetch + verify the public LuminaCyberspace snapshot into runtime/.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib-lumina.sh"

PKG="$(cd "$SELF/.." && pwd)"
assert_lumina_root "$PKG"
load_dotenv "$PKG/.env"
ensure_runtime "$PKG"

URL="${SNAPSHOT_URL:-$(tr -d '[:space:]' < "$PKG/pins/SNAPSHOT_URL.txt")}"
SHA_LINE="$(tr -d '\r' < "$PKG/pins/SNAPSHOT.sha256" | head -n1)"
EXPECT_SHA="${SNAPSHOT_SHA256:-${SHA_LINE%% *}}"
ARCHIVE_NAME="${SHA_LINE##* }"
[[ -n "$ARCHIVE_NAME" && "$ARCHIVE_NAME" != "$SHA_LINE" ]] || ARCHIVE_NAME="lumina-stack-public-20260924-2240.tar.gz"

DL="$PKG/runtime/downloads"
STACK="$PKG/runtime/stack"
ARCHIVE="$DL/$ARCHIVE_NAME"

echo "=== Lumina · fetch-snapshot ==="
echo "URL : $URL"
echo "SHA : $EXPECT_SHA"
echo "Out : $ARCHIVE"
echo

require_cmd curl
require_cmd tar
require_cmd sha256sum

mkdir -p "$DL"

if [[ -f "$ARCHIVE" ]]; then
  GOT="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
  if [[ "$GOT" == "$EXPECT_SHA" ]]; then
    lumina_ok "Archiv bereits vorhanden und Prüfsumme ok"
  else
    lumina_warn "Archiv vorhanden, Prüfsumme weicht ab — lade neu"
    rm -f "$ARCHIVE"
  fi
fi

if [[ ! -f "$ARCHIVE" ]]; then
  lumina_log "Lade Snapshot …"
  curl -fL --retry 3 --retry-delay 2 -o "$ARCHIVE.partial" "$URL"
  mv "$ARCHIVE.partial" "$ARCHIVE"
fi

GOT="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
if [[ "$GOT" != "$EXPECT_SHA" ]]; then
  die "SHA256 mismatch: got $GOT expected $EXPECT_SHA" 5
fi
lumina_ok "SHA256 verifiziert"

# Extract into a clean stack dir
rm -rf "$STACK"
mkdir -p "$STACK"
tar -xzf "$ARCHIVE" -C "$STACK"
# Flatten if single top-level dir
TOP=( "$STACK"/*/ )
if [[ ${#TOP[@]} -eq 1 && -d "${TOP[0]}" ]]; then
  # move contents up
  shopt -s dotglob nullglob
  mv "${TOP[0]}"* "$STACK"/ 2>/dev/null || true
  shopt -u dotglob nullglob
  rmdir "${TOP[0]}" 2>/dev/null || rm -rf "${TOP[0]}"
fi

# Record extract meta
{
  echo "url=$URL"
  echo "sha256=$EXPECT_SHA"
  echo "archive=$ARCHIVE_NAME"
  echo "extracted_at=$(date -Iseconds)"
} > "$PKG/runtime/status/snapshot.status"

lumina_ok "Snapshot extrahiert nach $STACK"
echo "Inhalt (Top):"
ls -1 "$STACK" | sed 's/^/  /'
echo
echo "Nächste Schritte: bash scripts/02-gen-keys.sh  (oder direkt 03-start-cyberspace.sh)"
exit 0
