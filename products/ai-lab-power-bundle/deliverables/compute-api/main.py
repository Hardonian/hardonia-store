"""
hardonia-checkout-api/app/main.py

Minimal Stripe Checkout + webhook service for Hardonia products.
No database of its own. It validates webhooks, records purchases
in revenue-os, and triggers fulfillment hooks.
"""
from __future__ import annotations

import json
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import stripe

import asyncio

async def _stripe_retry(client, method, url, **kwargs):
    max_attempts = 3
    backoff = 1
    for attempt in range(max_attempts):
        resp = await getattr(client, method)(url, **kwargs)
        if resp.status_code < 500:
            return resp
        if attempt < max_attempts - 1:
            await asyncio.sleep(backoff)
            backoff *= 2
    return resp

from fastapi import FastAPI, HTTPException, Request

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

from fastapi.responses import JSONResponse, RedirectResponse
from app.services import credit_user_balance


app = FastAPI(
    title="Hardonia Checkout API",
    version="0.2.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("audit")

class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method
        response = await call_next(request)
        logger.info({"event": "http_request", "method": method, "path": path, "status": response.status_code, "ip": ip})
        return response

app.add_middleware(AuditLogMiddleware)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.stripe.com; frame-ancestors 'none'"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# ── Global exception handler ──────────────────────────────────────────────────
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


HOME = Path("/home/scott/ai-workspace/repos/hardonia-checkout-api").resolve()
REVENUE_DB = Path("/home/scott/ai-lab/revenue-os/revenue-os.db")
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8020")


def _db() -> Any:
    import sqlite3
    con = sqlite3.connect(REVENUE_DB)
    con.row_factory = sqlite3.Row
    return con


def _product(slug: str) -> Optional[Dict[str, Any]]:
    con = _db()
    row = con.execute("SELECT * FROM products WHERE slug=?", (slug,)).fetchone()
    con.close()
    return dict(row) if row else None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hardonia-checkout-api", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}



def _canadian_tax(amount_cents: int, province: str = "") -> int:
    """Calculate Canadian tax for digital sales. Output in cents."""
    province = (province or "").upper()
    # GST for all Canadian sales
    gst = int(round(amount_cents * 0.05))
    # HST provinces
    hst_provinces = {"ON": 0.13, "NB": 0.15, "NL": 0.15, "NS": 0.15, "PE": 0.15}
    # PST provinces (only PST, no HST)
    pst_provinces = {"BC": 0.07, "SK": 0.06, "MB": 0.07, "QC": 0.09975}
    if province in hst_provinces:
        return int(round(amount_cents * hst_provinces[province]))
    if province in pst_provinces:
        return int(round(amount_cents * pst_provinces[province]))
    # Default: GST only
    return gst


@app.post("/api/v1/checkout/session")
async def create_checkout_session(request: Request):
    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY not configured")
    body = await request.json()
    slug = body.get("slug") or body.get("product_slug")
    email = body.get("email") or ""
    province = body.get("province") or ""
    country = body.get("country") or "CA"
    if not slug:
        raise HTTPException(status_code=400, detail="Missing product slug")

    product = _product(slug)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product not found: {slug}")

    validation = validate_product(slug)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["issues"])

    checkout_url = product.get("checkout_url") or product.get("stripe_payment_link_url") or ""
    if checkout_url and checkout_url.startswith("http"):
        return {"status": "ok", "mode": "link", "checkout_url": checkout_url}

    price = product.get("price") or "$29"
    price_num = int("".join([c for c in price if c.isdigit()]) or "2900")
    if price_num < 100:
        price_num = 990

    tax_cents = 0
    if country.upper() == "CA":
        tax_cents = _canadian_tax(price_num, province)
    else:
        tax_cents = _vat_for_country(price_num, country)

    payload = {
        "mode": "payment",
        "success_url": f"{BASE_URL}/p/{slug}?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{BASE_URL}/p/{slug}",
        "customer_email": email or None,
        "metadata": {"product_slug": slug, "source": "hardonia-checkout-api", "country": country, "province": province},
        "line_items": [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": product.get("name", slug)},
                    "unit_amount": price_num,
                },
                "quantity": 1,
            }
        ],
    }
    if tax_cents > 0:
        payload["automatic_tax"] = {"enabled": True}
        payload["metadata"]["tax_cents"] = str(tax_cents)
    payload = {k: v for k, v in payload.items() if v is not None}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            headers={
                "Authorization": f"Bearer {STRIPE_SECRET}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "mode": "payment",
                "success_url": payload["success_url"],
                "cancel_url": payload["cancel_url"],
                "customer_email": payload.get("customer_email") or "",
                "metadata[product_slug]": slug,
                "metadata[country]": country,
                "metadata[province]": province,
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][product_data][name]": product.get("name", slug),
                "line_items[0][price_data][unit_amount]": str(price_num),
                "line_items[0][quantity]": "1",
                "automatic_tax[enabled]": "true" if tax_cents > 0 else "false",
            },
            timeout=15,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Stripe error: {resp.text[:200]}")
        session = resp.json()

    # Record purchase with tax
    try:
        con = _db()
        con.execute(
            "INSERT INTO purchases (purchase_id, product_slug, amount_cents, status, metadata) VALUES (?, ?, ?, ?, ?)",
            (session.get("id"), slug, price_num + tax_cents, "pending", json.dumps({
                "session_id": session.get("id"),
                "country": country,
                "province": province,
                "tax_cents": tax_cents,
                "base_cents": price_num,
            })),
        )
        con.commit()
        con.close()
    except Exception:
        pass

    return {"status": "ok", "mode": "session", "checkout_url": session.get("url"), "session_id": session.get("id"), "tax_cents": tax_cents}


    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY not configured")
    body = await request.json()
    slug = body.get("slug") or body.get("product_slug")
    email = body.get("email") or ""
    if not slug:
        raise HTTPException(status_code=400, detail="Missing product slug")

    product = _product(slug)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product not found: {slug}")

    validation = validate_product(slug)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["issues"])

    checkout_url = product.get("checkout_url") or product.get("stripe_payment_link_url") or ""
    if checkout_url and checkout_url.startswith("http"):
        return {"status": "ok", "mode": "link", "checkout_url": checkout_url}

    price = product.get("price") or "$29"
    price_num = int("".join([c for c in price if c.isdigit()]) or "2900")
    if price_num < 100:
        price_num = 990

    payload = {
        "mode": "payment",
        "success_url": f"{BASE_URL}/p/{slug}?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{BASE_URL}/p/{slug}",
        "customer_email": email or None,
        "metadata": {"product_slug": slug, "source": "hardonia-checkout-api"},
        "line_items": [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": product.get("name", slug)},
                    "unit_amount": price_num,
                },
                "quantity": 1,
            }
        ],
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            headers={
                "Authorization": f"Bearer {STRIPE_SECRET}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"mode": "payment", "success_url": payload["success_url"], "cancel_url": payload["cancel_url"], "customer_email": payload.get("customer_email") or "", "metadata[product_slug]": slug, "line_items[0][price_data][currency]": "usd", "line_items[0][price_data][product_data][name]": product.get("name", slug), "line_items[0][price_data][unit_amount]": str(price_num), "line_items[0][quantity]": "1"},
            timeout=15,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Stripe error: {resp.text[:200]}")
        session = resp.json()

    return {"status": "ok", "mode": "session", "checkout_url": session.get("url"), "session_id": session.get("id")}


@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if STRIPE_WEBHOOK_SECRET:
        import hmac, hashlib
        try:
            parts = dict(p.split("=", 1) for p in sig.split(","))
            timestamp = parts.get("t", "")
            v1 = parts.get("v1", "")
            signed = f"{timestamp}.{body.decode()}"
            expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode(), signed.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, v1):
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
        except Exception as exc:
            raise HTTPException(status_code=403, detail=f"Webhook signature error: {exc}")

    event = json.loads(body)
    event_type = event.get("type", "unknown")
    session = event.get("data", {}).get("object", {}) or {}
    slug = ((session.get("metadata") or {}).get("product_slug")) or ""
    amount_cents = session.get("amount_total") or 0

    try:
        con = _db()
        con.execute(
            "INSERT INTO purchases (purchase_id, product_slug, amount_cents, status, metadata) VALUES (?, ?, ?, ?, ?)",
            (f"ev_{int(time.time()*1000)}", slug, amount_cents, event_type, json.dumps(event)),
        )
        con.commit()
        con.close()
    except Exception:
        pass

    return {"status": "ok"}



