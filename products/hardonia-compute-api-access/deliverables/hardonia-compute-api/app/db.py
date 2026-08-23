"""Database layer for Hardonia Compute API with job queue + credits."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(settings.db_path)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    c = _conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            email TEXT,
            plan TEXT DEFAULT 'free',
            quota_tokens INTEGER DEFAULT 100000,
            created_at TEXT,
            rate_per_min INTEGER DEFAULT 30,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            path TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            cost_usd REAL,
            latency_ms INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            api_key TEXT NOT NULL,
            job_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            model TEXT,
            prompt TEXT DEFAULT '',
            workflow TEXT DEFAULT '{}',
            params TEXT DEFAULT '{}',
            callback_url TEXT,
            result TEXT DEFAULT '{}',
            error TEXT,
            cost_credits INTEGER DEFAULT 0,
            credits_before INTEGER DEFAULT 0,
            credits_after INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            external_prompt_id TEXT,
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3
        );

        CREATE TABLE IF NOT EXISTS job_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            event TEXT NOT NULL,
            detail TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS credit_purchases (
            purchase_id TEXT PRIMARY KEY,
            api_key TEXT NOT NULL,
            stripe_session_id TEXT UNIQUE,
            amount_cents INTEGER NOT NULL,
            credits INTEGER NOT NULL,
            package TEXT,
            status TEXT DEFAULT 'pending',
            metadata TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS credit_transactions (
            transaction_id TEXT PRIMARY KEY,
            api_key TEXT NOT NULL,
            type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            ref_type TEXT,
            ref_id TEXT,
            reason TEXT,
            metadata TEXT DEFAULT '{}',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS delivery_tokens (
            token TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            api_key TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            download_url TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS webhooks (
            webhook_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            api_key TEXT NOT NULL,
            amount_cents INTEGER,
            currency TEXT DEFAULT 'cad',
            payload TEXT DEFAULT '{}',
            processed INTEGER DEFAULT 0,
            error TEXT,
            created_at TEXT,
            processed_at TEXT
        );
        """
    )
    # Idempotent migrations for existing tables.
    _migrate(c)
    c.commit()
    c.close()


def _migrate(c: sqlite3.Connection) -> None:
    """Add missing columns to legacy tables."""
    for table, column, ddl in (
        ("api_keys", "rate_per_min", "INTEGER DEFAULT 30"),
        ("api_keys", "active", "INTEGER DEFAULT 1"),
        ("jobs", "external_prompt_id", "TEXT"),
        ("jobs", "attempts", "INTEGER DEFAULT 0"),
        ("jobs", "max_attempts", "INTEGER DEFAULT 3"),
    ):
        cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


# ── API keys ──────────────────────────────────────────────────────────────────


def key_exists(key: str) -> bool:
    c = _conn()
    try:
        r = c.execute("SELECT 1 FROM api_keys WHERE key=?", (key,)).fetchone()
        return r is not None
    finally:
        c.close()


def create_key(
    key: str,
    email: str = "",
    plan: str = "free",
    quota: int = 100000,
    rate_per_min: int = 30,
    initial_credits: int = 0,
) -> Dict[str, Any]:
    c = _conn()
    try:
        c.execute(
            "INSERT OR IGNORE INTO api_keys(key,email,plan,quota_tokens,created_at,rate_per_min,active) VALUES(?,?,?,?,?,?,?)",
            (
                key,
                email,
                plan,
                quota,
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                rate_per_min,
                1,
            ),
        )
        if initial_credits > 0:
            _credit_transaction(
                c,
                api_key=key,
                type="purchase",
                amount=initial_credits,
                balance_after=initial_credits,
                ref_type="initial",
                reason="Initial credits",
            )
            c.execute(
                "UPDATE api_keys SET quota_tokens = ? WHERE key=?",
                (initial_credits, key),
            )
        c.commit()
        return {
            "key": key,
            "email": email,
            "plan": plan,
            "quota_tokens": quota if initial_credits <= 0 else initial_credits,
            "rate_per_min": rate_per_min,
        }
    finally:
        c.close()


