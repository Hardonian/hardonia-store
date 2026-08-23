"""Minimal checkout app services."""
import os
import sqlite3
from pathlib import Path

REVENUE_DB = Path("/home/scott/ai-lab/revenue-os/revenue-os.db")

def _db():
    con = sqlite3.connect(REVENUE_DB)
    con.row_factory = sqlite3.Row
    return con

def credit_user_balance(email: str, credits: int) -> dict:
    if not email:
        return {"status": "skipped", "reason": "missing email"}
    try:
        con = _db()
        con.execute(
            "INSERT INTO purchases (purchase_id, product_slug, amount_cents, status, metadata) VALUES (?, ?, ?, ?, ?)",
            (f"credit_{email}_{credits}", "credits", credits * 100, "credited", '{"email":"' + email + '"}'),
        )
        con.commit()
        con.close()
        return {"status": "credited", "credits": credits, "email": email}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
