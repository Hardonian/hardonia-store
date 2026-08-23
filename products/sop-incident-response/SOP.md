# AI Incident Response SOP

Use when an agent, GPU job, or model endpoint misbehaves in production.

## 0. Triage (0-5 min)
- Confirm the blast radius: which service, which users, which cost.
- Open an incident channel. Assign a single incident lead.

## 1. Freeze
- Stop the failing job/timer first: `systemctl --user stop <service>`.
- Do NOT restart until root cause is known.

## 2. Capture
- `journalctl --user -u <service> -n 200 --no-pager > /tmp/incident.log`
- Snapshot the current DB before any fix: `sqlite3 <db> '.backup' /tmp/<db>.bak`

## 3. Diagnose
- Reproduce on a throwaway copy, not production.
- Classify: code bug / config drift / resource exhaustion / bad input.

## 4. Fix
- Apply the smallest safe change. Back up before editing.
- If a secret leaked: rotate it NOW, then fix the exposure.

## 5. Verify
- Run the health check. Confirm the metric that broke is green.
- Re-enable the timer only after one clean cycle.

## 6. Communicate
- Postmortem within 24h: timeline, impact, root cause, 3 preventions.
- Update this SOP if a step was missing.

## Escalation
- Cost runaway: kill the GPU job, cap the cron, alert operator.
- Data exposure: rotate creds, audit access log, notify affected parties.
