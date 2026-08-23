#!/usr/bin/env bash
# financial-bridge.sh — pull REAL Gumroad revenue into kb/feeds/financial.json.
# The AU bot reads this to answer billing truthfully (no invented numbers).
set -Eeuo pipefail
OUT="/home/scott/hardonia.store/kb/feeds/financial.json"
TOK_FILE="/home/scott/.gumroad/token"
TMP="${OUT}.tmp"

if [[ ! -f "$TOK_FILE" ]]; then
  echo '{"total_revenue_cents":0,"products":[],"currency":"usd","generated_at":"'"$(date -u +%FT%TZ)"'","note":"no gumroad token"}' >"$TMP"
  mv "$TMP" "$OUT"; exit 0
fi
TOK=$(cat "$TOK_FILE")

RESP_FILE="${OUT}.gumroad.tmp"
curl -s --max-time 12 "https://api.gumroad.com/v2/products?access_token=$TOK" 2>/dev/null >"$RESP_FILE" || echo '{"success":false}' >"$RESP_FILE"

python3 - "$RESP_FILE" "$TMP" <<'PY'
import json, sys
resp_path, tmp = sys.argv[1], sys.argv[2]
try:
    with open(resp_path) as fh:
        d = json.load(fh)
    if not d.get("success"):
        out = {"total_revenue_cents": 0, "products": [], "currency": "usd",
               "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
               "note": "gumroad api error: %s" % str(d.get("message","?"))[:80]}
    else:
        prods = []
        total = 0
        for p in d.get("products", []):
            cents = int(p.get("price") or 0)
            sold = int(p.get("sales_count") or 0)
            rev = int((p.get("revenue") or 0))
            if not rev and sold:
                rev = cents * sold
            total += rev
            prods.append({"name": p.get("name"), "price_cents": cents,
                          "sold": sold, "revenue_cents": rev,
                          "url": p.get("url") or p.get("short_url")})
        out = {"total_revenue_cents": total, "products": prods, "currency": "usd",
               "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
               "note": "live gumroad"}
except Exception as e:
    out = {"total_revenue_cents": 0, "products": [], "currency": "usd",
           "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
           "note": "bridge error: %s" % str(e)[:80]}
json.dump(out, open(tmp, "w"), indent=2)
PY
rm -f "$RESP_FILE"
mv "$TMP" "$OUT"
echo "financial.json updated from Gumroad ($(python3 -c "import json;print(json.load(open('$OUT')).get('total_revenue_cents'))") cents)"