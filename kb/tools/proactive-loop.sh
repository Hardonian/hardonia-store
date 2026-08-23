#!/usr/bin/env bash
# proactive-loop.sh — turn intel/analytics into action (not just a dashboard).
# Runs every 30 min via proactive-loop.timer. Acts on:
#  1. docs gap: top product by views with NO FAQ entry -> open a 'docs-gap' issue (once).
#  2. capacity red: compute capacity_ok=false -> open/refresh a 'capacity' alert issue.
#  3. funnel stall: checkout_clicks>0 but conversions==0 for 24h -> 'funnel' issue.
# Idempotent: tracks opened issue state in feeds/proactive-state.json so it doesn't spam.
set -Eeuo pipefail
KB="/home/scott/hardonia.store/kb"
SNAP="$KB/feeds/snapshot.json"
STATE="$KB/feeds/proactive-state.json"
GH_ISSUE=1

state_get(){ python3 -c "import json;print(json.load(open('$STATE')).get('$1',''))" 2>/dev/null || echo ""; }
state_set(){ python3 - "$STATE" "$1" "$2" <<'PY'
import json,sys
p,a,v=sys.argv[1:4]
try: d=json.load(open(p))
except Exception: d={}
d[a]=v
json.dump(d,open(p,'w'),indent=2)
PY
}

open_issue(){
  # $1 title, $2 body, $3 label
  if [[ "$GH_ISSUE" != "1" ]]; then echo "dryrun"; return 0; fi
  python3 "$KB/tools/github_issue.py" --title "$1" --body "$2" --label "$3" 2>&1 | tail -1 || true
}

# ---- 1. docs gap ----
top=$(python3 -c "import json;d=json.load(open('$SNAP'));print(d.get('analytics',{}).get('top_pages','').split('(')[0].strip())" 2>/dev/null)
faq_hit=$(grep -ci "$top" "$KB/faq-customer.md" 2>/dev/null | head -1 | tr -d '[:space:]' || true)
faq_hit=${faq_hit:-0}
if [[ -n "$top" && "${faq_hit}" -eq 0 ]]; then
  prev=$(state_get "docs_gap_$top")
  if [[ "$prev" != "opened" ]]; then
    open_issue "[docs-gap] '$top' is a top-viewed product with no FAQ entry" \
      "Analytics shows '$top' is a top product by views but faq-customer.md has no entry. Add an FAQ Q&A so AU can answer it. Ref: kb/runbooks/catalog.md" "docs-gap"
    state_set "docs_gap_$top" "opened"
  fi
else
  # product now has FAQ -> clear the flag so it can re-alert if it regresses
  [[ -n "$top" ]] && state_set "docs_gap_$top" "resolved"
fi

# ---- 2. capacity red ----
cap_ok=$(python3 -c "import json;print(json.load(open('$SNAP')).get('compute',{}).get('capacity_ok',True))" 2>/dev/null)
if [[ "$cap_ok" == "False" ]]; then
  prev=$(state_get "capacity_alert")
  if [[ "$prev" != "opened" ]]; then
    open_issue "[capacity] compute capacity saturated — pause new key issuance" \
      "snapshot.compute.capacity_ok=false. AU bot auto-pauses key issuance. Investigate EPYC GPU load." "capacity"
    state_set "capacity_alert" "opened"
  fi
else
  state_set "capacity_alert" "resolved"
fi

# ---- 3. funnel stall ----
cc=$(python3 -c "import json;d=json.load(open('$SNAP'));print(d.get('analytics',{}).get('checkout_clicks',0))" 2>/dev/null)
conv=$(python3 -c "import json;d=json.load(open('$SNAP'));print(d.get('analytics',{}).get('conversions',0))" 2>/dev/null)
if [[ "${cc:-0}" -gt 0 && "${conv:-0}" -eq 0 ]]; then
  prev=$(state_get "funnel_alert")
  if [[ "$prev" != "opened" ]]; then
    open_issue "[funnel] checkout clicks but 0 conversions — checkout likely broken" \
      "analytics: checkout_clicks=$cc, conversions=$conv. Check Gumroad/checkout-api wiring; AU cannot self-serve this." "funnel"
    state_set "funnel_alert" "opened"
  fi
else
  state_set "funnel_alert" "resolved"
fi

echo "proactive-loop: ran (docs_gap=$top faq_hit=$faq_hit cap_ok=$cap_ok cc=$cc conv=$conv)"
