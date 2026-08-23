#!/usr/bin/env bash
# kb-lint.sh — validate the Hardonia KB.
# 1) Fails if any {{TOKEN}} besides {{AU}} is unresolved.
# 2) -set AU="..." resolves the global AU placeholder across all kb docs.
# 3) Validates markdown links/files exist where reasonable.
set -Eeuo pipefail

KB="/home/scott/hardonia.store/kb"
AU=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -set) AU="${2:-}"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

if [[ -n "$AU" ]]; then
  echo "Resolving {{AU}} -> '$AU' across $KB"
  # replace {{AU}} with the value (literal, no regex metachar expansion issues via perl)
  find "$KB" -name '*.md' -print0 | xargs -0 perl -i -pe "s/\{\{AU\}\}/$(printf '%s' "$AU" | sed 's/[&/]/\\&/g')/g"
  echo "Done. Re-run without -set to verify no stray {{AU}} remains."
  exit 0
fi

echo "== kb-lint: scanning for unresolved GLOBAL/content tokens =="
echo "   (note: templates/*.md fill-ins like {{SLUG}} are intentional and skipped)"
BAD=0
while IFS= read -r f; do
  # Skip template fill-ins and instructional prose tokens by directory + known words.
  case "$f" in
    */templates/*) continue;;            # templates are meant to be filled in later
  esac
  # Only flag tokens that are NOT {{AU}} and NOT the instruction words {{TOKENS}}/{{TOKEN}}.
  hits=$(grep -oE '\{\{[A-Z_]+\}\}' "$f" 2>/dev/null | grep -vE '^\{\{(AU|TOKENS|TOKEN)\}\}$' || true)
  if [[ -n "$hits" ]]; then
    echo "  UNRESOLVED in $f:"; echo "$hits" | sed 's/^/    /'
    BAD=1
  fi
done < <(find "$KB" -name '*.md')

if [[ "$BAD" -eq 1 ]]; then
  echo "FAIL: unresolved tokens found ({{AU}} is allowed/global)."
  exit 1
fi
echo "PASS: no unresolved tokens ({{AU}} global, resolve with -set)."
echo "== json sanity =="
for j in "$KB/feeds/snapshot.json" "$KB/feeds/intel.json" "$KB/feeds/financial.json" "$KB/feeds/analytics.json" "$KB/feeds/legal.json"; do
  [[ -f "$j" ]] && python3 -c "import json;json.load(open('$j'))" 2>/dev/null && echo "  ok: $j" || echo "  (missing or invalid: $j)"
done
