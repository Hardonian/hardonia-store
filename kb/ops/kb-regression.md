# ops/kb-regression.md — never ship a broken KB

The KB is the bot's brain. A regression (stale answer, wrong price, leaked internal detail) makes
the bot lie or leak. This gate prevents that.

## Definition of a KB regression
- faq-customer.md contradicts runbooks/ or the actual product folder.
- An internal-only fact (IP, token, margin, VRAM number) appears in faq-customer.md.
- A product in runbooks/catalog.md has no matching FAQ entry.
- snapshot.json drives a wrong bot answer (e.g. capacity_ok true but keys actually exhausted).
- au_bot.py guardrails weakened (leak/minor-safety/abuse checks removed or loosened).

## The gate (kb-ci.sh, runs on timer + pre-commit)
1. `tools/kb-lint.sh` — no unresolved tokens; templates excluded.
2. `tools/ecosystem-update.sh` — regenerate snapshot from live feeds (fails if a feed corrupt).
3. `python3 tools/au_bot.py "<guardrail probes>"` — must still escalate on leak/minor/abuse.
4. FAQ↔catalog integrity: every catalog product slug has a FAQ mention OR is reference-only.
5. Internal-leak scan: faq-customer.md must NOT match IP/token/internal patterns.

## On regression
- kb-ci fails → blocks the commit/merge, posts the diff to the operator.
- The human fixes the source doc (faq/runbook), not the bot's copy.
- Re-run kb-ci green before merge. Bot hot-reloads on file change, so no redeploy needed.

## Why pre-commit + timer (not just manual)
Timer catches feed drift (e.g. compute API behavior change) even if nobody edits the KB.
Pre-commit catches human edits before they reach the bot. Both = defense in depth.