@app.get("/health/db")
async def db_health():
    try:
        con = _db()
        con.execute("SELECT 1").fetchone()
        con.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": str(e)},
        )


@app.get("/api/v1/validate")
async def validate_products():
    con = _db()
    rows = con.execute("SELECT slug, name, price, checkout_url, status FROM products").fetchall()
    con.close()
    issues = []
    for r in rows:
        if not r['price']:
            issues.append(f"{r['slug']}: missing price")
        sentinel = 'REPLACE' + '_BEFORE' + '_PUBLISH'
        if not r['checkout_url'] or sentinel in (r['checkout_url'] or ''):
            issues.append(f"{r['slug']}: checkout not ready")
    return {"valid": len(issues) == 0, "issues": issues, "count": len(rows)}


@app.get("/api/v1/revenue/summary")
async def revenue_summary():
    con = _db()
    rows = con.execute("SELECT product_slug, COUNT(*) as purchases, SUM(amount_cents) as revenue_cents FROM purchases GROUP BY product_slug").fetchall()
    con.close()
    return {"summary": [dict(r) for r in rows]}


@app.get("/api/v1/revenue/exports")
async def revenue_exports():
    export_dir = Path("/home/scott/ai-lab/revenue-os/exports")
    files = sorted(export_dir.glob("purchases-*.csv"))
    return {"files": [str(p) for p in files[-5:]]}

