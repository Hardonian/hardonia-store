#!/usr/bin/env bash
set -Eeuo pipefail
json="$(cat "${HOME}/.cache/ai-lab/watchdog-status.json" 2>/dev/null || echo '[]')"
unhealthy="$(printf '%s\n' "$json" | grep '"healthy":false' || true)"
if [ -n "$unhealthy" ]; then
  printf 'ALERT\n%s\n' "$unhealthy"
  exit 1
fi
printf 'OK\n%s\n' "$json"
exit 0
