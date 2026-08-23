# Template — Product Launch Checklist

Product: {{SLUG}} / {{TITLE}}
Owner: {{OWNER}}

## Pre-launch
- [ ] product.json complete (title, type, price, owner)
- [ ] README + WALKTHROUGH + DELIVERABLE-SNAPSHOT + PREVIEW + SUPPORT written (no theatre)
- [ ] deliverables/ path verified, assets present
- [ ] Gumroad listing draft (copy from templates/gumroad-listing.md)
- [ ] FAQ entry added to faq-customer.md
- [ ] catalog.md row added
- [ ] legal/ terms reference if access/subscription

## Launch
- [ ] Run publish_gumroad_v3.py (respect 10/24h cap) OR wait cron @14:00
- [ ] Verify receipt delivers download/key
- [ ] AU bot reloads KB (hot-reload on file change)
- [ ] Post to channels per launch.md

## Post-launch
- [ ] 24h: check analytics top_product + conversion in feeds/snapshot.json
- [ ] 7d: review support issues → FAQ gaps
- [ ] 30d: financial margin_by_product check
