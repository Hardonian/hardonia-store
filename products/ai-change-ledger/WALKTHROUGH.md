# AI Change Ledger Walkthrough

1. Run the engine on the target machine.
2. Keep `reports/change-ledger/ledger.jsonl` append-only.
3. Publish or export only `latest.md`/`latest.html` when the customer approves sharing.
4. Verify the chain before every handoff:

```bash
python3 /home/scott/ai-lab/scripts/bin/ai-change-ledger.py --verify
```

A modified historical receipt causes verification to fail with a line-specific chain error.
