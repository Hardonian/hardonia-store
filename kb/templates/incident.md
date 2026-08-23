# Template — Incident Postmortem

## Incident: {{TITLE}}
- Date: {{DATE}}
- Severity: {{SEV}}
- Detected by: {{DETECTED_BY}}  (AU bot / customer / monitor)
- Status: {{RESOLVED|OPEN}}

## Impact
- Customers affected: {{COUNT}}
- Products: {{PRODUCTS}}
- Revenue impact: {{AMOUNT|none}}

## Timeline
- {{T1}}: {{EVENT}}
- {{T2}}: {{EVENT}}

## Root cause
{{ROOT_CAUSE}}  <- smallest true cause

## Fix applied
{{FIX}}  <- commands/files changed

## Verification
{{VERIFY}}  <- what proved it's fixed

## Prevention
{{PREVENT}}  <- KB/runbook/bot change so it doesn't recur
- [ ] Updated {{KB_DOC}}
- [ ] Bot answer updated? {{YES_NO}}
