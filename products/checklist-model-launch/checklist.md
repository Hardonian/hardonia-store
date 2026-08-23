# Model / Agent Launch Checklist

Run before any local model or agent touches production traffic.

## Pre-launch
- [ ] Weights verified present (sha256 of the .safetensors recorded)
- [ ] GPU visibility confirmed for the serving runtime
- [ ] Quantization level chosen and documented
- [ ] Context window and max tokens bounded
- [ ] System prompt reviewed for scope creep
- [ ] Tool access scoped to least-privilege (no rm -rf, no prod DB writes)
- [ ] Rate limit + concurrency cap set
- [ ] Secrets loaded from env, never in code or logs
- [ ] Input validation on every user-facing route
- [ ] Auth dependency on every non-public route

## Launch
- [ ] Staged rollout (1% -> 10% -> 100%)
- [ ] Health check returns 200 with real model load
- [ ] Fallback path when the model is cold/unavailable
- [ ] Cost guardrail (max $/day) wired and tested
- [ ] Observability: latency, error rate, token cost per call

## Post-launch
- [ ] 24h soak with no OOM or silent 500s
- [ ] Rollback command documented and tested
- [ ] Incident SOP linked from the runbook
- [ ] Changelog entry written
