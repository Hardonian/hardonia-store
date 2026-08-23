INTERNAL OPERATOR DOCUMENT — NOT CUSTOMER-FACING.

# AI Portrait Studio — Customer Handoff

## What you bought
- Product: AI Portrait Studio
- Price: $19–$49
- Files: 4

## Customization (template edit)
1. Your bundle is generated from the canonical deliverables.
2. To rebrand: edit `README.md` / `WALKTHROUGH.md` placeholders (your name, brand, colors).
3. Re-run the bundle builder to repackage: `python3 /home/scott/ai-lab/scripts/bin/customize_bundle.py --product ai-portrait-studio --brand 'YOUR BRAND'`
4. The output drops to `/home/scott/ai-lab/store/sent/<order_id>/`.

## Delivery
On purchase, the delivery pipeline assembles your bundle and drops it to the send folder; if email is configured it is sent automatically, otherwise a draft is staged for manual send.
