#!/usr/bin/env bash
set -Eeuo pipefail
OUT="${1:-$HOME/ai-lab/status/lab-health-report.md}"
mkdir -p "$(dirname "$OUT")"
cat > "$OUT" <<'MD'
# AI Lab Health Report
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
MD
for p in 8000 8011 8188 5678 11438 8001 3002; do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/health" 2>/dev/null || true)
  printf ' - %s HTTP %s\n' "$port" "$CODE" >> "$OUT"
done
echo "Wrote $OUT"
