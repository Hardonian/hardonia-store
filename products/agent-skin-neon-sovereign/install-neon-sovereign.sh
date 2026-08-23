#!/usr/bin/env bash
# install-neon-sovereign.sh — one-line install for the Neon Sovereign skin pack.
# Usage: curl -fsSL <store-url>/install-neon-sovereign.sh | bash
set -Eeuo pipefail
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKIN_DIR="$HERMES_HOME/skins"
mkdir -p "$SKIN_DIR"
SRC="https://raw.githubusercontent.com/Hardonian/agent-skins/main/neon-sovereign/skin.yaml"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$SRC" -o "$SKIN_DIR/neon-sovereign.yaml"
else
  wget -qO "$SKIN_DIR/neon-sovereign.yaml" "$SRC"
fi
echo "Neon Sovereign skin installed to $SKIN_DIR/neon-sovereign.yaml"
echo "Set 'display.skin: neon-sovereign' in $HERMES_HOME/config.yaml"
