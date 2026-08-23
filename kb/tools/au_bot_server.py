#!/usr/bin/env python3
"""
AU bot intake server (Hardonia Auth/Access Unit).
Exposes the au_bot answer/escalation engine over HTTP so the storefront / email / chat can
call it. Stdlib only (http.server) — zero extra deps, no Docker bloat.

Endpoints:
  POST /au/ask      {"query": "...", "history": ["...", ...]}  -> {answer} or {escalation}
  GET  /au/health   -> {status, snapshot_at, capacity_ok, intel_block, legal_clear}
  GET  /au/ready    -> "ok" (200) for liveness probes

Design:
- Reuses au_bot.answer() (guardrails + FAQ routing + snapshot state) — single source of truth.
- On escalation, optionally opens a GitHub issue via tools/github_issue.py (if GH_ISSUE=1).
- Reads snapshot.json live each request (no stale cache).
- Kill-switch: if snapshot legal.minor_safety_clear=false OR intel.block=true, /au/ask returns a
  safe "temporarily unavailable" escalation without invoking the model path.

Run: python3 au_bot_server.py   (listens 127.0.0.1:8071)
Fronted by Caddy reverse_proxy /au/ -> 127.0.0.1:8071 (add to Caddyfile site block).
"""
import json, os, sys, subprocess, datetime, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import au_bot as bot

HOST = "127.0.0.1"
PORT = int(os.environ.get("AU_BOT_PORT", "8071"))
GH_ISSUE = (
    os.environ.get("GH_ISSUE", "0") == "1"
    and os.environ.get("AU_ALLOW_AUTO_ISSUES", "0") == "1"
)
REPO = "Hardonian/hardonia-compute-api"
SNAP = bot.SNAP_PATH
MAX_BODY_BYTES = 16_384


def snapshot_state():
    try:
        d = json.load(open(SNAP))
    except Exception:
        return {"capacity_ok": True, "intel_block": False, "legal_clear": True, "at": None}
    return {
        "capacity_ok": d.get("compute", {}).get("capacity_ok", True),
        "intel_block": d.get("intel", {}).get("block", False),
        "legal_clear": d.get("legal", {}).get("minor_safety_clear", True),
        "at": d.get("generated_at"),
    }

def _parse_handoff(esc_text):
    """Strip the leading label line of an escalation and parse the JSON handoff."""
    js = esc_text.split("\n", 1)[1] if "\n" in esc_text else "{}"
    try:
        return json.loads(js)
    except Exception:
        return {"raw": esc_text[:300]}

# ---- per-IP rate limit (in-memory; restart clears) ----
from collections import defaultdict, deque
_ASK_RL = defaultdict(deque)
_ASK_RL_MAX = 10      # max asks
_ASK_RL_WINDOW = 60   # per 60s per IP

def _rate_ok(ip):
    dq = _ASK_RL[ip]
    now = time.time()
    while dq and now - dq[0] > _ASK_RL_WINDOW:
        dq.popleft()
    if len(dq) >= _ASK_RL_MAX:
        return False
    dq.append(now)
    return True

def open_issue(payload):
    """Best-effort GitHub issue creation; never blocks the customer response."""
    if not GH_ISSUE:
        return None
    try:
        title = f"[auth] {payload.get('auth_event','escalation')} — {str(payload.get('symptom',''))[:60]}"
        body = json.dumps(payload, indent=2)
        p = subprocess.run(
            ["python3", os.path.join(HERE, "github_issue.py"), "--title", title, "--body", body, "--label", "auth"],
            capture_output=True, text=True, timeout=20,
        )
        if p.returncode == 0:
            return p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "created"
        return f"error: {p.stderr.strip()[:120]}"
    except Exception as e:
        return f"exception: {e}"

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/") in ("/au/health", "/au/health/"):
            st = snapshot_state()
            self._send(200, {"status": "ok", **st})
        elif self.path.rstrip("/") in ("/au/ready", "/au/ready/"):
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.rstrip("/") != "/au/ask":
            self._send(404, {"error": "not found"}); return
        try:
            raw_length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            self._send(400, {"error": "invalid content length"}); return
        if raw_length <= 0 or raw_length > MAX_BODY_BYTES:
            self._send(413, {"error": "request too large"}); return
        try:
            req = json.loads(self.rfile.read(raw_length))
        except Exception:
            self._send(400, {"error": "bad json"}); return
        q = (req.get("query") or "").strip()
        hist = req.get("history") or []
        if not q:
            self._send(400, {"error": "query required"}); return
        # per-IP rate limit on the ask endpoint (prevents bot/gh flooding)
        ip = self.client_address[0]
        if not _rate_ok(ip):
            self._send(429, {"error": "rate limited", "retry_after": _ASK_RL_WINDOW})
            return

        # Kill-switch (safety): bot.live_state() reads flag files + snapshot directly.
        st = bot.live_state()
        if not st["legal_clear"] or st["intel_block"]:
            esc = bot.escalate("S1", "legal", "kill_switch", q[:200], "-", None, None,
                               hist + [q], ["kill_switch"])
            handoff = _parse_handoff(esc)
            self._send(200, {"escalation": esc, "issue": open_issue(handoff)})
            return

        out = bot.answer(q, hist)
        if out.startswith("[ESCALATION"):
            handoff = _parse_handoff(out)
            if isinstance(handoff, dict):
                handoff.setdefault("customer_query_redacted", bot.redact(q))
            issue = open_issue(handoff) if isinstance(handoff, dict) else None
            self._send(200, {"escalation": out, "issue": issue})
        else:
            self._send(200, {"answer": out})

    def log_message(self, format, *args):  # quiet
        pass

if __name__ == "__main__":
    print(f"AU bot intake server on {HOST}:{PORT} (GH_ISSUE={GH_ISSUE})", flush=True)
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
