#!/usr/bin/env bash
# install-heritage-quiet.sh — one-line install for the Heritage Quiet skin pack.
# Usage: curl -fsSL <store-url>/install-heritage-quiet.sh | bash
set -Eeuo pipefail
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKIN_DIR="$HERMES_HOME/skins"
mkdir -p "$SKIN_DIR"
SRC="https://raw.githubusercontent.com/Hardonian/agent-skins/main/heritage-quiet/skin.yaml"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$SRC" -o "$SKIN_DIR/heritage-quiet.yaml"
else
  wget -qO "$SKIN_DIR/heritage-quiet.yaml" "$SRC"
fi
echo "Heritage Quiet skin installed to $SKIN_DIR/heritage-quiet.yaml"
echo "Set 'display.skin: heritage-quiet' in $HERMES_HOME/config.yaml"
