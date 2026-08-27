#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Nexus Bootstrap ==="
mkdir -p data logs control/vendor

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo "→ .env angelegt (chmod 600)"
fi

if [ ! -d control/vendor/nexus-python ]; then
  echo "→ Klone Python-Referenz aus digitaldesignerjazz/nexus"
  git clone --depth 1 https://github.com/digitaldesignerjazz/nexus.git /tmp/nexus-clone
  mkdir -p control/vendor/nexus-python
  cp -a /tmp/nexus-clone/python/. control/vendor/nexus-python/
  rm -rf /tmp/nexus-clone
fi

chmod +x scripts/*.sh control/nexus_control.py || true
echo "Bootstrap fertig."
echo "Start: bash scripts/02-start-control-plane.sh"
