# Support Operations — Hardonia

## Channels
- Primary: GitHub Issues `Hardonian/hardonia-compute-api`.
- Email: scottrmhardie@gmail.com.
- Tier-1 auto: AU support bot (see `au-support-bot.md`) on the storefront / email intake.

## Severity model
| Sev | Definition | Example | SLA |
|-----|------------|---------|-----|
| S1 | Revenue/domain down, data leak, abuse | hardonia.store unreachable, key leaked | same day |
| S2 | Paid customer blocked from deliverable | API key not delivered, download 404 | 1 business day |
| S3 | Question / how-to / non-blocking | "how do I use ComfyUI pack?" | 2-3 business days |
| S4 | Feedback / suggestion | "add a workflow for X" | backlog |

Current public SLA: 2-3 business days (S3 baseline). Do not promise tighter without staffing.

## Triage flow
1. Bot captures: product, symptom, what they tried, Stripe order ID (starts with `cs_`) if any.
2. Bot answers if match in `faq-customer.md` + `runbooks/`. Else tags severity + routes.
3. Human picks up S2+ from GitHub Issues. S4 → backlog label.
4. S1 → page Scott + open incident per `templates/incident.md` + run `runbooks/dns-tls.md` if domain.

## Escalation path
- S2/S3 → support agent → if blocked, Scott.
- S1 / legal / abuse / security → Scott directly, no queue delay.
- AU bot guardrail breach (customer got internal data) → Scott + kill the answer + log in `runbooks/`.

## Billing rules (hard)
- Hardonia does NOT hold card data. Payments are processed through Stripe.
- Refunds/chargebacks are handled via Stripe; contact support with your Stripe order ID and we'll review per policy.
- Never promise a Hardonia-side refund or credit in writing without Scott's approval.

## KB discipline
- Every resolved S2+ gets a FAQ or runbook update so the bot handles it next time.
- Stale answer found? Fix `faq-customer.md` or `runbooks/` — the bot reads those, not your head.