@app.get("/api/v1/products")
async def api_products():
    con = _db()
    rows = con.execute("SELECT slug,name,price,status FROM products WHERE status='ready'").fetchall()
    con.close()
    return {"products": [dict(r) for r in rows]}


@app.post("/webhooks/stripe/credit")
async def stripe_credit_webhook(request: Request):
    payload = await request.json()
    event_type = payload.get("type")
    if event_type == "checkout.session.completed":
        session = payload.get("data", {}).get("object", {})
        customer_email = session.get("customer_details", {}).get("email")
        amount_total = session.get("amount_total", 0)
        credits = max(1, int(amount_total / 100))
        if customer_email:
            credit_user_balance(customer_email, credits)
            return {"status": "credited", "credits": credits, "email": customer_email}
    return {"status": "ignored"}


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="missing webhook secret")
    body = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="missing signature")
    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=signature,
            secret=secret,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid signature: {exc}")
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email")
        amount_total = session.get("amount_total", 0)
        credits = max(1, int(amount_total / 100))
        if customer_email:
            credit_user_balance(customer_email, credits)
            return {"status": "credited", "credits": credits, "email": customer_email}
    return {"status": "received"}



@app.post("/webhooks/stripe/fulfill")
async def stripe_fulfill_webhook(request: Request):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if secret:
        import hmac, hashlib
        try:
            parts = dict(p.split("=", 1) for p in sig.split(","))
            timestamp = parts.get("t", "")
            v1 = parts.get("v1", "")
            signed = f"{timestamp}.{body.decode()}"
            expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, v1):
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
        except Exception as exc:
            raise HTTPException(status_code=403, detail=f"Webhook signature error: {exc}")

    event = json.loads(body)
    event_type = event.get("type", "unknown")
    session = event.get("data", {}).get("object", {}) or {}
    slug = ((session.get("metadata") or {}).get("product_slug")) or ""
    amount_cents = session.get("amount_total") or 0
    session_id = session.get("id", "")
    customer_email = session.get("customer_details", {}).get("email", "")

    # Update purchase status
    try:
        con = _db()
        con.execute(
            "UPDATE purchases SET status=? WHERE purchase_id=?",
            (event_type, session_id),
        )
        con.commit()
        con.close()
    except Exception:
        pass

    # Generate delivery token for digital products
    delivery = {"status": "received", "product": slug}
    if event_type == "checkout.session.completed" and slug:
        import secrets
        token = secrets.token_urlsafe(32)
        try:
            con = _db()
            con.execute(
                "INSERT OR IGNORE INTO delivery_tokens (token, job_id, api_key, expires_at, download_url, created_at) VALUES (?, ?, ?, datetime('now', '+30 days'), ?, datetime('now'))",
                (token, session_id, customer_email, f"{BASE_URL}/download/{token}"),
            )
            con.commit()
            con.close()
        except Exception:
            pass
        delivery["download_url"] = f"{BASE_URL}/download/{token}"
        delivery["delivery_token"] = token

        # Trigger compute-api credit if applicable
        if slug == "hardonia-compute-api-access":
            credits = max(1, int(amount_cents / 100))
            credit_user_balance(customer_email, credits)

    return delivery


