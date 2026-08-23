"""
hardonia-compute-api/services.py

Job execution engine:
- chat -> Ollama router/lanes
- image/workflow -> ComfyUI prompt + poll
- credits enforced before run
- webhook callback on completion
- retry with backoff
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Any, Dict, Optional

import httpx

from app.config import settings

# Pricing in credits
CREDITS_PER_1K_TOKENS = 8
CREDITS_PER_IMAGE = 20
CREDITS_PER_WORKFLOW = 50

# Ollama lane fallback order
_LANES = [11438, 11434, 11435, 11436, 11437]


# ── Ollama client ─────────────────────────────────────────────────────────────


def _parse_ollama(data: dict, model: str):
    if "choices" in data:
        msg = data["choices"][0]["message"]["content"]
        u = data.get("usage", {}) or {}
        pt = u.get("prompt_tokens") or u.get("prompt_eval_count") or 0
        ct = u.get("completion_tokens") or u.get("eval_count") or 0
        tt = u.get("total_tokens") or (pt + ct)
        return msg, pt, ct, tt
    msg = data.get("message", {}).get("content", "")
    pt = data.get("prompt_eval_count", 0)
    ct = data.get("eval_count", 0)
    tt = pt + ct
    return msg, pt, ct, tt


async def _try_openai(c: httpx.AsyncClient, model: str, messages: list, temperature: float, max_tokens: int):
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
    r = await c.post(f"{settings.ollama_router_url}/v1/chat/completions", json=payload)
    r.raise_for_status()
    return r.json()


async def _try_native(c: httpx.AsyncClient, port: int, model: str, messages: list, temperature: float, max_tokens: int):
    payload = {"model": model, "messages": messages, "temperature": temperature, "num_predict": max_tokens, "stream": False}
    r = await c.post(f"http://127.0.0.1:{port}/api/chat", json=payload)
    r.raise_for_status()
    return r.json()


async def chat_completion(model: str, messages: list, temperature: float = 0.7, max_tokens: int = 512, api_key: str = "", timeout: float = 120.0):
    t0 = time.monotonic()
    last_err = None
    async with httpx.AsyncClient(timeout=timeout) as c:
        try:
            data = await _try_openai(c, model, messages, temperature, max_tokens)
            msg, pt, ct, tt = _parse_ollama(data, model)
            lat = int((time.monotonic() - t0) * 1000)
            cost = (tt / 1000.0) * CREDITS_PER_1K_TOKENS
            return {"model": data.get("model", model), "content": msg,
                    "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt},
                    "cost_credits": round(cost, 2), "latency_ms": lat}
        except Exception as e:
            last_err = e
        for port in _LANES:
            try:
                data = await _try_native(c, port, model, messages, temperature, max_tokens)
                msg, pt, ct, tt = _parse_ollama(data, model)
                lat = int((time.monotonic() - t0) * 1000)
                cost = (tt / 1000.0) * CREDITS_PER_1K_TOKENS
                return {"model": model, "content": msg,
                        "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt},
                        "cost_credits": round(cost, 2), "latency_ms": lat}
            except Exception as e:
                last_err = e
    raise RuntimeError(f"all lanes failed: {last_err}")


# ── ComfyUI client ────────────────────────────────────────────────────────────


async def comfyui_prompt(workflow: dict, client_id: str = "hardonia-compute-api", timeout: float = 180.0):
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(f"{settings.comfyui_url}/prompt", json={"prompt": workflow, "client_id": client_id})
        r.raise_for_status()
        return r.json()


async def comfyui_history(prompt_id: str, timeout: float = 15.0):
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.get(f"{settings.comfyui_url}/history/{prompt_id}")
        r.raise_for_status()
        return r.json()


async def image_generate(workflow: dict, api_key: str = "", timeout: float = 300.0):
    t0 = time.monotonic()
    try:
        payload = await comfyui_prompt(workflow)
    except Exception as exc:
        lat = int((time.monotonic() - t0) * 1000)
        return {"prompt_id": None, "cost_credits": 0, "latency_ms": lat, "status": "failed", "error": f"comfyui_prompt_failed: {exc}"}
    prompt_id = payload.get("prompt_id")
    if not prompt_id:
        lat = int((time.monotonic() - t0) * 1000)
        return {"prompt_id": None, "cost_credits": 0, "latency_ms": lat, "status": "failed", "error": "comfyui_did_not_return_prompt_id"}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            hist = await comfyui_history(prompt_id)
        except Exception as exc:
            lat = int((time.monotonic() - t0) * 1000)
            return {"prompt_id": prompt_id, "cost_credits": 0, "latency_ms": lat, "status": "failed", "error": f"comfyui_history_failed: {exc}"}
        if prompt_id in hist:
            entry = hist[prompt_id]
            status = entry.get("status", {})
            if status.get("completed") or status.get("status_str") == "success":
                lat = int((time.monotonic() - t0) * 1000)
                return {"prompt_id": prompt_id, "cost_credits": CREDITS_PER_IMAGE, "latency_ms": lat, "status": "completed", "outputs": entry.get("outputs", {})}
            if status.get("failed"):
                lat = int((time.monotonic() - t0) * 1000)
                return {"prompt_id": prompt_id, "cost_credits": 0, "latency_ms": lat, "status": "failed", "error": "comfyui_job_failed", "details": status}
        await asyncio.sleep(2)
    lat = int((time.monotonic() - t0) * 1000)
    return {"prompt_id": prompt_id, "cost_credits": 0, "latency_ms": lat, "status": "timeout"}


# ── Webhook delivery ──────────────────────────────────────────────────────────


async def deliver_webhook(callback_url: str, payload: Dict[str, Any], timeout: float = 10.0):
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(callback_url, json=payload)
        r.raise_for_status()
        return {"status_code": r.status_code, "text": r.text[:220]}


# ── Retry helper ──────────────────────────────────────────────────────────────


async def run_with_retry(coro_factory, max_attempts: int = 3, base_delay: float = 1.0):
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_factory()
        except Exception as e:
            last_err = e
            if attempt == max_attempts:
                break
            await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
    raise RuntimeError(f"job failed after {max_attempts} attempts: {last_err}")


async def list_models():
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(f"{__import__('app.config', fromlist=['settings']).settings.ollama_router_url}/v1/models")
        if r.status_code == 200:
            return r.json().get("data", [])
        r2 = await c.get(f"{__import__('app.config', fromlist=['settings']).settings.ollama_router_url}/api/tags")
        if r2.status_code == 200:
            return [{"id": m["name"]} for m in r2.json().get("models", [])]
        return []


async def gpu_status():
    import httpx
    async with httpx.AsyncClient(timeout=8.0) as c:
        r = await c.get(f"{__import__('app.config', fromlist=['settings']).settings.audit_api_url}/health")
        if r.status_code != 200:
            return {"error": "audit-api unreachable"}
        body = r.json()
    metrics = body.get("metrics", {})
    return {
        "status": body.get("status"),
        "gpu": metrics.get("gpu_metrics"),
        "api_health": metrics.get("api_health"),
        "ts": body.get("ts"),
    }


async def run_ollama_job(job_id: str, payload: dict):
    model = payload.get("model", "llama3")
    prompt = payload.get("prompt", "")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            return {"status": "completed", "result": result.get("response", "")}
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}


async def run_comfyui_job(job_id: str, payload: dict):
    workflow = payload.get("workflow", {})
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8188/prompt",
                json={"prompt": workflow},
                timeout=300.0
            )
            response.raise_for_status()
            result = response.json()
            return {"status": "completed", "result": result}
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}


async def dispatch_job(job_id: str, payload: dict):
    job_type = payload.get("type", "ollama")
    if job_type == "comfyui":
        return await run_comfyui_job(job_id, payload)
    return await run_ollama_job(job_id, payload)
