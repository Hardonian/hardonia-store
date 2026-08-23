#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-"$ROOT/receipts"}
python3 "$ROOT/ai-change-ledger.py" --out-dir "$OUT"
python3 "$ROOT/ai-change-ledger.py" --out-dir "$OUT" --verify
printf 'Receipt files: %s\n' "$OUT"