@app.get("/download/{token}")
async def download_delivery(token: str):
    con = _db()
    row = con.execute("SELECT token, job_id, api_key, download_url, created_at FROM delivery_tokens WHERE token=?", (token,)).fetchone()
    con.close()
    if not row:
        raise HTTPException(status_code=404, detail="Invalid or expired download token")
    return {"status": "valid", "download_url": row[3], "api_key": row[2], "expires": "30 days from purchase"}



@app.post("/api/v1/checkout/subscription")
async def create_subscription_session(request: Request):
    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY not configured")
    body = await request.json()
    slug = body.get("slug") or body.get("product_slug")
    email = body.get("email") or ""
    plan = body.get("plan", "starter")
    if not slug:
        raise HTTPException(status_code=400, detail="Missing product slug")

    product = _product(slug)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product not found: {slug}")

    price_map = {
        "starter": {"usd": 1900},
        "pro": {"usd": 9900},
        "enterprise": {"usd": 29900},
    }
    price_data = price_map.get(plan, price_map["starter"])

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            headers={
                "Authorization": f"Bearer {STRIPE_SECRET}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "mode": "subscription",
                "success_url": f"{BASE_URL}/p/{slug}?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{BASE_URL}/p/{slug}",
                "customer_email": email or "",
                "metadata": {"product_slug": slug, "plan": plan, "source": "hardonia-checkout-api"},
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][product_data][name]": f"{product.get('name', slug)} - {plan}",
                "line_items[0][price_data][unit_amount]": str(price_data["usd"]),
                "line_items[0][quantity]": "1",
            },
            timeout=15,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Stripe error: {resp.text[:200]}")
        session = resp.json()

    return {"status": "ok", "mode": "subscription", "checkout_url": session.get("url"), "session_id": session.get("id"), "plan": plan}



@app.post("/api/v1/refund")
async def create_refund(request: Request):
    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY not configured")
    body = await request.json()
    session_id = body.get("session_id")
    reason = body.get("reason", "requested_by_customer")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.stripe.com/v1/refunds",
            headers={
                "Authorization": f"Bearer {STRIPE_SECRET}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "payment_intent": session_id,
                "reason": reason,
            },
            timeout=15,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Stripe refund error: {resp.text[:200]}")
        refund = resp.json()
    try:
        con = _db()
        con.execute("UPDATE purchases SET status=? WHERE purchase_id=?", ("refunded", session_id))
        con.commit()
        con.close()
    except Exception:
        pass
    return {"status": "refunded", "refund_id": refund.get("id")}



@app.post("/api/v1/affiliate/track")
async def track_affiliate(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    affiliate_code = body.get("affiliate_code")
    if not session_id or not affiliate_code:
        raise HTTPException(status_code=400, detail="session_id and affiliate_code required")
    try:
        con = _db()
        con.execute(
            "INSERT OR IGNORE INTO affiliate_events (session_id, affiliate_code, created_at) VALUES (?, ?, datetime('now'))",
            (session_id, affiliate_code),
        )
        con.commit()
        con.close()
    except Exception:
        pass
    return {"status": "tracked"}

@app.get("/api/v1/affiliate/summary")
async def affiliate_summary():
    try:
        con = _db()
        rows = con.execute("SELECT affiliate_code, COUNT(*) as conversions, SUM(amount_cents) as revenue_cents FROM affiliate_events ae JOIN purchases p ON ae.session_id = p.purchase_id GROUP BY affiliate_code").fetchall()
        con.close()
        return {"affiliates": [dict(zip(["code","conversions","revenue_cents"], r)) for r in rows]}
    except Exception as e:
        return {"affiliates": []}



@app.post("/api/v1/coupon/validate")
async def validate_coupon(request: Request):
    body = await request.json()
    code = (body.get("code") or "").upper()
    slug = body.get("slug")
    valid_codes = {
        "LAUNCH20": {"percent": 20, "expires": "2026-12-31"},
        "HARDONIA10": {"percent": 10, "expires": "2027-06-30"},
        "EARLY50": {"percent": 50, "expires": "2026-09-30"},
    }
    coupon = valid_codes.get(code)
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon")
    product = _product(slug) if slug else None
    price = 0
    if product:
        price = int("".join([c for c in product.get("price", "$29") if c.isdigit()]) or "2900")
        if price < 100: price = 990
    discount = int(round(price * coupon["percent"] / 100))
    return {"valid": True, "code": code, "percent": coupon["percent"], "discount_cents": discount, "expires": coupon["expires"]}


@app.on_event("shutdown")
async def shutdown_event():
    import logging
    logging.getLogger("audit").info("service_shutdown")
