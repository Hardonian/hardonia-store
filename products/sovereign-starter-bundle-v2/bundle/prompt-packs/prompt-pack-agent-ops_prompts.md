# Agent Ops Prompt Pack — 30 drop-in prompts

Copy-paste into Hermes / Claude Code / Codex / GPT. Replace <...> with your context.

## 1. Health check
"Audit the <service> on <host>. List every systemd timer, its last run, and any that failed in the last 24h. Report as a table."

## 2. Root-cause a crash
"A process crashed with <error>. Find the unit file, the last 50 journal lines, and the most likely root cause. Propose a fix and the exact command to apply it."

## 3. Safe restart
"Restart <service> without dropping in-flight work. Show the command, the verification step, and the rollback command if it fails."

## 4. Dependency drift
"Compare requirements.txt in <repo> against what is actually imported. Flag unused deps and missing pins."

## 5. Port conflict
"Something is already bound to :<port>. Find the PID, the unit that owns it, and whether killing it is safe."

## 6. Disk pressure
"Find the 10 largest directories under /home/scott excluding node_modules caches. Suggest what is safe to prune."

## 7. Secret scan
"Grep the <repo> working tree for leaked API keys, tokens, and private keys. Report file:line without printing secrets. Suggest a .gitignore fix."

## 8. Cron audit
"List every cron job and systemd timer owned by this user. Flag any that write to /mnt or symlink the runtime off root."

## 9. Webhook verify
"Write a FastAPI route that verifies a Stripe webhook signature using the raw body and a secret from env. Reject on bad sig with 400."

## 10. Idempotent script
"Rewrite <script> so it is safe to re-run: back up before change, skip if already applied, log every step."

## 11. Log triage
"Tail <service> logs for the last hour. Group errors by type. Surface the top 3 recurring failures."

## 12. GPU check
"Report GPU visibility for Ollama and ComfyUI. If a GPU shows but Ollama says 0, give the fix."

## 13. Rollback plan
"<deploy> failed at <step>. Write a sequenced rollback using the last known-good state. Do not destroy history."

## 14. Backup verify
"Verify the nightly backup of <db> actually restores. Give a throwaway restore command against a temp file."

## 15. Rate limit
"Add a simple in-memory rate limiter to <endpoint>. Return 429 with Retry-After when exceeded."

## 16. Migration safety
"Generate a SQLite migration that adds <column> without locking the table. Include the down-migration."

## 17. Test green
"Make <repo> test suite pass locally. Run lint, typecheck, and tests. Report what you changed."

## 18. Env diff
"Diff the running service env against its .env file. Flag any mismatch that would cause a silent failure."

## 19. Access review
"List every route in <fastapi_app> that has no auth dependency. Flag the dangerous ones."

## 20. Cache purge
"Purge the npm/node-gyp/build caches safely on this machine without touching the runtime."

## 21. Watchdog
"Write a systemd path unit that restarts <service> if its socket disappears."

## 22. Postmortem
"Write a blameless postmortem for <incident>: timeline, impact, root cause, 3 preventative actions."

## 23. Cost cut
"Find the most expensive idle resource in this lab and the exact command to stop it."

## 24. Repo split
"Decide if <monorepo> should be split. Give the criteria and a safe split plan."

## 25. Signature test
"Generate a signed download URL for <slug> with HMAC-SHA256 and a 7-day expiry. Show verification."

## 26. Tenant check
"Verify RLS is enabled on every table in <supabase_schema>. List any table missing it."

## 27. Dry run
"Add a --dry-run flag to <script> that prints every command it WOULD run."

## 28. Alert rule
"Write a check that fires if <metric> is zero for 7 days. Output healthy/error only."

## 29. Doc sync
"Update <README> to match the current CLI flags. Remove any that no longer exist."

## 30. Debrief
"Summarize what you did this session as a handoff note a future agent can act on."
