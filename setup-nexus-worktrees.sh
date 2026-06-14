#!/bin/bash
set -e

echo "=== Nexus + SolNetP2P Worktree Setup ==="

# === Configuration ===
NEXUS_DIR="$HOME/projects/nexus"
NEXUS_DEV_DIR="$HOME/projects/nexus-dev"
SOLNETP2P_DEV_DIR="$HOME/projects/solnetp2p-dev"

echo ""
echo "This script will create:"
echo "  - $NEXUS_DEV_DIR     (Nexus worktree)"
echo "  - $SOLNETP2P_DEV_DIR (SolNetP2P worktree)"
echo ""

# 1. Ensure we're inside the main Nexus repo
if [ ! -d ".git" ] || [ ! -f ".gitmodules" ]; then
    echo "Error: Please run this script from inside your main Nexus repository."
    exit 1
fi

# 2. Create worktree for Nexus development
if [ ! -d "$NEXUS_DEV_DIR" ]; then
    echo "→ Creating Nexus worktree at $NEXUS_DEV_DIR..."
    git worktree add "$NEXUS_DEV_DIR" main
else
    echo "→ Nexus worktree already exists at $NEXUS_DEV_DIR"
fi

# 3. Initialize submodules in the new worktree
if [ -d "$NEXUS_DEV_DIR" ]; then
    echo "→ Initializing submodules in nexus-dev..."
    cd "$NEXUS_DEV_DIR"
    git submodule update --init --recursive || true
    cd - > /dev/null
fi

# 4. Create a dedicated worktree for SolNetP2P
mkdir -p "$(dirname "$SOLNETP2P_DEV_DIR")"

if [ ! -d "$SOLNETP2P_DEV_DIR" ]; then
    echo "→ Creating dedicated SolNetP2P worktree at $SOLNETP2P_DEV_DIR..."
    if [ -d "mesh/solnetp2p" ]; then
        cd mesh/solnetp2p
        git worktree add "$SOLNETP2P_DEV_DIR" main 2>/dev/null || git worktree add "$SOLNETP2P_DEV_DIR" -f main --detach
        cd - > /dev/null
    else
        echo "Warning: mesh/solnetp2p submodule not found. Creating empty worktree."
        mkdir -p "$SOLNETP2P_DEV_DIR"
    fi
else
    echo "→ SolNetP2P worktree already exists at $SOLNETP2P_DEV_DIR"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Recommended directories:"
echo "  Nexus dev:        $NEXUS_DEV_DIR"
echo "  SolNetP2P dev:    $SOLNETP2P_DEV_DIR"
echo ""
echo "Useful commands after setup:"
echo "  cd ~/projects/nexus-dev          # Work on Nexus"
echo "  cd ~/projects/solnetp2p-dev    # Work on SolNetP2P"
echo ""
echo "To update SolNetP2P submodule pointer in Nexus:"
echo "  cd ~/projects/nexus-dev"
echo "  cd mesh/solnetp2p && git pull origin main && cd .."
echo "  git add mesh/solnetp2p && git commit -m 'chore: Update SolNetP2P submodule'"