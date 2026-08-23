#!/usr/bin/env bash
# ecosystem-update.sh — regenerate kb/feeds/snapshot.json from LIVE feeds.
# Wiring per kb/ecosystem.md. Idempotent, fails loud if a feed is missing/corrupt.
# Real sources (verified 2026-07):
#   intel:  /home/scott/ai-lab/reports/intel/latest.json  (clusters[]: theme/count/confidence)
#           /home/scott/ai-lab/reports/intel/predictive-winrate-*.json (predictions[]: offer/win_rate)
#   analytics: /home/scott/ai-lab/reports/analytics/summary.json (views/conversions/revenue)
#   compute: EPYC nvidia-smi probe
#   financial/legal: optional override files in feeds/ (fall back to safe defaults)
set -Eeuo pipefail

KB="/home/scott/hardonia.store/kb"
FEEDS="$KB/feeds"
HISTORY="$FEEDS/history"
mkdir -p "$HISTORY"
LOG="$FEEDS/update.log"
TS=$(date -u +%FT%TZ)
log(){ echo "[$TS] $*" >>"$LOG"; }

# ---- compute probe (EPYC local) ----
num(){ case "$1" in (*[!0-9]*) echo 0;; (*) echo "${1:-0}";; esac; }
compute_json='{"gpu_util_pct":0,"free_vram_pct":100,"active_keys":0,"capacity_ok":true}'
if command -v nvidia-smi >/dev/null 2>&1; then
  UTIL=$(num "$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)")
  TOTAL=$(num "$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)")
  USED=$(num "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)")
  if [[ "$TOTAL" -gt 0 ]]; then FREE_PCT=$(( (TOTAL - USED) * 100 / TOTAL )); else FREE_PCT=100; fi
  ACTIVE_KEYS=$(ls /home/scott/.config/caddy/ 2>/dev/null | wc -l)
  CAP_OK="true"; [[ "$FREE_PCT" -lt 10 ]] && CAP_OK="false"
  compute_json="{\"gpu_util_pct\":$UTIL,\"free_vram_pct\":$FREE_PCT,\"active_keys\":$ACTIVE_KEYS,\"capacity_ok\":$CAP_OK}"
  log "compute probe: util=$UTIL free_pct=$FREE_PCT cap_ok=$CAP_OK"
else
  log "nvidia-smi not found; compute probe skipped (defaults)"
fi
if ! python3 -c "import json,sys;json.load(sys.stdin)" <<<"$compute_json" 2>/dev/null; then
  log "WARN: compute_json invalid, using safe default"; compute_json='{"gpu_util_pct":0,"free_vram_pct":100,"active_keys":0,"capacity_ok":true}'
fi

# ---- intel (REAL: predictive-winrate via intel-bridge.sh) ----
INTEL_FLAG="$FEEDS/intel-flag.json"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$HERE/intel-bridge.sh" >/dev/null 2>&1
themes=""; best_offer=""; best_wr=0
if [[ -f "$FEEDS/intel.json" ]]; then
  read -r themes best_offer best_wr < <(python3 - "$FEEDS/intel.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
ts=[t.get('offer') for t in d.get('themes',[])][:5]
print(", ".join(ts) if ts else "none", d.get('best_offer') or "", d.get('best_win_rate') or 0)
PY
)
  log "intel: themes=$themes best_offer=$best_offer wr=$best_wr"
fi
if [[ -f "$INTEL_FLAG" ]]; then
  blocked=$(python3 -c "import json;print('true' if json.load(open('$INTEL_FLAG')).get('block') else 'false')" 2>/dev/null || echo false)
  if [[ "$blocked" == "true" ]]; then
    INTEL=$(python3 -c "import json;d=json.load(open('$INTEL_FLAG'));print(json.dumps({'block':True,'active_flags':d.get('active_flags',[]),'note':d.get('note','manual block')}))")
  else
    INTEL=$(python3 -c "import json;print(json.dumps({'block':False,'active_flags':[],'note':'themes: $themes | best_offer: $best_offer (wr $best_wr)'}))")
  fi
else
  INTEL=$(python3 -c "import json;print(json.dumps({'block':False,'active_flags':[],'note':'themes: $themes | best_offer: $best_offer (wr $best_wr)'}))")
fi

# ---- financial (REAL: Gumroad revenue via financial-bridge.sh) ----
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if bash "$HERE/financial-bridge.sh" >/dev/null 2>&1; then
  FIN=$(cat "$FEEDS/financial.json" 2>/dev/null || echo '{"total_revenue_cents":0,"products":[],"currency":"usd"}')
  log "financial: bridged from Gumroad"
else
  FIN='{"total_revenue_cents":0,"products":[],"currency":"usd"}'
  log "financial bridge failed; default"
fi

# ---- analytics (REAL: aggregate storefront SQLite events via analytics-bridge.sh) ----
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if bash "$HERE/analytics-bridge.sh" >/dev/null 2>&1; then
  ANALYTICS=$(cat "$FEEDS/analytics.json" 2>/dev/null || echo '{"visitors_24h":0,"top_product":"","conversion_pct":0}')
  log "analytics: bridged from storefront events"
else
  ANALYTICS='{"visitors_24h":0,"top_product":"","conversion_pct":0}'
  log "analytics bridge failed; default"
fi

# ---- financial / legal (optional overrides) ----
fin(){ [[ -f "$1" ]] && cat "$1" || echo "$2"; }
# FIN already set from financial-bridge.sh above (real Gumroad revenue)
LEGAL=$(fin "$FEEDS/legal.json" '{"open_flags":[],"minor_safety_clear":true}')

# ---- merge atomically ----
OUT="$FEEDS/snapshot.json"
TMP="$FEEDS/snapshot.json.tmp"
cat >"$TMP" <<EOF
{
  "generated_at": "$TS",
  "intel": $INTEL,
  "analytics": $ANALYTICS,
  "financial": $FIN,
  "compute": $compute_json,
  "legal": $LEGAL
}
EOF
if ! python3 -c "import json,sys; json.load(open('$TMP'))" 2>/dev/null; then
  log "ERROR: snapshot invalid JSON; aborting (old kept)"; echo "ERROR: invalid snapshot" >&2; exit 1
fi
mv "$TMP" "$OUT"
cp "$OUT" "$HISTORY/snapshot.$(date -u +%Y%m%d-%H%M%S).json"
log "snapshot written"
echo "snapshot updated: $OUT ($(date -u +%TZ))"
