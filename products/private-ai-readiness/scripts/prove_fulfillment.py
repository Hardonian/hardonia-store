#!/usr/bin/env python3
"""Self-cleaning technical proof for Private AI Readiness fulfillment.

Posts a locally signed synthetic Stripe event to the existing local checkout
listener. It never calls Stripe, never charges a card, and removes every
synthetic database row that it creates, whether the assertion passes or fails.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SLUG = "private-ai-readiness"
PACKAGE = "standard"
DB = Path("/home/scott/ai-lab/revenue-os/revenue-os.db")
ENV = Path("/home/scott/.local/etc/hardonia-checkout-api.env")
WEBHOOK_URL = "http://127.0.0.1:8012/webhooks/stripe"


def webhook_secret() -> str:
    for line in ENV.read_text(errors="replace").splitlines():
        if line.startswith("STRIPE_WEBHOOK_SECRET="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Stripe webhook secret is unavailable")


def signed_header(payload: bytes, secret: str) -> str:
    stamp = str(int(time.time()))
    digest = hmac.new(secret.encode(), stamp.encode() + b"." + payload, hashlib.sha256).hexdigest()
    return f"t={stamp},v1={digest}"


def post(payload: bytes, signature: str) -> tuple[int, dict]:
    req = urllib.request.Request(WEBHOOK_URL, data=payload, method="POST", headers={
        "Content-Type": "application/json", "Stripe-Signature": signature,
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


def cleanup(event_id: str, session_id: str) -> None:
    conn = sqlite3.connect(DB)
    try:
        for table, column, value in (
            ("commerce_events", "event_id", event_id),
            ("commerce_processed_events", "event_id", event_id),
            ("commerce_transition_audit", "provider_event_id", event_id),
            ("commerce_provider_objects", "object_id", session_id),
            ("purchases", "purchase_id", session_id),
        ):
            try:
                conn.execute(f"DELETE FROM {table} WHERE {column}=?", (value,))
            except sqlite3.Error:
                pass
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute("SELECT stripe_price_id, amount_cents, currency FROM commerce_catalog WHERE product_slug=? AND package=? AND active=1", (SLUG, PACKAGE)).fetchone()
    finally:
        conn.close()
    if not row:
        raise RuntimeError("active commerce catalog mapping is missing")
    price_id, amount, currency = row
    unique = f"{int(time.time())}_{os.getpid()}_{os.urandom(4).hex()}"
    event_id, session_id = f"evt_proof_{unique}", f"cs_proof_{unique}"
    event = {
        "id": event_id, "object": "event", "livemode": True,
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": session_id, "object": "checkout.session", "payment_status": "paid", "status": "complete",
            "metadata": {"product_slug": SLUG, "package": PACKAGE},
            "client_reference_id": "src:technical-proof", "customer_email": "proof-buyer@example.invalid",
            "amount_total": amount, "currency": currency, "payment_intent": f"pi_proof_{unique}",
            "line_items": {"object": "list", "data": [{"quantity": 1, "amount_total": amount, "price": {"id": price_id, "currency": currency, "unit_amount": amount}}]},
        }},
    }
    try:
        raw = json.dumps(event, separators=(",", ":")).encode()
        code, result = post(raw, signed_header(raw, webhook_secret()))
        if code != 200 or result.get("status") != "fulfilled":
            raise RuntimeError(f"webhook did not fulfill synthetic event (http={code}, status={result.get('status')!r})")
        conn = sqlite3.connect(DB)
        try:
            purchase = conn.execute("SELECT fulfillment_status, fulfillment_url FROM purchases WHERE purchase_id=?", (session_id,)).fetchone()
        finally:
            conn.close()
        if not purchase or purchase[0] not in {"fulfilled", "delivered"} or not purchase[1] or "/download/" not in purchase[1]:
            raise RuntimeError("fulfilled event did not produce a signed download URL")
        # Prove the fulfillment application directly. Public-edge reachability
        # is separately monitored because Cloudflare loopback probes are not a
        # substitute for an external buyer test.
        signed = urllib.parse.urlsplit(purchase[1])
        local_url = urllib.parse.urlunsplit(("http", "127.0.0.1:8012", signed.path, signed.query, ""))
        request = urllib.request.Request(local_url, method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
            if response.status != 200 or len(payload) == 0 or response.headers.get_content_type() != "application/zip":
                raise RuntimeError("signed download was not readable from the fulfillment application")
        print(f"PASS: signed webhook -> fulfilled -> signed download ({len(payload)} bytes) -> self-cleanup")
        return 0
    finally:
        cleanup(event_id, session_id)


if __name__ == "__main__":
    raise SystemExit(main())