def get_key(key: str) -> Optional[Dict[str, Any]]:
    c = _conn()
    try:
        r = c.execute(
            "SELECT key,email,plan,quota_tokens,created_at,rate_per_min,active FROM api_keys WHERE key=?",
            (key,),
        ).fetchone()
        return dict(r) if r else None
    finally:
        c.close()


def set_key_active(key: str, active: bool) -> None:
    c = _conn()
    try:
        c.execute("UPDATE api_keys SET active=? WHERE key=?", (1 if active else 0, key))
        c.commit()
    finally:
        c.close()


# ── Usage ─────────────────────────────────────────────────────────────────────


def log_usage(
    key: str,
    path: str,
    model: str,
    pt: int,
    ct: int,
    tt: int,
    cost: float,
    lat: int,
) -> None:
    c = _conn()
    try:
        c.execute(
            "INSERT INTO usage_logs(api_key,path,model,prompt_tokens,completion_tokens,total_tokens,cost_usd,latency_ms,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                key,
                path,
                model,
                pt,
                ct,
                tt,
                cost,
                lat,
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
        )
        c.commit()
    finally:
        c.close()


def used_tokens(key: str) -> int:
    c = _conn()
    try:
        r = c.execute(
            "SELECT COALESCE(SUM(total_tokens),0) FROM usage_logs WHERE api_key=?",
            (key,),
        ).fetchone()
        return r[0] if r else 0
    finally:
        c.close()


