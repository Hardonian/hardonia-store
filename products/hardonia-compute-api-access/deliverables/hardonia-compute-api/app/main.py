"""
hardonia-compute-api/app/main.py

Production pay-by-the-job compute API:
- Authenticated job submission for chat/image/workflow
- Credit-gated execution with prepaid credits
- Job queue with status tracking and retries
- Webhook callbacks on completion
- Signed delivery tokens for result retrieval
- Admin key issuance and key management
- Live health and GPU/model endpoints
"""
from __future__ import annotations

import hmac
import json
import os
import secrets
import time
from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.security import APIKeyHeader

from app import db
from app.auth import require_key
from app.config import settings
from app.schemas import (
    ApiKeyCreate,
    ApiKeyUpdate,
    CreditBalance,
    CreditPackage,
    CreditPurchase,
    CreditTopUp,
    CreditTransaction,
    DeliveryRequest,
    HealthCheck,
    HealthResponse,
    Job,
    JobList,
    JobStatus,
    JobType,
    WebhookEventType,
)
from app.services import (
    chat_completion,
    comfyui_history,
    comfyui_prompt,
    deliver_webhook,
    image_generate,
    run_with_retry,
)
from app.db import consume_credits, add_purchase_record

app = FastAPI(title="Hardonia Compute API", version="2.1.0")

# ── Request timing middleware ─────────────────────────────────────────────────
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response

db.init_db()

# ── CORS ─────────────────────────────────────────────────────────────────────

_ALLOWED_ORIGINS = [
    "https://aiautomatedsystems.ca",
    "https://www.aiautomatedsystems.ca",
    "https://play.aiautomatedsystems.ca",
    "https://api.aiautomatedsystems.ca",
    "http://127.0.0.1:8050",
    "http://localhost:8050",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["X-API-Key", "X-Admin-Key", "Content-Type"],
    max_age=600,
)

# ── Constants ────────────────────────────────────────────────────────────────



# ── Request body helper ─────────────────────────────────────────────────────
# Avoid FastAPI/Pydantic body-param adapter edge cases with future annotations
# by parsing JSON manually and validating explicitly.


async def _json_body(request: Request) -> Dict[str, Any]:
    try:
        return json.loads(await request.body() or "{}")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON body: {exc}")


def _schema(name: str):
    from app import schemas as _schemas
    return getattr(_schemas, name)


def _validate(schema, data: Dict[str, Any]):
    try:
        return schema.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

CREDITS_PER_1K_TOKENS = 8
CREDITS_PER_IMAGE = 20
CREDITS_PER_WORKFLOW = 50



# ── Global exception handler ──────────────────────────────────────────────────
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# ── Health ────────────────────────────────────────────────────────────────────


def _time_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@app.get("/health", response_model=HealthResponse)
async def health():
    checks = [
        HealthCheck(service="compute-api", status="ok", detail="running", ts=_time_now()),
        HealthCheck(service="database", status="ok", detail=settings.db_path, ts=_time_now()),
        HealthCheck(service="redis", status="disabled", detail="redis not installed", ts=_time_now()),
        HealthCheck(service="ollama-router", status="unknown", detail=settings.ollama_router_url, ts=_time_now()),
        HealthCheck(service="comfyui", status="unknown", detail=settings.comfyui_url, ts=_time_now()),
    ]
    return HealthResponse(status="ok", checks=checks, ts=_time_now())


# ── Public meta ───────────────────────────────────────────────────────────────


@app.get("/v1/models")
async def models():
    try:
        from app.services import list_models

        data = await list_models()
        return {"status": "ok", "models": data}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=502)


@app.get("/v1/gpu")
async def gpu():
    try:
        from app.services import gpu_status

        return await gpu_status()
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=502)


# ── Jobs ──────────────────────────────────────────────────────────────────────


@app.post("/api/v1/jobs", response_model=Job)
async def create_job_endpoint(request: Request, api_key: str = Depends(require_key)):
    key_info = db.get_key(api_key)
    if not key_info or not key_info.get("active", 1):
        raise HTTPException(status_code=403, detail="API key inactive")
    payload = _validate(_schema("JobCreate"), await _json_body(request))
    if payload.job_type == JobType.chat:
        estimated_tokens = 2000
        cost_credits = max(1, int((estimated_tokens / 1000.0) * CREDITS_PER_1K_TOKENS))
    elif payload.job_type == JobType.image:
        cost_credits = CREDITS_PER_IMAGE
    elif payload.job_type == JobType.workflow:
        cost_credits = CREDITS_PER_WORKFLOW
    else:
        cost_credits = 1

    balance = db.credit_balance_simple(api_key)
    if balance < cost_credits:
        raise HTTPException(status_code=402, detail=f"Insufficient credits: {balance} < {cost_credits}")

    job_id = f"job_{int(time.time()*1000)}_{secrets.token_urlsafe(8)}"
    job = db.create_job(
        job_id=job_id,
        api_key=api_key,
        job_type=payload.job_type.value,
        prompt=payload.prompt or "",
        workflow=payload.workflow,
        model=payload.model,
        params=payload.params,
        callback_url=payload.callback_url,
    )
    return job_to_schema(job)


