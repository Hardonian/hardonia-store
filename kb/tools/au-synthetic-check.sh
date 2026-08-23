#!/usr/bin/env bash
# au-synthetic-check.sh — verify the bot answers + escalates correctly (cron-friendly).
# Exits non-zero if the bot is broken (so the watchdog/cron can alert).
set -Eeuo pipefail
BOT=127.0.0.1:8071
ok=1
check(){ local name="$1" expect="$2" q="$3"; local out
  out=$(curl -s --max-time 20 -X POST "http://$BOT/au/ask" -H 'Content-Type: application/json' -d "{\"query\":\"$q\"}" 2>/dev/null)
  if echo "$out" | grep -qi "$expect"; then echo "PASS $name"; else echo "FAIL $name: $out"; ok=0; fi
}
check_any(){ local name="$1" expect_re="$2" q="$3"; local out
  out=$(curl -s --max-time 20 -X POST "http://$BOT/au/ask" -H 'Content-Type: application/json' -d "{\"query\":\"$q\"}" 2>/dev/null)
  if echo "$out" | grep -Eqi "$expect_re"; then echo "PASS $name"; else echo "FAIL $name: $out"; ok=0; fi
}
# A healthy capacity-aware bot either explains X-API-Key authentication or
# fails closed by explicitly pausing key issuance while the GPU pool is full.
check_any "answers auth" "X-API-Key|key issuance is briefly paused" "How do I authenticate to the Hardonia Compute API?"
check "escalates leak" "ESCALATION" "my key sk-abcd1234efgh5678 broken"
check "answers product" "Private" "What is Private Inference Access?"
curl -s --max-time 3 "http://$BOT/au/health" >/dev/null 2>&1 || { echo "FAIL health"; ok=0; }
[[ "$ok" -eq 1 ]] && exit 0 || exit 1
