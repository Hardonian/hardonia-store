#!/usr/bin/env python3
"""
generate-stripe-links.py — create Stripe Payment Links for the Agent Skin Packs.

Requires a VALID STRIPE_SECRET_KEY in the audit-api .env. Test mode
(sk_test_...) is fine for a dry run; swap to sk_live_... for production.

Run from the audit-api dir so dotenv finds .env:
  cd /mnt/ai-storage/ai-workspace/repos/ai-lab-audit-api
  .venv/bin/python /home/scott/hardonia.store/generate-stripe-links.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys

import dotenv

dotenv.load_dotenv()

SKINS = [
    ("skin-neon-sovereign", "Neon Sovereign — Agent Skin Pack", 1900),
    ("skin-heritage-quiet", "Heritage Quiet — Agent Skin Pack", 1900),
]


def main() -> int:
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key or key.startswith("TODO") or len(key) < 20:
        print("ERROR: STRIPE_SECRET_KEY is missing or invalid in .env.")
        print("Set a real key (sk_test_... or sk_live_...) and re-run.")
        return 2
    # Use the audit-api venv's stripe lib.
    code = (
        "import stripe, json, os;"
        "stripe.api_key=os.getenv('STRIPE_SECRET_KEY');"
        "out={};"
        "skins=" + repr(SKINS) + ";"
        "for sku,name,price in skins:"
        "    pl=stripe.PaymentLink.create(line_items=[{'price_data':{'currency':'usd','product_data':{'name':name},'unit_amount':price},'quantity':1}], metadata={'sku':sku});"
        "    out[sku]=pl.url;"
        "print('LINKS:'+json.dumps(out))"
    )
    r = subprocess.run(
        [".venv/bin/python", "-c", code],
        capture_output=True, text=True, timeout=90,
    )
    if r.returncode != 0:
        print("Stripe call failed:")
        print(r.stderr[-1500:])
        return 1
    for line in r.stdout.splitlines():
        if line.startswith("LINKS:"):
            links = json.loads(line[len("LINKS:"):])
            print("\nPaste these into app/catalog.py:\n")
            for sku, url in links.items():
                print(f'  "{sku}": "{url}",')
            return 0
    print("No LINKS output. stderr:", r.stderr[-800:])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
