#!/usr/bin/env bash
# analytics-bridge.sh — aggregate storefront SQLite events into kb/feeds/analytics.json.
# Real conversion data (not zeros). Called by ecosystem-update.sh so the snapshot carries it.
set -Eeuo pipefail

DB="/home/scott/ai-lab/revenue-os/revenue-os.db"
OUT="/home/scott/hardonia.store/kb/feeds/analytics.json"
TMP="${OUT}.tmp"

if [[ ! -f "$DB" ]]; then
  echo '{"total_page_views":0,"views_today":0,"unique_visitors":0,"checkout_clicks":0,"checkout_clicks_today":0,"conversions":0,"conversion_rate":0,"total_revenue_cents":0,"top_pages":"","generated_at":"'"$(date -u +%FT%TZ)"'"}' >"$TMP"
  mv "$TMP" "$OUT"
  exit 0
fi

python3 - "$DB" "$TMP" <<'PY'
import sqlite3, json, sys, datetime
db, tmp = sys.argv[1], sys.argv[2]
today = datetime.date.today().isoformat()
try:
    c = sqlite3.connect(db)
    q = lambda s, a=(): c.execute(s, a).fetchone()[0]
    total_views = q("SELECT count(*) FROM events WHERE event_type IN ('product_view','page_view')") or 0
    views_today = q("SELECT count(*) FROM events WHERE event_type IN ('product_view','page_view') AND date(created_at)=?", (today,)) or 0
    checkout = q("SELECT count(*) FROM events WHERE event_type='checkout_click'") or 0
    checkout_today = q("SELECT count(*) FROM events WHERE event_type='checkout_click' AND date(created_at)=?", (today,)) or 0
    # conversions = purchases recorded
    conv = q("SELECT count(*) FROM purchases") or 0
    rev = q("SELECT coalesce(sum(amount_cents),0) FROM purchases") or 0
    top = c.execute("SELECT product_slug,count(*) n FROM events WHERE product_slug IS NOT NULL GROUP BY product_slug ORDER BY n DESC LIMIT 3").fetchall()
    top_pages = ", ".join(f"{r[0]}({r[1]})" for r in top)
    rate = round(100.0 * conv / total_views, 2) if total_views else 0.0
    out = {
        "total_page_views": total_views,
        "views_today": views_today,
        "unique_visitors": 0,  # events table has no stable visitor id; left 0 (honest)
        "checkout_clicks": checkout,
        "checkout_clicks_today": checkout_today,
        "conversions": conv,
        "conversion_rate": rate,
        "total_revenue_cents": rev,
        "top_pages": top_pages,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
except Exception as e:
    out = {"error": str(e), "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
json.dump(out, open(tmp, "w"), indent=2)
PY

mv "$TMP" "$OUT"
echo "analytics.json updated from storefront events"
