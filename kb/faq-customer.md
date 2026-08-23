# FAQ — Customer (public-safe)

These answers are bot-served and human-reviewed. Keep them current; the AU bot reads this file.
Do NOT put internal-only info here. Internal-only Q&A is in `faq-internal.md`.

## Products & access
**Q: How do I get my download / API key after buying?**
A: Right after checkout you're sent to a confirmation page with a claim link, and you get a receipt email. Open the claim link (or visit the link from your receipt) and enter the email you used at checkout — we verify it against your Stripe payment, then release your download or API key. For access products (Private Inference, Compute API) your key is shown on the claim page and emailed to you. Lost the link? Use the claim URL from your receipt email, or contact support with your Stripe order ID.

**Q: What is Private Inference Access?**
A: Private, local-first Ollama/ComfyUI access run on Hardonia infrastructure — your prompts and
data stay private; we do not train on them. You get an API key and endpoint docs.

**Q: What is Hardonia Compute API Access?**
A: Programmatic access to Hardonia compute (Ollama/ComfyUI endpoints) via API key. Usage docs are
in the product folder `products/hardonia-compute-api-access/`. Rate limits are per-plan.

**Q: Do the ComfyUI / n8n packs need my own hardware?**
A: The packs are workflow + prompt bundles you run on your own ComfyUI/n8n instance. The
Subscription adds new workflows monthly. AI Portrait Studio runs locally/privately.

**Q: Is my data private?**
A: Yes for inference/portrait products — local-first, no training on your data. See
`products/legal/` for terms. We do not sell customer data.

## Billing & refunds
**Q: I need a refund.**
A: Payments are processed through Stripe. For refunds, contact support with your Stripe order ID (starts with `cs_`) and we'll review per our refund policy. We don't hold card data; Stripe handles the payment rails.

**Q: How does the ComfyUI subscription renew?**
A: Subscriptions are billed through Stripe on a monthly cycle. Cancel anytime from the billing portal linked in your receipt email; you keep everything you've already downloaded.

## Technical
**Q: The download link is 404 / key not working.**
A: Open a support ticket with your Stripe order ID (starts with `cs_`) and the error. The claim link is tied to the email you used at checkout — make sure it matches. We treat failed delivery as S2 (1 business day).

**Q: Can I use the API from behind a corporate proxy / firewall?**
A: Endpoints are standard HTTPS. If your network blocks them, that's on your side; we can't change
your firewall. The storefront itself is served via Cloudflare tunnel (see status if down).

## API keys & access (AU — Auth/Access Unit)
**Q: How do I authenticate to the Hardonia Compute API?**
A: Send your key in the `X-API-Key` header. Your key is shown on the claim page right after purchase and emailed to you; it's also available again via your claim link. Missing header → 401.

**Q: I get 403 "Invalid API key".**
A: Check the key is copied exactly (no trailing spaces) and the product matches. If it still 403s
after a clean copy, your key may be inactive or credits exhausted — open a GitHub issue (S2) with
your order ID and last 4 key chars; we'll verify and reissue if needed.

**Q: I get 429 "Too many attempts" / "Rate limit exceeded".**
A: Two causes: (1) brute-force cooldown — after ~25 bad tries/60s the key locks out 5 min; wait and
retry with the correct key. (2) rate limit — you exceeded your plan's `rate_per_min` (default 30);
back off ~a minute or request a higher plan. AU never reveals the threshold numbers to others.

**Q: My credits/quota ran out.**
A: Compute API is prepaid (starter/growth/scale/enterprise). Top up by purchasing a credit pack or higher plan; your key balance updates after checkout and claim.

**Q: I lost my key / think it leaked.**
A: Open a GitHub issue (S2) "rotate my key" with your order ID. We invalidate the old key and issue
a new one. Never paste your full key in public; give last 4 chars only. (AU routes this to a human —
key rotation is admin-only and must not be automated.)

## Product catalog (what each product is + how access works)
**Q: What is AI Lab Health Report? ($19)**
A: A one-page operational report on your AI lab — GPU/utilization/health signals with prioritized
fixes. Delivered as a downloadable PDF/report after checkout via your claim link.

**Q: What is the ComfyUI Workflow Pack? ($49)**
A: A bundle of production-ready ComfyUI workflows + prompt presets you run on your own ComfyUI
instance. Download via your claim link after purchase; no key needed.

**Q: What is the ComfyUI Workflow Subscription? ($29/mo)**
A: Monthly addition of new ComfyUI workflows to the pack. Billed through Stripe; cancel anytime from
the billing portal in your receipt and keep what you've downloaded.

**Q: What is AI Portrait Studio? ($19–$49)**
A: A local/private portrait-generation workflow (ComfyUI). Runs on your hardware — private, no
training on your data. Download via your claim link after purchase.

**Q: What is the n8n Automation Kit? ($39)**
A: Prebuilt n8n automation workflows you import into your own n8n instance. Download via your claim
link; runs on your infrastructure.

**Q: What is Local AI Ops Checklist? ($29)**
A: A setup/hardening checklist for running local AI (Ollama/ComfyUI/Caddy/tunnel) safely. Delivered
as a downloadable checklist/runbook via your claim link.

**Q: What is the AI Lab Power Bundle? ($59)**
A: Bundle of AI Lab Health Report + Local AI Ops Checklist (saves $19 vs buying separate). Download
both via your claim link.

**Q: What is Autonomous Revenue Loop? ($499 one-time / $997 with implementation / $750–$2500/mo retainer)**
A: A done-with-you system that builds hands-off revenue loops from your AI assets. Access/implementation
is coordinated via GitHub issue + email after purchase (enterprise-style onboarding).

**Q: What is Hardonia Compute API Access? ($20 starter / $99 pro / $299 enterprise)**
A: Programmatic access to Hardonia compute (Ollama/ComfyUI) via API key. Your key is shown on the
claim page and emailed to you after checkout; rate limits and credits are per-plan. Usage docs in the product folder.

**Q: What is Private Inference Access? ($9/mo or $0.10 per 1k tokens)**
A: Private, local-first inference (Ollama/ComfyUI) on Hardonia infrastructure — your prompts/data stay
private, no training on them. You get an API key + endpoint docs on your claim page and by email after checkout.

