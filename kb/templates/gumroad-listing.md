# Template — Gumroad Listing Publish

Product: {{SLUG}}
Script: /home/scott/ai-lab/productization/gumroad-listings/publish_gumroad_v3.py
Token: /home/scott/.gumroad/token (scottrmhardie.gumroad.com)

## Checklist
- [ ] Listing copy finalized (title, description, price, cover)
- [ ] Product assets zipped + path correct
- [ ] API key delivery wired for access products (checkout-api)
- [ ] Under the 10-CREATE / 24h cap (count today's creates first)
- [ ] Not relying on API delete (unreliable) — persist instead

## Publish
```
python3 /home/scott/ai-lab/productization/gumroad-listings/publish_gumroad_v3.py \
  --slug {{SLUG}} --title "{{TITLE}}" --price {{PRICE}}
```
Or let the cron run it: gumroad-publish.timer @14:00 daily.

## Verify
- [ ] Listing live at scottrmhardie.gumroad.com
- [ ] Test purchase (own account) → receipt + download/key delivered
- [ ] AU bot FAQ matches listing claims
