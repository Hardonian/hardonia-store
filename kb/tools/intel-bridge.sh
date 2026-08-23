#!/usr/bin/env bash
# intel-bridge.sh — pull REAL predictive-winrate into kb/feeds/intel.json.
# ecosystem-update.sh already reads cache_predictions/latest.json, but this makes intel.json
# a first-class real feed (not a stub) so the bot + proactive loop can rely on it.
set -Eeuo pipefail
SRC="/home/scott/ai-lab/dashboard/cache_predictions/latest.json"
OUT="/home/scott/hardonia.store/kb/feeds/intel.json"
TMP="${OUT}.tmp"

if [[ ! -f "$SRC" ]]; then
  echo '{"block":false,"active_flags":[],"note":"no predictive-winrate source","themes":[],"best_offer":null,"generated_at":"'"$(date -u +%FT%TZ)"'"}' >"$TMP"
  mv "$TMP" "$OUT"; exit 0
fi

python3 - "$SRC" "$TMP" <<'PY'
import json, sys
src, tmp = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(src))
    preds = d.get("predictions", [])
    # normalize: some entries are {path,percent,trend} (url paths), some {offer,win_rate}
    themes = []
    best = None
    best_wr = -1
    for p in preds:
        offer = p.get("offer") or p.get("path") or p.get("name") or str(p)[:40]
        wr = p.get("win_rate") or p.get("percent") or 0
        try: wr = float(wr)
        except Exception: wr = 0.0
        themes.append({"offer": offer, "win_rate": round(wr, 2)})
        if wr > best_wr:
            best_wr, best = wr, offer
    out = {"block": False, "active_flags": [],
           "themes": themes[:10],
           "best_offer": best,
           "best_win_rate": round(best_wr, 2) if best else None,
           "generated_at": d.get("updated_at") or __import__("datetime").datetime.utcnow().isoformat()+"Z",
           "note": "live predictive-winrate"}
except Exception as e:
    out = {"block": False, "active_flags": [], "themes": [], "best_offer": None,
           "note": "bridge error: %s" % str(e)[:80],
           "generated_at": __import__("datetime").datetime.utcnow().isoformat()+"Z"}
json.dump(out, open(tmp, "w"), indent=2)
PY
mv "$TMP" "$OUT"
echo "intel.json updated from predictive-winrate ($(python3 -c "import json;d=json.load(open('$OUT'));print(len(d.get('themes',[])))") themes)"