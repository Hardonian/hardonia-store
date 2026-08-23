# ops/kill-switch.md — pause the bot safely during incidents

The AU bot must be able to go quiet WITHOUT a redeploy. Two mechanisms, both live:

## 1. Snapshot-driven (automatic, no human in loop)
The bot reads feeds/snapshot.json every request. If either trips, /au/ask returns a safe
escalation and never runs the answer path:
- `legal.minor_safety_clear = false` → hard pause (abuse/legal incident).
- `intel.block = true` → pause (product-affecting intel flag).

Set via feeds/intel-flag.json (block=true) or feeds/legal.json (minor_safety_clear=false).
ecosystem-update.timer regenerates snapshot every 30m; for IMMEDIATE effect, run:
  bash /home/scott/hardonia.store/kb/tools/ecosystem-update.sh
then the next request sees it. (Sub-30s pause achievable by running the update script.)

## 2. Service-level (manual, immediate)
  systemctl --user stop au-bot-server.service   # bot intake offline; storefront shows fallback
Storefront fallback: if /au/ask is unreachable, show "support via GitHub issue" link
(Hardonian/hardonia-compute-api) — never a hung request.

## Resume
- Clear the flag (intel-flag.json block=false), run ecosystem-update.sh, OR
  systemctl --user start au-bot-server.service.
- Verify: curl -s 127.0.0.1:8071/au/health → legal_clear true, intel_block false.

## Rule
During any S1 (revenue/legal/abuse), pause the bot FIRST, investigate SECOND. A wrong bot answer
during an incident compounds the damage.
