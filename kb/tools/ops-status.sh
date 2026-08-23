#!/usr/bin/env bash
# ops-status.sh — one-glance health of the whole Hardonia system.
# Prints: domain, origin, tunnel, storefront, AU bot, intel/analytics/financial feeds, services.
set -Eeuo pipefail
echo "===== Hardonia Ops Status ($(date -u +%FT%TZ)) ====="
# domain
ns=$(dig +short aiautomatedsystems.ca NS 2>/dev/null | head -1)
echo "DOMAIN : ${ns:-NONE} $(echo "$ns" | grep -q cloudflare && echo '[Cloudflare OK]' || echo '[NOT cf]')"
# origin (content-based, self-signed cert quirk)
if curl -sk --resolve aiautomatedsystems.ca:443:127.0.0.1 https://aiautomatedsystems.ca/ 2>/dev/null | grep -qiE '<html|hardonia'; then
  echo "ORIGIN : HTTP 200 (app HTML served)"
else echo "ORIGIN : NOT serving HTML"; fi
# services
for u in storefront au-bot-server caddy cloudflared ollama-router n8n comfyui qdrant redis postgres; do
  st=$(systemctl --user is-active "$u.service" 2>/dev/null || systemctl is-active "$u" 2>/dev/null || echo "-")
  printf "SVC    : %-16s %s\n" "$u" "$st"
done
# AU bot
curl -s --max-time 3 127.0.0.1:8071/au/health >/dev/null 2>&1 && echo "AU BOT : up" || echo "AU BOT : DOWN"
# feeds
python3 - <<'PY'
import json,os
kb="/home/scott/hardonia.store/kb/feeds"
for f in ("intel","analytics","financial","legal"):
    p=os.path.join(kb,f+".json")
    try:
        d=json.load(open(p))
        if f=="analytics": print(f"FEED   : {f}: views={d.get('total_page_views')} conv={d.get('conversions')}")
        elif f=="financial": print(f"FEED   : {f}: revenue_cents={d.get('total_revenue_cents')} products={len(d.get('products',[]))}")
        elif f=="intel": print(f"FEED   : {f}: block={d.get('block')} themes={len(d.get('themes',[]))}")
        else: print(f"FEED   : {f}: minor_safety_clear={d.get('minor_safety_clear')}")
    except Exception as e:
        print(f"FEED   : {f}: ERROR {e}")
PY
# system inventory (machine-readable KB)
INV="/home/scott/hardonia.store/kb/system-inventory.json"
if [ -f "$INV" ]; then
  python3 - "$INV" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    svc=d.get("services",{})
    print(f"INV    : {len(svc)} services, {len(d.get('workers',{}))} workers, {len(d.get('cron_groups',{}))} cron groups")
    for name,info in svc.items():
        port=info.get("port")
        print(f"  - {name}:{port}")
except Exception as e:
    print(f"INV    : ERROR {e}")
PY
fi
echo "===== end ====="
