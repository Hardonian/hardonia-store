# ops/health.md — unified scale-operations health

One page for "is the business operating?" Pulls from the same live feeds the bot uses.

## Live signals (from feeds/snapshot.json, refreshed every 30m by kb-ecosystem-update.timer)
- Domain: aiautomatedsystems.ca NS = Cloudflare? (dig) — tunnel orange CNAME.
- Origin: Caddy :443 → 8020 = 200? (tls-status.sh)
- Compute: free_vram_pct, capacity_ok (EPYC GPU). <10% → bot pauses key issuance.
- Intel: block flag, top themes, best predicted offer (from ai-lab/reports/intel).
- Analytics: visitors_24h, conversion_pct, top_product.
- Legal: minor_safety_clear, open_flags.
- KB: kb-lint PASS, au_bot guardrails intact.
- Bot: au_bot_server :8071 /au/health = ok.

## How to read it at 2am
1. Domain down? → runbooks/dns-tls.md (usually dashboard tunnel 503 or grey A).
2. Bot answering wrong? → kb-regression.md (snapshot stale or FAQ contradiction).
3. Capacity red? → pause new key sales, flag Scott, check EPYC.
4. Legal flag? → kill-switch (ops/kill-switch.md): bot auto-escalates, go quiet on thread.

## Single command for the whole picture
  bash /home/scott/hardonia.store/kb/tools/kb-ci.sh --report
(prints DOMAIN / ORIGIN / COMPUTE / INTEL / KB / BOT status lines)
