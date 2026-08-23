# Runbook — Storefront, Checkout & Gumroad Ops

## Storefront
- Code: hardonia.store/storefront (Python service). Loads API_KEY from
  `~/.config/systemd/user/storefront.service.d/env.conf` → storefront/.env.
- Checkout API: `/home/scott/.local/etc/hardonia-checkout-api.env`.
- When debugging live services, ALWAYS check the running process cmdline + `/proc/$PID/environ`
  BEFORE editing app code. (Lesson from 2026-07-11 storefront wipe — never write_file over a
  live main.py; use patch.)

## Delivery model
- All products digital, delivered via Gumroad (download link + API key in receipt).
- Access products: key generated/validated by checkout-api; key docs in product folder.
- Subscription: Gumroad recurring; new workflows dropped to buyer library monthly.

## Gumroad ops
- Live token: `/home/scott/.gumroad/token` (acct scottrmhardie.gumroad.com).
- HARD 10-CREATE / 24h cap. API deletes unreliable (persist), list pagination buggy.
- Reliable path: wait cap reset + `publish_gumroad_v3.py` (cron gumroad-publish.timer @14:00).
- Script: `/home/scott/ai-lab/productization/gumroad-listings/publish_gumroad_v3.py`.

## Billing reality (support must know)
- Hardonia does NOT hold card data. Refunds/chargebacks = Gumroad's job.
- Never promise a Hardonia-side refund in writing.

## Failure modes
- Download 404 → check Gumroad listing asset + product deliverables/ path; open S2 issue.
- Key not delivered → check checkout-api env + storefront service status; open S2 issue.
- Storefront down → `runbooks/dns-tls.md` (domain/DNS), then storefront service restart.