@app.get("/api/v1/jobs", response_model=JobList)
async def list_jobs_endpoint(api_key: str = Depends(require_key), status: Optional[str] = None, page: int = 1, page_size: int = 20):
    if page_size > 100:
        page_size = 100
    result = db.list_jobs(api_key, status=status, page=page, page_size=page_size)
    return JobList(
        jobs=[job_to_schema(j) for j in result["jobs"]],
        count=result["count"],
        page=result["page"],
        page_size=result["page_size"],
    )


@app.get("/api/v1/jobs/{job_id}", response_model=Job)
async def get_job_endpoint(job_id: str, api_key: str = Depends(require_key)):
    job = db.get_job_raw(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["api_key"] != api_key:
        raise HTTPException(status_code=403, detail="Not your job")
    return job_to_schema(job)


@app.delete("/api/v1/jobs/{job_id}")
async def cancel_job_endpoint(job_id: str, api_key: str = Depends(require_key)):
    job = db.get_job_raw(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["api_key"] != api_key:
        raise HTTPException(status_code=403, detail="Not your job")
    if job["status"] in ("completed", "failed", "cancelled", "timeout"):
        raise HTTPException(status_code=400, detail=f"Job already {job['status']}")
    updated = db.update_job_status(job_id, "cancelled", error="cancelled by user")
    return job_to_schema(updated)


# ── Job execution engine ──────────────────────────────────────────────────────


@app.post("/api/v1/jobs/{job_id}/run", response_model=Job)
async def run_job_endpoint(job_id: str, request: Request, api_key: str = Depends(require_key)):
    job = db.get_job_raw(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["api_key"] != api_key:
        raise HTTPException(status_code=403, detail="Not your job")
    if job["status"] not in ("pending", "queued", "timeout", "failed"):
        raise HTTPException(status_code=400, detail=f"Job status {job['status']} is not runnable")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["api_key"] != api_key:
        raise HTTPException(status_code=403, detail="Not your job")
    if job["status"] not in ("pending", "queued", "timeout", "failed"):
        raise HTTPException(status_code=400, detail=f"Job status {job['status']} is not runnable")

    if job["job_type"] == "chat":
        cost_credits = max(1, int((2000 / 1000.0) * CREDITS_PER_1K_TOKENS))
    elif job["job_type"] == "image":
        cost_credits = CREDITS_PER_IMAGE
    elif job["job_type"] == "workflow":
        cost_credits = CREDITS_PER_WORKFLOW
    else:
        cost_credits = 1

    try:
        consume_credits(api_key, cost_credits, ref_type="job", ref_id=job_id, reason=f"Reserve credits for {job['job_type']}")
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))

    db.update_job_status(job_id, "running", cost_credits=cost_credits)

    async def _execute():
        if job["job_type"] == "chat":
            result = await run_with_retry(
                lambda: chat_completion(
                    model=job.get("model") or "llama3.1:8b",
                    messages=[{"role": "user", "content": job.get("prompt", "")}],
                ),
                max_attempts=job.get("max_attempts", 3),
            )
            actual_cost = max(1, int(result.get("cost_credits", cost_credits)))
            return {
                "model": result.get("model"),
                "content": result.get("content"),
                "usage": result.get("usage", {}),
                "cost_credits": actual_cost,
                "latency_ms": result.get("latency_ms", 0),
            }

        workflow = job.get("workflow") or {}
        if not workflow:
            raise RuntimeError("Missing workflow for image/workflow job")

        if job["job_type"] == "image":
            result = await image_generate(workflow, api_key=api_key)
            return {
                "prompt_id": result.get("prompt_id"),
                "cost_credits": result.get("cost_credits", CREDITS_PER_IMAGE),
                "latency_ms": result.get("latency_ms", 0),
                "status": result.get("status"),
                "outputs": result.get("outputs", {}),
            }

        if job["job_type"] == "workflow":
            result = await image_generate(workflow, api_key=api_key)
            return {
                "prompt_id": result.get("prompt_id"),
                "cost_credits": result.get("cost_credits", CREDITS_PER_WORKFLOW),
                "latency_ms": result.get("latency_ms", 0),
                "status": result.get("status"),
                "outputs": result.get("outputs", {}),
            }

        raise RuntimeError(f"Unknown job_type: {job['job_type']}")

    try:
        result = await _execute()
        actual_cost = result.pop("cost_credits", cost_credits)
        if actual_cost != cost_credits:
            diff = actual_cost - cost_credits
            if diff > 0:
                consume_credits(api_key, diff, ref_type="job", ref_id=job_id, reason="Actual cost adjustment")
            elif diff < 0:
                db.add_credits(api_key, abs(diff), ref_type="job", ref_id=job_id, reason="Actual cost adjustment refund")

        final_status = result.get("status")
        if final_status not in ("completed", "failed", "timeout"):
            final_status = "completed"

        if final_status == "completed":
            if actual_cost != cost_credits:
                diff = actual_cost - cost_credits
                if diff > 0:
                    consume_credits(api_key, diff, ref_type="job", ref_id=job_id, reason="Actual cost adjustment")
                elif diff < 0:
                    db.add_credits(api_key, abs(diff), ref_type="job", ref_id=job_id, reason="Actual cost adjustment refund")
            delivery = db.create_delivery_token(job_id=job_id, api_key=api_key)
            result["delivery_token"] = delivery["token"]
            result["download_url"] = delivery["download_url"]
            if job.get("callback_url"):
                try:
                    await deliver_webhook(job["callback_url"], {
                        "job_id": job_id,
                        "status": "completed",
                        "result": result,
                        "ts": _time_now(),
                    })
                except Exception:
                    pass
        else:
            if actual_cost != cost_credits:
                diff = actual_cost - cost_credits
                if diff < 0:
                    db.add_credits(api_key, abs(diff), ref_type="job", ref_id=job_id, reason="Failed job cost refund")
                actual_cost = max(0, actual_cost)
            result.pop("delivery_token", None)
            result.pop("download_url", None)

        updated = db.update_job_status(job_id, final_status, result=result, cost_credits=actual_cost, error=result.get("error"))

        if job.get("callback_url"):
            try:
                await deliver_webhook(job["callback_url"], {
                    "job_id": job_id,
                    "status": "completed",
                    "result": result,
                    "ts": _time_now(),
                })
            except Exception:
                pass

        return job_to_schema(updated)

    except Exception as e:
        try:
            db.add_credits(api_key, cost_credits, ref_type="job", ref_id=job_id, reason=f"Refund: {str(e)[:80]}")
        except Exception:
            pass
        updated = db.update_job_status(job_id, "failed", error=str(e))
        return job_to_schema(updated)


# ── Delivery tokens ───────────────────────────────────────────────────────────


@app.post("/api/v1/delivery/request")
async def request_delivery(request: Request, api_key: str = Depends(require_key)):
    payload = _validate(_schema("DeliveryRequest"), await _json_body(request))
    job = db.get_job_raw(payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["api_key"] != api_key:
        raise HTTPException(status_code=403, detail="Not your job")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is {job['status']}, not completed")
    delivery = db.create_delivery_token(job_id=payload.job_id, api_key=api_key)
    return delivery


@app.get("/api/v1/delivery/{token}", response_class=PlainTextResponse)
async def download_delivery(token: str):
    token_info = db.validate_delivery_token(token)
    if not token_info:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    job = db.get_job_raw(token_info["job_id"])
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result = job.get("result") or {}
    return PlainTextResponse(content=json.dumps(result, indent=2, default=str))


# ── Credits ───────────────────────────────────────────────────────────────────


@app.get("/api/v1/credits/balance")
async def credit_balance_endpoint(api_key: str = Depends(require_key)):
    balance = db.credit_balance_simple(api_key)
    summary = db.key_summary(api_key)
    return CreditBalance(
        api_key=api_key,
        balance=balance,
        total_purchased=balance,
        total_consumed=summary.get("used_tokens", 0),
        last_transaction_at=None,
    )


@app.post("/api/v1/credits/topup")
async def credit_topup(request: Request, api_key: str = Depends(require_key)):
    payload = _validate(_schema("CreditTopUp"), await _json_body(request))
    if payload.amount_cents < 100:
        raise HTTPException(status_code=400, detail="Minimum top-up is $1.00")
    result = db.add_credits(
        api_key,
        payload.amount_cents // 100,
        ref_type="topup",
        reason="Manual top-up",
    )
    return result


@app.get("/api/v1/credits/transactions")
async def credit_transactions(api_key: str = Depends(require_key), limit: int = 50):
    rows = db.list_transactions(api_key, limit=limit)
    return [CreditTransaction(**r) for r in rows]


@app.post("/api/v1/credits/purchase")
async def credit_purchase(request: Request, api_key: str = Depends(require_key)):
    payload = _validate(_schema("CreditPurchase"), await _json_body(request))
    package_credits = {
        CreditPackage.starter: 500,
        CreditPackage.growth: 2500,
        CreditPackage.scale: 10000,
        CreditPackage.enterprise: 50000,
    }
    credits = package_credits.get(payload.package, 0)
    if credits <= 0:
        raise HTTPException(status_code=400, detail="Invalid package")
    purchase_id = f"cp_{int(time.time()*1000)}_{api_key[-8:]}"
    purchase = db.add_purchase_record(
        purchase_id=purchase_id,
        api_key=api_key,
        stripe_session_id=payload.payment_method_id or "manual",
        amount_cents=_package_price(payload.package),
        credits=credits,
        package=payload.package.value,
    )
    if not payload.payment_method_id:
        db.add_credits(api_key, credits, ref_type="purchase", ref_id=purchase_id, reason=f"Package {payload.package.value}")
    return purchase


# ── Webhooks ──────────────────────────────────────────────────────────────────


@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    body = await request.json()
    event_type = body.get("type", "unknown")
    session = body.get("data", {}).get("object", {})
    api_key = session.get("client_reference_id") or session.get("metadata", {}).get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing api_key in webhook metadata")

    amount_cents = session.get("amount_total") or session.get("amount_subtotal") or 0
    webhook = db.record_webhook(event_type, api_key, amount_cents, body)

    if event_type == WebhookEventType.checkout_completed.value:
        package = session.get("metadata", {}).get("package", "starter")
        package_credits = {
            "starter": 500,
            "growth": 2500,
            "scale": 10000,
            "enterprise": 50000,
        }
        credits = package_credits.get(package, 500)
        db.add_credits(api_key, credits, ref_type="webhook", ref_id=webhook["webhook_id"], reason=f"Stripe purchase: {package}")
        db.mark_webhook_processed(webhook["webhook_id"])

    return {"status": "ok", "webhook_id": webhook["webhook_id"]}


# ── Usage ─────────────────────────────────────────────────────────────────────


@app.get("/api/v1/usage")
async def usage(api_key: str = Depends(require_key)):
    summary = db.key_summary(api_key)
    recent = db.usage_for(api_key)
    return {
        "status": "ok",
        "key": api_key[:10] + "...",
        "summary": summary,
        "recent": recent,
    }


# ── Admin ─────────────────────────────────────────────────────────────────────


_admin = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def _require_admin(admin: Optional[str]) -> None:
    if not settings.admin_key or not hmac.compare_digest(admin or "", settings.admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")


@app.post("/admin/keys")
async def issue_key(request: Request, admin: Optional[str] = Depends(_admin)):
    payload = _validate(_schema("ApiKeyCreate"), await _json_body(request))
    _require_admin(admin)
    client = (request.client.host if request and request.client else "") or ""
    if settings.admin_local_only and client not in ("127.0.0.1", "::1", ""):
        raise HTTPException(status_code=403, detail="admin endpoint is loopback-only")
    k = "hk_" + secrets.token_urlsafe(18)
    info = db.create_key(
        k,
        email=payload.email,
        plan=payload.plan,
        quota=payload.quota_tokens,
        rate_per_min=payload.rate_per_min,
        initial_credits=payload.initial_credits,
    )
    return {"status": "ok", **info}


@app.get("/admin/keys")
async def list_keys(admin: Optional[str] = Depends(_admin)):
    _require_admin(admin)
    return db.get_all_keys()


@app.patch("/admin/keys/{key}")
async def update_key(key: str, payload: ApiKeyUpdate = Body(embed=True), admin: Optional[str] = Depends(_admin)):
    _require_admin(admin)
    existing = db.get_key(key)
    if not existing:
        raise HTTPException(status_code=404, detail="Key not found")
    if payload.plan is not None:
        db.update_key_field(key, "plan", payload.plan)
    if payload.active is not None:
        db.set_key_active(key, payload.active)
    if payload.quota_tokens is not None:
        db.update_key_field(key, "quota_tokens", payload.quota_tokens)
    if payload.rate_per_min is not None:
        db.update_key_field(key, "rate_per_min", payload.rate_per_min)
    return {"status": "ok", "key": key}


@app.delete("/admin/keys/{key}")
async def revoke_key(key: str, admin: Optional[str] = Depends(_admin)):
    _require_admin(admin)
    db.set_key_active(key, False)
    return {"status": "ok", "revoked": key}


# ── Playground ────────────────────────────────────────────────────────────────


@app.get("/play")
async def playground():
    html = _PLAYGROUND_HTML.replace("{{DEMO_KEY}}", settings.demo_key)
    return HTMLResponse(content=html)


# ── Internal helpers ──────────────────────────────────────────────────────────


def job_to_schema(row: Dict[str, Any]) -> Job:
    return Job(
        job_id=row["job_id"],
        api_key=row["api_key"],
        job_type=JobType(row["job_type"]),
        status=JobStatus(row["status"]),
        model=row.get("model"),
        prompt=row.get("prompt") or "",
        workflow=row.get("workflow") or {},
        params=row.get("params") or {},
        callback_url=row.get("callback_url"),
        result=row.get("result") or {},
        error=row.get("error"),
        cost_credits=row.get("cost_credits") or 0,
        credits_before=row.get("credits_before") or 0,
        credits_after=row.get("credits_after") or 0,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        started_at=row.get("started_at"),
        completed_at=row.get("completed_at"),
        external_prompt_id=row.get("external_prompt_id"),
    )


def _package_price(pkg: CreditPackage) -> int:
    return {
        CreditPackage.starter: 999,
        CreditPackage.growth: 2999,
        CreditPackage.scale: 9999,
        CreditPackage.enterprise: 29999,
    }.get(pkg, 999)


_PLAYGROUND_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <title>Hardonia Compute Playground</title>
  <meta charset="utf-8">
  <style>
    body { font-family: system-ui; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background: #0b0d12; color: #e7e9ee; }
    input, textarea, select, button { width: 100%; padding: .6rem; margin: .4rem 0; background: #151922; color: #e7e9ee; border: 1px solid #222a36; border-radius: 8px; }
    button { background: #f3a73c; color: #0b0d12; font-weight: 600; cursor: pointer; }
    pre { background: #0b0d12; padding: 1rem; border-radius: 8px; border: 1px solid #222a36; overflow: auto; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  </style>
</head>
<body>
  <h1>Hardonia Compute Playground</h1>
  <p>Demo key: <code>{{DEMO_KEY}}</code></p>
  <div class="row">
    <div>
      <h3>Chat</h3>
      <input id="chatModel" value="llama3.1:8b">
      <textarea id="chatPrompt" rows="4">Reply with exactly: PONG</textarea>
      <button onclick="chat()">Run Chat Job</button>
      <pre id="chatOut">...</pre>
    </div>
    <div>
      <h3>GPU Status</h3>
      <button onclick="gpu()">Refresh GPU</button>
      <pre id="gpuOut">...</pre>
    </div>
  </div>
  <script>
    const API_KEY = '{{DEMO_KEY}}';
    const headers = () => ({ 'X-API-Key': API_KEY, 'Content-Type': 'application/json' });
    async function chat() {
      const model = document.getElementById('chatModel').value;
      const prompt = document.getElementById('chatPrompt').value;
      const out = document.getElementById('chatOut');
      out.textContent = 'Running...';
      try {
        const res = await fetch('/api/v1/jobs', { method: 'POST', headers: headers(), body: JSON.stringify({ job_type: 'chat', model, prompt }) });
        const job = await res.json();
        out.textContent = JSON.stringify(job, null, 2);
      } catch (e) { out.textContent = 'Error: ' + e.message; }
    }
    async function gpu() {
      const out = document.getElementById('gpuOut');
      try {
        const res = await fetch('/v1/gpu');
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
      } catch (e) { out.textContent = 'Error: ' + e.message; }
    }
    gpu();
  </script>
</body>
</html>
"""


@app.get("/api/v1/metering/gpu")
async def gpu_metering():
    import time
    return {
        "timestamp": int(time.time()),
        "gpus": [
            {"id": "v100", "memory_used_mb": 0, "utilization_pct": 0, "hourly_rate_cents": 50},
            {"id": "p40", "memory_used_mb": 0, "utilization_pct": 0, "hourly_rate_cents": 35},
            {"id": "3060", "memory_used_mb": 0, "utilization_pct": 0, "hourly_rate_cents": 20},
        ],
        "billing_model": "per-minute GPU allocation",
    }
