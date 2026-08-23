# Ecosystem — The Living Knowledge System

Per Scott's directive: KB, real-time intel, site analytics, financial, internal compute, and legal
are not separate silos. They are ONE interacting system. This doc defines the wiring so the AU bot,
support agents, and ops all run on the same live truth.

## Architecture (data flow)
```
intel-agent findings ─┐
site analytics ──────┼─► tools/ecosystem-update.sh ─► kb/feeds/snapshot.json
financial / costs ───┤                                     │
compute (GPU/VRAM) ──┤                                     │ reads
legal flags ─────────┘                                     ▼
                                                       AU bot (tier-1)
                                                       support-ops (triage)
                                                       runbooks (actions)
```
- `kb/feeds/snapshot.json` is the single live context object. Everyone reads it; only
  `ecosystem-update.sh` writes it. No doc edits by hand for numeric state.
- The KB (faq/runbooks) is the qualitative truth. The snapshot is the quantitative truth.
  Bot answers = KB (how) + snapshot (now).

## snapshot.json shape (contract)
{
  "generated_at": "ISO8601",
  "intel":     { "block": false, "active_flags": [], "note": "" },
  "analytics": { "visitors_24h": 0, "top_product": "", "conversion_pct": 0 },
  "financial": { "gumroad_fees_pct": 10, "burn_monthly": 0, "revenue_monthly": 0,
                 "margin_by_product": {} },
  "compute":   { "gpu_util_pct": 0, "free_vram_pct": 0, "active_keys": 0,
                 "capacity_ok": true },
  "legal":     { "open_flags": [], "minor_safety_clear": true }
}

## Wiring rules
1. INTEL → if `intel.block` true for a product, bot suppresses that product's answers + escalates.
   Manual override: `feeds/intel-flag.json` (`block:true`) → bot pauses all auth answers (incident).
2. ANALYTICS → `top_product` + `conversion_pct` feed launch/FAQ priority (what to document next).
3. FINANCIAL → bot never quotes margins; ops uses it for deprecation/capacity pricing decisions.
4. COMPUTE → `capacity_ok=false` ⇒ bot says "slots limited" and support pauses new key issuance.
5. LEGAL → any `open_flags` or `minor_safety_clear=false` ⇒ hard escalate to Scott, bot goes quiet
   on that thread (kill-switch, `ops/kill-switch.md`).
6. KB-CI → `tools/kb-ci.sh` (timer `kb-ci.timer`) runs lint + snapshot + guardrail probes every
   15 min; fails loud on regression so a broken KB never reaches the bot.

## update.sh responsibilities
- `tools/ecosystem-update.sh`: pulls each feed (intel agent output, analytics export,
  financial tally, compute probe on EPYC, legal flag file), merges into snapshot.json atomically,
  logs to `feeds/update.log`. Idempotent, rerunnable, fails loud if a feed is missing.
- Schedule: `kb-ecosystem-update.timer` every 30 min + on boot. Keep last 7 snapshots in `feeds/history/`.
- Bot intake: `au-bot-server.service` (port 8071) → Caddy `/au/` → storefront/chat. Escalations
  auto-file via `github_issue.py` to `Hardonian/hardonia-compute-api` (label `auth`).

## Why this matters at scale
Without the loop, the bot goes stale the day after launch and agents guess. With it, a GPU
saturation, a ComfyUI CVE intel flag, or a margin dip automatically changes what the bot says and
what support escalates — no meeting required. The KB is the nervous system; the feeds are its senses.