def usage_for(key: str, limit: int = 50) -> List[Dict[str, Any]]:
    c = _conn()
    try:
        rows = c.execute(
            "SELECT path,model,total_tokens,cost_usd,created_at FROM usage_logs WHERE api_key=? ORDER BY id DESC LIMIT ?",
            (key, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def key_summary(key: str) -> Dict[str, Any]:
    c = _conn()
    try:
        r = c.execute(
            "SELECT plan,quota_tokens FROM api_keys WHERE key=?",
            (key,),
        ).fetchone()
        if not r:
            return {"plan": None, "quota_tokens": 0, "used_tokens": 0, "remaining": 0, "credits": 0}
        used = used_tokens(key)
        credits = credit_balance(c, key)
        return {
            "plan": r["plan"],
            "quota_tokens": r["quota_tokens"],
            "used_tokens": used,
            "remaining": max(0, r["quota_tokens"] - used),
            "credits": credits,
        }
    finally:
        c.close()


# ── Jobs ──────────────────────────────────────────────────────────────────────


def create_job(
    job_id: str,
    api_key: str,
    job_type: str,
    prompt: str = "",
    workflow: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    callback_url: Optional[str] = None,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    c = _conn()
    try:
        credits_before = credit_balance(c, api_key)
        c.execute(
            "INSERT INTO jobs(job_id,api_key,job_type,status,model,prompt,workflow,params,callback_url,created_at,updated_at,credits_before,max_attempts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                api_key,
                job_type,
                "pending",
                model,
                prompt,
                json.dumps(workflow or {}),
                json.dumps(params or {}),
                callback_url,
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                credits_before,
                max_attempts,
            ),
        )
        c.execute(
            "INSERT INTO job_events(job_id,event,detail,created_at) VALUES(?,?,?,?)",
            (job_id, "created", json.dumps({"job_type": job_type}), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
        )
        c.commit()
        return get_job(c, job_id)
    finally:
        c.close()


def get_job(c: sqlite3.Connection, job_id: str) -> Optional[Dict[str, Any]]:
    r = c.execute(
        "SELECT * FROM jobs WHERE job_id=?",
        (job_id,),
    ).fetchone()
    if not r:
        return None
    row = dict(r)
    row["workflow"] = json.loads(row.get("workflow") or "{}")
    row["params"] = json.loads(row.get("params") or "{}")
    row["result"] = json.loads(row.get("result") or "{}")
    return row


def update_job_status(
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    cost_credits: int = 0,
    external_prompt_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    c = _conn()
    try:
        row = get_job(c, job_id)
        if not row:
            return None
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        updates = ["status=?", "updated_at=?", "attempts=attempts+1"]
        params: List[Any] = [status, now]
        if status == "running":
            updates.append("started_at=?")
            params.append(now)
        if status in ("completed", "failed", "cancelled", "timeout"):
            updates.append("completed_at=?")
            params.append(now)
        if result is not None:
            updates.append("result=?")
            params.append(json.dumps(result))
        if error is not None:
            updates.append("error=?")
            params.append(error)
        if cost_credits:
            updates.append("cost_credits=?")
            params.append(cost_credits)
        if external_prompt_id:
            updates.append("external_prompt_id=?")
            params.append(external_prompt_id)
        params.append(job_id)
        c.execute(f"UPDATE jobs SET {', '.join(updates)} WHERE job_id=?", params)
        c.execute(
            "INSERT INTO job_events(job_id,event,detail,created_at) VALUES(?,?,?,?)",
            (job_id, status, json.dumps({"error": error} if error else {}), now),
        )
        c.commit()
        return get_job(c, job_id)
    finally:
        c.close()


def list_jobs(api_key: str, status: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    c = _conn()
    try:
        where = ["api_key=?"]
        params: List[Any] = [api_key]
        if status:
            where.append("status=?")
            params.append(status)
        params.extend([page_size, (page - 1) * page_size])
        rows = c.execute(
            f"SELECT * FROM jobs WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        jobs = []
        for r in rows:
            row = dict(r)
            row["workflow"] = json.loads(row.get("workflow") or "{}")
            row["params"] = json.loads(row.get("params") or "{}")
            row["result"] = json.loads(row.get("result") or "{}")
            jobs.append(row)
        count = c.execute(
            f"SELECT COUNT(*) FROM jobs WHERE {' AND '.join(where)}",
            params[:-2],
        ).fetchone()[0]
        return {"jobs": jobs, "count": count, "page": page, "page_size": page_size}
    finally:
        c.close()


# ── Credits ───────────────────────────────────────────────────────────────────


def credit_balance(c: sqlite3.Connection, api_key: str) -> int:
    r = c.execute(
        "SELECT COALESCE(SUM(amount),0) FROM credit_transactions WHERE api_key=?",
        (api_key,),
    ).fetchone()
    return r[0] if r else 0


def _credit_transaction(
    c: sqlite3.Connection,
    api_key: str,
    type: str,
    amount: int,
    balance_after: int,
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    transaction_id = f"ct_{int(time.time()*1000)}_{api_key[-8:]}"
    c.execute(
        "INSERT INTO credit_transactions(transaction_id,api_key,type,amount,balance_after,ref_type,ref_id,reason,metadata,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            transaction_id,
            api_key,
            type,
            amount,
            balance_after,
            ref_type,
            ref_id,
            reason,
            json.dumps(metadata or {}),
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        ),
    )


def add_credits(
    api_key: str,
    amount: int,
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    if amount <= 0:
        raise ValueError("amount must be positive")
    c = _conn()
    try:
        balance = credit_balance(c, api_key)
        new_balance = balance + amount
        _credit_transaction(c, api_key, "purchase", amount, new_balance, ref_type, ref_id, reason)
        c.execute("UPDATE api_keys SET quota_tokens=? WHERE key=?", (new_balance, api_key))
        c.commit()
        return {"api_key": api_key, "amount": amount, "balance_after": new_balance}
    finally:
        c.close()


def consume_credits(
    api_key: str,
    amount: int,
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    if amount <= 0:
        raise ValueError("amount must be positive")
    c = _conn()
    try:
        balance = credit_balance(c, api_key)
        if balance < amount:
            raise ValueError(f"Insufficient credits: {balance} < {amount}")
        new_balance = balance - amount
        _credit_transaction(c, api_key, "consumption", -amount, new_balance, ref_type, ref_id, reason)
        c.execute("UPDATE api_keys SET quota_tokens=? WHERE key=?", (new_balance, api_key))
        c.commit()
        return {"api_key": api_key, "amount": -amount, "balance_after": new_balance}
    finally:
        c.close()


def credit_balance_simple(api_key: str) -> int:
    c = _conn()
    try:
        return credit_balance(c, api_key)
    finally:
        c.close()


def list_transactions(api_key: str, limit: int = 50) -> List[Dict[str, Any]]:
    c = _conn()
    try:
        rows = c.execute(
            "SELECT transaction_id,type,amount,balance_after,ref_type,ref_id,reason,created_at FROM credit_transactions WHERE api_key=? ORDER BY created_at DESC LIMIT ?",
            (api_key, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


# ── Delivery tokens ───────────────────────────────────────────────────────────


def create_delivery_token(job_id: str, api_key: str, ttl_hours: int = 24) -> Dict[str, Any]:
    c = _conn()
    try:
        import secrets
        token = f"dl_{secrets.token_urlsafe(32)}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        expires = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + ttl_hours * 3600))
        download_url = f"/api/v1/delivery/{token}"
        c.execute(
            "INSERT INTO delivery_tokens(token,job_id,api_key,expires_at,download_url,created_at) VALUES(?,?,?,?,?,?)",
            (token, job_id, api_key, expires, download_url, now),
        )
        c.commit()
        return {
            "token": token,
            "job_id": job_id,
            "api_key": api_key,
            "expires_at": expires,
            "download_url": download_url,
            "created_at": now,
        }
    finally:
        c.close()


def validate_delivery_token(token: str) -> Optional[Dict[str, Any]]:
    c = _conn()
    try:
        r = c.execute(
            "SELECT * FROM delivery_tokens WHERE token=?",
            (token,),
        ).fetchone()
        if not r:
            return None
        row = dict(r)
        now = time.time()
        expires = time.mktime(time.strptime(row["expires_at"], "%Y-%m-%dT%H:%M:%SZ"))
        if now > expires:
            c.execute("DELETE FROM delivery_tokens WHERE token=?", (token,))
            c.commit()
            return None
        return row
    finally:
        c.close()


# ── Webhooks ──────────────────────────────────────────────────────────────────


def record_webhook(event_type: str, api_key: str, amount_cents: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    c = _conn()
    try:
        webhook_id = f"wh_{int(time.time()*1000)}_{api_key[-8:]}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        c.execute(
            "INSERT INTO webhooks(webhook_id,event_type,api_key,amount_cents,payload,created_at) VALUES(?,?,?,?,?,?)",
            (webhook_id, event_type, api_key, amount_cents, json.dumps(payload), now),
        )
        c.commit()
        return {"webhook_id": webhook_id, "event_type": event_type, "processed": False}
    finally:
        c.close()


def mark_webhook_processed(webhook_id: str, error: Optional[str] = None) -> None:
    c = _conn()
    try:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        c.execute(
            "UPDATE webhooks SET processed=1, processed_at=?, error=? WHERE webhook_id=?",
            (now, error, webhook_id),
        )
        c.commit()
    finally:
        c.close()


# ── Helpers ───────────────────────────────────────────────────────────────────


def add_purchase_record(
    purchase_id: str,
    api_key: str,
    stripe_session_id: str,
    amount_cents: int,
    credits: int,
    package: Optional[str] = None,
) -> Dict[str, Any]:
    c = _conn()
    try:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        c.execute(
            "INSERT OR IGNORE INTO credit_purchases(purchase_id,api_key,stripe_session_id,amount_cents,credits,package,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (purchase_id, api_key, stripe_session_id, amount_cents, credits, package, "completed", now, now),
        )
        c.commit()
        return {
            "purchase_id": purchase_id,
            "api_key": api_key,
            "amount_cents": amount_cents,
            "credits": credits,
            "package": package,
            "status": "completed",
        }
    finally:
        c.close()


def get_all_keys() -> List[Dict[str, Any]]:
    c = _conn()
    try:
        rows = c.execute("SELECT key,email,plan,quota_tokens,rate_per_min,active,created_at FROM api_keys").fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def get_credit_purchases(api_key: str, limit: int = 20) -> List[Dict[str, Any]]:
    c = _conn()
    try:
        rows = c.execute(
            "SELECT * FROM credit_purchases WHERE api_key=? ORDER BY created_at DESC LIMIT ?",
            (api_key, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def get_job_raw(job_id: str) -> Optional[Dict[str, Any]]:
    return get_job(_conn(), job_id)

