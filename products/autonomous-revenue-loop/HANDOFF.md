INTERNAL OPERATOR DOCUMENT — NOT CUSTOMER-FACING.

# Autonomous Revenue Loop — Customer Handoff

## What you bought
- Product: Autonomous Revenue Loop
- Price: $499 one-time / $997 with implementation day / $750-$2500/mo retainer
- Files: 10

## Customization (template edit)
1. Your bundle is generated from the canonical deliverables.
2. To rebrand: edit `README.md` / `WALKTHROUGH.md` placeholders (your name, brand, colors).
3. Re-run the bundle builder to repackage: `python3 /home/scott/ai-lab/scripts/bin/customize_bundle.py --product autonomous-revenue-loop --brand 'YOUR BRAND'`
4. The output drops to `/home/scott/ai-lab/store/sent/<order_id>/`.

## Delivery
On purchase, the delivery pipeline assembles your bundle and drops it to the send folder; if email is configured it is sent automatically, otherwise a draft is staged for manual send.
