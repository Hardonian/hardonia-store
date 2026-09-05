# Delivery Walkthrough

## Before the session

1. Complete `intake_form.md` without including API keys, passwords, private customer data, or confidential prompts.
2. Copy this package to the machine being reviewed.
3. Run:

```bash
python3 scripts/collect_readiness_evidence.py --out private-ai-readiness-evidence.json
```

4. Review the JSON file locally. Remove any fields the client does not authorize for sharing.
5. Share the sanitized evidence and intake through the agreed private channel.

## During the session

The review checks workload ownership, GPU/VRAM contention, container runtime readiness, local-serving boundaries, data handling, model licensing questions, and the client’s intended commercial use. It does not include penetration testing, legal advice, formal certification, or production changes unless separately scoped.

## After the session

The operator completes `report_template.md` using the actual evidence. Each finding should cite evidence, state uncertainty, name an owner, and have an acceptance test. Recommendations are ranked as immediate, short-term, or ongoing.

## Buyer acceptance checklist

- The report identifies the reviewed host(s) and evidence collection time.
- Every material finding has evidence and a remediation owner.
- Every recommended change has a rollback or safety note.
- Any legal, licensing, or regulatory conclusion is labeled for specialist verification.
