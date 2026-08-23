# AI Change Ledger

AI Change Ledger is a private, recurring evidence layer for teams running local or self-hosted AI.

It creates hash-chained receipts of aggregate operational state so an operator can answer:

- What changed since the last receipt?
- Did a service, timer, inference lane, GPU, or revenue-control state change?
- Can we prove the record was not silently rewritten?

## What ships

- Python stdlib-only engine
- Append-only JSONL ledger
- Hash-chain verification command
- Markdown and HTML receipt output
- No prompts, customer records, credentials, or payment payloads

## Local proof

The included lab proof is at:

- `/home/scott/ai-lab/reports/change-ledger/latest.md`
- `/home/scott/ai-lab/reports/change-ledger/latest.html`

Run:

```bash
python3 /home/scott/ai-lab/scripts/bin/ai-change-ledger.py
python3 /home/scott/ai-lab/scripts/bin/ai-change-ledger.py --verify
```

## Operations layer

The local operator can also run:

```bash
python3 /home/scott/ai-lab/scripts/bin/ai-change-ledger-ops.py status
python3 /home/scott/ai-lab/scripts/bin/ai-change-ledger-ops.py strategy
python3 /home/scott/ai-lab/scripts/bin/ai-change-ledger-ops.py housekeeping
```

The existing Hermes scheduler runs one local daily wrapper. It writes a log, creates a receipt, verifies the chain, emits the next strategic action, and performs dry-run housekeeping. It does not post, email, invoice, charge, or publish.


Target price: $29/month for a private recurring receipt lane; $199 one-time installation for managed setup.

Current channel status:

- Stripe recurring Payment Link is live and verified: `https://buy.stripe.com/7sY14m1Ve7lWeNkdCVb3q20`
- Gumroad is not claimed as active; its legacy publisher hit 404s on old update targets and was stopped.
- This product is not a compliance certification or security guarantee.
