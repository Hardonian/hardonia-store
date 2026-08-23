# Support Agent Onboarding — Hardonia

You are the human in the loop behind the AU support bot. The bot handles tier-1; you handle
escalations, billing disputes, and anything the bot flags. Read `support-ops.md` first.

## Tools you use
- GitHub Issues: `Hardonian/hardonia-compute-api` — primary tracker.
- Support email: scottrmhardie@gmail.com.
- This KB: `faq-customer.md` (public-safe), `faq-internal.md` (internal), `runbooks/`.
- Live context: `kb/feeds/snapshot.json` (financial/compute/legal/intel snapshot).

## Day 1
- [ ] Read `brand.md` — voice is direct, no hype, no theatre.
- [ ] Read `faq-customer.md` and `faq-internal.md` cold; note anything stale → file a KB issue.
- [ ] Shadow the AU bot: read `au-support-bot.md`. Know its guardrails so you can catch bypasses.
- [ ] Understand severity + SLA in `support-ops.md` (current SLA: 2-3 business days).

## Response rules
- Use `templates/reply-customer.md`. Fill its placeholders, never invent product behavior.
- Billing/refunds → Gumroad owns the card; point customer to Gumroad, don't promise a Hardonia refund.
- If the bot escalated, the thread already has the transcript — don't re-ask what the bot gathered.
- Capacity questions (e.g. "are private inference slots full?") → check `feeds/snapshot.json` compute block.

## Escalation triggers (straight to Scott)
- Legal / abuse / minor-safety concerns.
- Suspected credential leak or unauthorized access to an API key.
- Anything referencing internal IPs, tokens, or server topology from a customer.
- Revenue-impacting incident (storefront/domain down) — also page `runbooks/dns-tls.md`.
