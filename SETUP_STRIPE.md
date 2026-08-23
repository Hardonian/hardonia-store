# Finish Agent Skin Pack checkout — Stripe Payment Link setup

The Agent Skin Packs are fully built, registered in the catalog, and live in the
store at `/p/agent-skin-neon-sovereign` and `/p/agent-skin-heritage-quiet`.
The ONLY thing blocking live purchases is **real Stripe Payment Link URLs**
(the current `catalog.py` entries have `TODO_PASTE_REAL_STRIPE_PAYMENT_LINK`
placeholders, so checkout returns 503 "not configured yet").

## One-time: paste your real Stripe key

The running audit-api reads its key from:
  /mnt/ai-storage/ai-workspace/repos/ai-lab-audit-api/.env   (STRIPE_SECRET_KEY=)

Currently it is EMPTY (the home copy's `sk_test_...` key is a truncated
placeholder and was rejected by Stripe). Put your real secret key there:

  cd /mnt/ai-storage/ai-workspace/repos/ai-lab-audit-api
  # edit .env: STRIPE_SECRET_KEY=sk_live_xxx   (or sk_test_xxx for test mode)

## Generate the Payment Links (run once)

A ready script lives at /home/scott/hardonia.store/generate-stripe-links.py.
With a valid key in the .env above, run:

  cd /mnt/ai-storage/ai-workspace/repos/ai-lab-audit-api
  .venv/bin/python /home/scott/hardonia.store/generate-stripe-links.py

It prints two `buy.stripe.com/...` URLs. Paste them into
  /mnt/ai-storage/ai-workspace/repos/ai-lab-audit-api/app/catalog.py
replacing the TODO_PASTE_REAL_STRIPE_PAYMENT_LINK values, then:

  systemctl --user restart ai-lab-audit-api

## Verify

  curl -s -m5 -X POST http://127.0.0.1:8011/api/checkout \
    -H 'content-type: application/x-www-form-urlencoded' \
    -d 'sku=skin-neon-sovereign'
  # expect HTTP 303 + Location: https://buy.stripe.com/...

Buyers reach the pack from:
  https://aiautomatedsystems.ca/p/agent-skin-neon-sovereign
The skin file is already downloadable:
  https://aiautomatedsystems.ca/product-assets/agent-skin-neon-sovereign/skin.yaml

## Autonomous loop (already running)

Nightly cron `overnight-agent-skin-factory` generates 2 new skin packs,
writes valid skin.yaml + product.json (draft, readiness 40), and queues a
social blurb. Promote drafts to `ready` (readiness 95) after a glance.
