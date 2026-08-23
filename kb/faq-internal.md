# FAQ — Internal (team only)

NOT customer-safe. Contains pricing, infra, capacity, incident, and financial context.
The AU bot must NEVER serve these answers. Internal-only by design.

## Pricing & margins
**Q: What's our margin on Gumroad products?**
A: Gumroad takes a flat fee (~10% incl. processing at current tier). Net margin per sale ≈ 90%
minus any delivery compute cost. Live numbers in `feeds/snapshot.json` → financial block.
Don't quote exact margins to customers; say "digital product, priced for value."

**Q: Can we discount / run a sale?**
A: Yes, via Gumroad. Coordinate with Scott; update `runbooks/catalog.md` price column after.
Hard cap: don't go below cost-of-compute for access products (see compute block).

## Infra & capacity
**Q: Are we at GPU capacity for Private Inference / Compute API?**
A: Check `feeds/snapshot.json` → compute block (GPU util, free VRAM, active keys).
EPYC hosts P40/V100/3060. If free VRAM < threshold, pause new key issuance and flag Scott.
The bot should answer "slots limited, check back" — NOT expose VRAM numbers to customers.

**Q: Why is the site down / TLS error?**
A: Usually grey-A vs Cloudflare tunnel, or Caddy cert. Runbook: `runbooks/dns-tls.md`.
The 2026-07-11 incident root cause: empty Caddy cert store (fixed via `tls internal`) + grey A
bypassing the live tunnel. Fix = delete grey A, let tunnel create orange CNAME. No token needed.

## Legal & compliance
**Q: Minor-safety / abuse report?**
A: Zero tolerance. Any minor-safety, non-consensual, or abuse signal → escalate to Scott
immediately, do not engage the bot, preserve the thread. See `au-support-bot.md` guardrails.

**Q: What can we promise customers legally?**
A: Privacy for inference/portrait (local-first). We do NOT promise uptime SLAs, 24/7, or refunds.
Terms live in `products/legal/`. Don't invent warranties.

## Financial & ops
**Q: What's our burn / cost per month?**
A: See `feeds/snapshot.json` → financial block (EPYC power, storage, domain, Gumroad fees).
If cost-per-product > revenue for 2 consecutive months, flag for deprecation review.

**Q: How do intel findings feed support?**
A: The intel agent writes findings to `feeds/snapshot.json` → intel block. If an intel item
affects a product (e.g. "ComfyUI X exploit"), the bot suppresses related answers and escalates.
