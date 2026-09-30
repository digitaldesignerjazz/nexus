#!/usr/bin/env bash
# Earth Node bring-up on an operator host (Onyx / Hannover).
# Never clobbers $HOME/nexus when that tree has no server-setup.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SELF/lib.sh"

trap 'die "Earth-Node-Bootstrap abgebrochen in Zeile $LINENO" 1' ERR

HUB="${NEXUS_HUB:-$HOME/nexus-hub}"
REPO_URL="${NEXUS_REPO_URL:-https://github.com/digitaldesignerjazz/nexus.git}"

echo "=== Nexus Earth Node Bootstrap ==="
echo "Hub : $HUB"
echo "Home: $HOME"

require_cmd git
require_cmd python3

if [[ -d "$HOME/nexus" && ! -d "$HOME/nexus/server-setup" ]]; then
  nexus_warn "$HOME/nexus existiert ohne server-setup — bleibt unangetastet."
fi

if [[ -d "$HUB/.git" ]]; then
  nexus_log "Hub vorhanden — fast-forward pull"
  git -C "$HUB" fetch origin || die "git fetch in $HUB fehlgeschlagen." 5
  branch="$(git -C "$HUB" rev-parse --abbrev-ref HEAD)"
  git -C "$HUB" pull --ff-only origin "$branch" || \
    die "ff-only pull fehlgeschlagen in $HUB (lokale Commits?). Branch: $branch" 5
elif [[ -e "$HUB" ]]; then
  die "$HUB existiert, ist aber kein git-Repo. Anderen NEXUS_HUB setzen." 3
else
  parent="$(dirname "$HUB")"
  mkdir -p "$parent"
  nexus_log "Klone $REPO_URL → $HUB"
  git clone "$REPO_URL" "$HUB" || die "git clone nach $HUB fehlgeschlagen." 5
fi

SETUP="$HUB/server-setup"
[[ -d "$SETUP/scripts" ]] || die "Klon ohne server-setup: $SETUP" 3
cd "$SETUP"

bash "$SETUP/scripts/00-doctor.sh"
bash "$SETUP/scripts/01-bootstrap.sh"

if [[ -f .env ]]; then
  if grep -q '^NEXUS_NODE_NAME=' .env; then
    sed -i.bak 's/^NEXUS_NODE_NAME=.*/NEXUS_NODE_NAME=onyx-earth/' .env
  else
    printf '\nNEXUS_NODE_NAME=onyx-earth\n' >> .env
  fi
  if grep -q '^NEXUS_SITE=' .env; then
    sed -i.bak 's/^NEXUS_SITE=.*/NEXUS_SITE=Hannover/' .env
  else
    printf 'NEXUS_SITE=Hannover\n' >> .env
  fi
  chmod 600 .env
  rm -f .env.bak
fi

bash "$SETUP/scripts/02-start-control-plane.sh" --background
exit $?
