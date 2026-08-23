# Hardonia Support & Knowledge Base

Single source of truth for everything customer-facing and team-facing as Hardonia scales.
Every doc here is real — grounded in the actual product catalog, storefront, and support channels.
No invented product names, no theatre.

## How to use this KB
- Support agents: start at `faq-customer.md` and `faq-internal.md`, escalate per `support-ops.md`.
- New hires: read `onboarding-team.md` then `onboarding-support-agent.md`.
- Bot engineers: the AU support bot spec is `au-support-bot.md` (soul + guardrails + routing).
- Ops: `runbooks/` covers catalog, storefront, and the DNS/TLS recovery recipe.
- Templates: `templates/` — copy, fill the placeholders, ship.

## Brand constants (do not edit per-doc; defined in `brand.md`)
- Brand: Hardonia
- Storefront: hardonia.store (Gumroad-backed digital products)
- Support email: scottrmhardie@gmail.com
- GitHub issues: Hardonian/hardonia-compute-api
- AU = Auth/Access Unit   <-- Hardonia's customer-facing auth & key-lifecycle support bot

## Product catalog (real, as of 2026-07)
| slug | title | type |
|------|-------|------|
| private-inference-access | Private Inference Access | one-time / access |
| hardonia-compute-api-access | Hardonia Compute API Access | API key / access |
| ai-lab-power-bundle | AI Lab Power Bundle | bundle |
| n8n-automation-kit | n8n Automation Kit | pack |
| local-ai-ops-checklist | Local AI Ops Checklist | pack |
| comfyui-workflow-pack | ComfyUI Workflow Pack | pack |
| comfyui-workflow-subscription | ComfyUI Workflow Subscription | subscription |
| ai-portrait-studio | AI Portrait Studio | pack |
| ai-lab-health-report | AI Lab Health Report | report |
| autonomous-revenue-loop | Autonomous Revenue Loop | playbook |
| legal | Legal (licenses/terms) | reference |

## Doc map
- brand.md — voice, constants, do/don't
- onboarding-team.md — new team member checklist
- onboarding-support-agent.md — support role checklist
- support-ops.md — triage, SLA, escalation, severity
- faq-customer.md — public FAQ (safe to ship)
- faq-internal.md — internal-only FAQ (pricing, infra, incidents)
- au-support-bot.md — bot soul script, guardrails, routing, fallback
- runbooks/catalog.md — product catalog + packaging ownership
- runbooks/storefront.md — storefront + checkout + Gumroad ops
- runbooks/dns-tls.md — domain down recovery (Cloudflare tunnel recipe)
- templates/reply-customer.md — response templates
- templates/incident.md — incident postmortem template
- templates/launch.md — product launch checklist
- templates/gumroad-listing.md — Gumroad publish checklist
- tools/kb-lint.sh — verify no stray tokens; ecosystem-update.sh regenerates feeds/snapshot.json
- tools/au_bot.py — the AU bot engine (guardrails + FAQ routing + snapshot state)
- tools/au_bot_server.py — live intake server (loopback port 8071, /au/ask, /au/health)
- tools/github_issue.py — escalation -> Hardonian/hardonia-compute-api
- tools/kb-ci.sh — regression gate + unified health report (`kb-ci.sh --report`)
- ops/access-matrix.md — role-based access as we scale
- ops/kb-regression.md — never ship a broken KB (the gate)
- ops/health.md — unified scale-ops health page
- ops/kill-switch.md — pause the bot safely during incidents
- ops/caddy-au-snippet.txt — Caddy config to front /au/ behind the public site

## Maintenance rule
When a product changes, update `runbooks/catalog.md` first, then the affected FAQ entry.
The AU bot pulls answers from faq-customer.md + runbooks/ — keep those two current or the bot lies.
