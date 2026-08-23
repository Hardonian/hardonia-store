#!/usr/bin/env python3
"""Sovereign low-cost digital product factory.

One command to launch a new $9-$19 intangible digital product end-to-end:
  1. writes product.json + deliverable into hardonia.store/products/<slug>/
  2. registers Offer in the live audit-api catalog.py (price_id baked later)
  3. inserts into revenue-os.db products + commerce_catalog
  4. creates a live Stripe Payment Link + captures price_id
  5. wires the webhook (commerce_catalog.stripe_price_id = real price_1)
The audit-api checkout then creates a Checkout Session and the webhook fulfills.

Run from the audit-api venv (has stripe + dotenv) with the live key in env.
"""
from __future__ import annotations
import argparse, json, os, re, sqlite3, sys
from pathlib import Path

STORE = Path("/home/scott/hardonia.store/products")
REVENUE_DB = "/home/scott/ai-lab/revenue-os/revenue-os.db"
CATALOG = Path("/mnt/ai-storage/ai-workspace/repos/ai-lab-audit-api/app/catalog.py")
PRICE_USD = 19  # default; override per product

# Deliverable templates by kind
DELIVERABLES = {
    "prompt-pack": ("prompts.md", "# {name} — Prompt Pack\n\n{description}\n\n## Prompts\n{promo_body}\n"),
    "sop": ("SOP.md", "# {name} — Standard Operating Procedure\n\n{description}\n\n## Steps\n{promo_body}\n"),
    "checklist": ("checklist.md", "# {name} — Checklist\n\n{description}\n\n## Items\n{promo_body}\n"),
    "template": ("template.md", "# {name} — Template\n\n{description}\n\n## Fill-in\n{promo_body}\n"),
    "lora": ("lora.yaml", "name: \"{name}\"\ntype: comfyui-lora\nbase_model: \"SDXL 1.0\"\ndescription: >\n  {description}\n"),
    "skin": ("skin.yaml", "name: \"{name}\"\ntype: agent-skin\ndescription: >\n  {description}\n"),
    "bundle": ("bundle.md", "# {name}\n\n{description}\n\n## What's included\n{promo_body}\n\nThis bundle combines several sovereign assets at one price. After purchase you receive each component's download.\n"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--kind", required=True, choices=list(DELIVERABLES))
    ap.add_argument("--price", type=int, default=PRICE_USD)
    ap.add_argument("--audience", default="Sovereign AI operators")
    ap.add_argument("--pain", default="Unbranded, generic outputs")
    ap.add_argument("--offer", default="Drop-in ready-to-use asset")
    ap.add_argument("--description", default="")
    ap.add_argument("--promo", default="")  # markdown body for the deliverable
    ap.add_argument("--category", default="digital-asset")
    args = ap.parse_args()

    import stripe
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        print("STRIPE_SECRET_KEY missing", file=sys.stderr); return 2

    d = STORE / args.slug
    d.mkdir(parents=True, exist_ok=True)

    # 1. deliverable
    fname, tpl = DELIVERABLES[args.kind]
    deliverable = tpl.format(name=args.name, description=args.description or args.name,
                             promo_body=args.promo or "- (add your copy)")
    (d / fname).write_text(deliverable)

    # 2. product.json (store schema)
    product = {
        "slug": args.slug,
        "name": args.name,
        "tagline": args.description or args.name,
        "price": args.price,
        "currency": "usd",
        "audience": args.audience,
        "pain": args.pain,
        "offer": args.offer,
        "deliverable": fname,
        "stripe_sku": args.slug,
        "checkout_url": "",
        "gumroad_url": "",
        "status": "ready",
    }
    (d / "product.json").write_text(json.dumps(product, indent=2))

    # 3. live Stripe Payment Link + price_id
    stripe.api_key = key
    pl = stripe.PaymentLink.create(
        line_items=[{"price_data": {"currency": "usd",
                     "product_data": {"name": args.name},
                     "unit_amount": args.price * 100}, "quantity": 1}],
        metadata={"product_slug": args.slug})
    obj = stripe.PaymentLink.retrieve(pl.id, expand=["line_items"])
    price_id = obj.line_items.data[0].price.id
    link = pl.url

    # 4. catalog.py Offer — insert INSIDE the OFFERS dict (before its closing "}").
    cat = CATALOG.read_text()
    offer = (f'    "{args.slug}": Offer(\n'
             f'        sku="{args.slug}",\n'
             f'        name={args.name!r},\n'
             f'        price_usd={args.price},\n'
             f'        payment_link={link!r},\n'
             f'        price_id={price_id!r},\n'
             f'    ),\n')
    if f'"{args.slug}": Offer(' in cat:
        print("  catalog.py already has", args.slug, "(skipping insert)")
    else:
        # Insert INSIDE the OFFERS dict: find the dict's closing brace (the last
        # "}" before "def public_catalog") and insert the offer before it, with a
        # trailing comma, so the edited module still compiles.
        # Older factory code inserted AFTER the close -> IndentationError (broke
        # the live audit-api twice, 2026-08). We also compile-verify before
        # writing, restoring the file if the edit is malformed.
        import py_compile
        import tempfile
        idx_def = cat.rfind("def public_catalog")
        if idx_def == -1:
            raise SystemExit(f"[catalog insert] cannot locate def public_catalog in {CATALOG}")
        # Robust: the OFFERS dict's closing brace is the LAST '}' before
        # "def public_catalog" (file may carry blank lines after the brace;
        # a literal "}\n\ndef public_catalog" match is fragile and has broken
        # the live API twice). Strip trailing whitespace so blank lines cannot
        # hide the brace.
        idx = cat[:idx_def].rstrip().rfind("}")
        if idx == -1:
            raise SystemExit(f"[catalog insert] cannot locate OFFERS dict close in {CATALOG}")
        # Offer text (4-space indent, trailing comma) goes right before the brace.
        cat_new = cat[:idx] + "\n" + offer.rstrip("\n") + cat[idx:]
        # Verify it compiles before touching the live file.
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(cat_new)
            tmp = tf.name
        try:
            py_compile.compile(tmp, doraise=True)
        except py_compile.PyCompileError as e:
            raise SystemExit(f"[catalog] edited catalog.py FAILED compile: {e}")
        finally:
            os.unlink(tmp)
        CATALOG.write_text(cat_new)

    # 5. DB rows
    conn = sqlite3.connect(REVENUE_DB); conn.row_factory = sqlite3.Row
    try:
        conn.execute("""INSERT INTO products(slug,name,status,audience,pain,offer,price,checkout_url,
            deliverable_path,source,readiness_score,gumroad_url,category,stripe_sku)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (args.slug, args.name, "ready", args.audience, args.pain, args.offer,
             f"${args.price}", link, str(d / fname), str(d / "product.json"), 95,
             link, args.category, args.slug))
    except sqlite3.IntegrityError:
        conn.execute("UPDATE products SET name=?,checkout_url=?,stripe_sku=?,status='ready' WHERE slug=?",
                     (args.name, link, args.slug, args.slug))
    try:
        conn.execute("""INSERT INTO commerce_catalog(product_slug,package,stripe_price_id,currency,
            amount_cents,price_cents,mode,compute_credits,provider_link_id,active,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (args.slug, "standard", price_id, "usd", args.price*100, args.price*100,
             "payment", None, link, 1, "now"))
    except sqlite3.IntegrityError:
        conn.execute("UPDATE commerce_catalog SET stripe_price_id=?,active=1 WHERE product_slug=?",
                     (price_id, args.slug))
    conn.commit()
    conn.close()

    print(f"LAUNCHED {args.slug}")
    print(f"  link: {link}")
    print(f"  price_id: {price_id}")
    print(f"  deliverable: {d / fname}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
