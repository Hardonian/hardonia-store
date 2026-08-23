# ops/access-matrix.md — who can do what as Hardonia scales

Source of truth for role-based access. Keep current; the AU bot + support-ops reference this.

## Roles
| role | who | can |
|------|-----|-----|
| Founder/Owner | Scott | everything: DNS, tunnel, Caddy, keys, legal, finance, bot deploy |
| Support Agent | TBD | answer S3, triage S2, file GitHub issues, rotate keys (via Scott) |
| Bot (AU) | automated | tier-1 auth Q&A, structured escalation; NEVER issue/rotate keys |
| Intel Agent | automated | write intel signals to ai-lab/reports/intel; never touches KB directly |

## Hard boundaries (enforced by code + process)
- Key ISSUANCE / ROTATION = admin-only (human, Scott). Bot routes to human; never self-serves.
- Caddyfile / DNS / tunnel = Scott only (sudo interactive on epyc). Not delegated.
- KB edits = any role via PR; merged by Scott. Bot reads KB, does not write it.
- Financial refunds = Gumroad only. No Hardonia-side refund authority.
- Legal/abuse/minor-safety = escalate to Scott, bot goes quiet.

## Service accounts (non-human)
- cloudflared tunnel: token-run, started by systemd. Dashboard controls ingress.
- ecosystem-update: systemd timer, writes feeds/snapshot.json only.
- au_bot_server: systemd user service, loopback port 8071, fronted by Caddy /au/.
- kb-ci: systemd timer, runs kb-lint + ecosystem-update gate.

## Onboarding a new role
1. Add row here. 2. Assign GitHub team + support email alias. 3. Read onboarding-*.md.
4. For support: shadow AU bot, learn guardrails, get issue-filing access.
