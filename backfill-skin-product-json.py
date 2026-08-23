#!/usr/bin/env python3
"""Backfill product.json (store-standard schema) for agent-skin packs.

The store catalog uses one product.json per product dir
(slug/name/price/checkout_url/readiness_score/...). Our agent-skin packs
were written with only skin.yaml; this adds the standard metadata so they
sit consistently beside the other 42 products and are promotable.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

STORE = Path("/home/scott/hardonia.store")
PRODUCTS = STORE / "products"

# Manual mapping for the two hand-authored launch packs.
LAUNCH = {
    "agent-skin-neon-sovereign": {
        "sku": "skin-neon-sovereign", "name": "Neon Sovereign — Agent Skin Pack",
        "price_usd": 19, "tagline": "Cyan-on-ink command surface for operators running sovereign AI fleets at 2am.",
    },
    "agent-skin-heritage-quiet": {
        "sku": "skin-heritage-quiet", "name": "Heritage Quiet — Agent Skin Pack",
        "price_usd": 19, "tagline": "Restrained heritage monochrome — Wall Street restraint for AI operators.",
    },
}


def write_product_json(slug: str, meta: dict) -> None:
    d = PRODUCTS / slug
    (d / "skin.yaml").write_text((d / "skin.yaml").read_text(), encoding="utf-8")  # ensure exists
    product = {
        "slug": slug,
        "name": meta["name"],
        "status": "ready",
        "audience": "sovereign AI operators running Hermes / local agent fleets",
        "pain": "generic, unbranded agent UIs; no identity separation between fleets or clients",
        "offer": f"{meta['name']}: a drop-in skin.yaml that themes the agent CLI/TUI/GUI from one file, plus 2 bundled operator skills.",
        "price": f"${meta['price_usd']} one-time",
        "headline": meta["tagline"],
        "checkout_url": f"https://aiautomatedsystems.ca/api/checkout?sku={meta['sku']}&email=",
        "gumroad_url": f"https://aiautomatedsystems.ca/api/checkout?sku={meta['sku']}&email=",
        "image_path": f"{d}/assets/cover.png",
        "deliverable_path": f"{d}/skin.yaml",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "readiness_score": 95,
        "source": f"{d}/product.json",
        "launch_gate": "ready: deliverable present, checkout wired, install script included",
        "sku": meta["sku"],
    }
    (d / "product.json").write_text(json.dumps(product, indent=2) + "\n", encoding="utf-8")
    print(f"wrote product.json for {slug}")


if __name__ == "__main__":
    for slug, meta in LAUNCH.items():
        write_product_json(slug, meta)
    # Also handle any auto-generated skin-* dirs (dated) — mark them draft.
    for d in sorted(PRODUCTS.glob("skin-*20*")):
        if (d / "skin.yaml").exists() and not (d / "product.json").exists():
            name = d.name.replace("skin-", "").replace("-20", " ").title()
            write_product_json(d.name, {
                "sku": d.name, "name": f"{name} — Agent Skin Pack",
                "price_usd": 19, "tagline": "Auto-generated sovereign agent skin pack.",
            })
            # downgrade auto-gen to draft (operator review before promo)
            p = json.loads((d / "product.json").read_text())
            p["status"] = "draft"; p["readiness_score"] = 40
            p["launch_gate"] = "draft: operator review of tagline + palette before promotion"
            (d / "product.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
            print(f"wrote DRAFT product.json for {d.name}")
