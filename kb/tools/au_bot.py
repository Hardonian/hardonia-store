#!/usr/bin/env python3
"""
AU — Auth/Access Unit support bot (Hardonia).
Ingests kb/faq-customer.md + kb/runbooks/ + kb/feeds/* and answers customer auth/access
questions with guardrails. NOT a toy: it enforces the hard rules from kb/au-support-bot.md.

Hardening (2026-07-12):
- Reads intel-flag.json + legal.json DIRECTLY (not just snapshot) -> real sub-second kill-switch.
- LEAK_RE fixed; transcript redacted before any escalation handoff (no re-leak to GitHub).
- Grounded generative fallback via local Ollama (hermes3) ONLY when (a) FAQ has a confident
  keyword match AND (b) Ollama is reachable AND (c) no guardrail trips. Never invents behavior.
- Capacity/intel/legal state read live from snapshot + flag files every call.

Usage:
  python3 au_bot.py "How do I authenticate to the Compute API?"
  python3 au_bot.py --interactive
  echo "I get 403 invalid api key" | python3 au_bot.py -
"""
import argparse, json, os, re, sys, urllib.request

KB = "/home/scott/hardonia.store/kb"
FAQ = os.path.join(KB, "faq-customer.md")
SNAP_PATH = os.path.join(KB, "feeds", "snapshot.json")
INTEL_FLAG = os.path.join(KB, "feeds", "intel-flag.json")
LEGAL_FLAG = os.path.join(KB, "feeds", "legal.json")
OLLAMA_URL = os.environ.get("AU_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODELS = os.environ.get("AU_OLLAMA_MODELS", "hermes3:latest,qwen2.5-coder:7b,granite4.1:3b").split(",")
GEN_FALLBACK = os.environ.get("AU_GEN", "0") == "1"  # explicit opt-in only; deterministic FAQ is the safe default
MAX_QUERY_CHARS = 2000
MAX_HISTORY_ITEMS = 5
MAX_HISTORY_CHARS = 500
HISTORY_FILE = os.environ.get("AU_HISTORY", "/home/scott/hardonia.store/kb/feeds/au-log.json")


# ---- guardrail patterns (hard, non-negotiable) ----
# Fixed: sk- with >=8 alnum; common key header shapes; generic 20-64 char bearer tokens.
LEAK_RE = re.compile(
    r"\b(sk-[a-zA-Z0-9]{8,}|AKIA[0-9A-Z]{16}|x-api-key:\s*\S{6,}|"
    r"bearer\s+[a-zA-Z0-9\-_]{20,}|[a-zA-Z0-9]{32,64})\b", re.I)
MINOR_RE = re.compile(r"\b(minor|child|under\s*1[0-9]|underage|csam|cp\b|\d{1,2}\s*[- ]?year[- ]?old)\b", re.I)
INTERNAL_RE = re.compile(r"\b(127\.0\.0\.1|192\.168\.|10\.\d|209\.216|/root/|/var/lib/caddy|caddyfile|vram|gpu_util|cloudflared|noTLSVerify)\b", re.I)
ABUSE_RE = re.compile(r"\b(non-?consensual|deepfake\s+real|revenge\s+porn|hack\s+(into|someone)|crack\s+(a|someone)|bypass\s+auth)\b", re.I)

# ---- FAQ parse ----
def load_faq(path):
    if not os.path.exists(path):
        return []
    out, section, q, buf = [], "General", None, []
    with open(path) as f:
        for line in f:
            m = re.match(r"^##\s+(.*)", line)
            if m:
                if q is not None:
                    out.append({"section": section, "q": q, "a": "\n".join(buf).strip()})
                section, q, buf = m.group(1).strip(), None, []
                continue
            qm = re.match(r"^\*\*Q:\s*(.*)\*\*", line)
            if qm:
                if q is not None:
                    out.append({"section": section, "q": q, "a": "\n".join(buf).strip()})
                q, buf = qm.group(1).strip(), []
                continue
            am = re.match(r"^A:\s*(.*)", line)
            if am and q is not None:
                buf.append(am.group(1).strip())
                continue
            if q is not None:
                buf.append(line.strip())
    if q is not None:
        out.append({"section": section, "q": q, "a": "\n".join(buf).strip()})
    return out

FAQ_ENTRIES = load_faq(FAQ)

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

SNAP = load_json(SNAP_PATH, {})

# ---- live state: read flag files DIRECTLY (real kill-switch, not 30-min-delayed) ----
def live_state():
    flag = load_json(INTEL_FLAG, {"block": False, "active_flags": []})
    legal = load_json(LEGAL_FLAG, {"open_flags": [], "minor_safety_clear": True})
    snap = load_json(SNAP_PATH, {})
    return {
        "intel_block": bool(flag.get("block")) or bool(snap.get("intel", {}).get("block", False)),
        "legal_clear": bool(legal.get("minor_safety_clear", True))
                       and bool(snap.get("legal", {}).get("minor_safety_clear", True)),
        "capacity_ok": bool(snap.get("compute", {}).get("capacity_ok", True)),
        "active_flags": flag.get("active_flags", []),
        "open_legal": legal.get("open_flags", []),
    }

# ---- routing keywords per FAQ question ----
KEYWORDS = {
    "authenticate": ["authenticate", "x-api-key", "header", "how do i use", "api key", "api access", "how to connect"],
    "403": ["403", "invalid api key", "invalid key", "unauthorized key", "rejected"],
    "429": ["429", "rate limit", "too many attempts", "cooldown", "throttled", "limit"],
    "credits": ["credit", "quota", "exhaust", "top up", "top-up", "ran out", "balance"],
    "rotate": ["lost", "leaked", "compromise", "rotate", "reset key", "new key", "stolen"],
    "delivery": ["download", "404", "where", "receipt", "link", "not working", "deliver", "access file"],
    "refund": ["refund", "chargeback", "money back"],
    "billing": ["bill", "pay", "gumroad", "charge", "price", "cost", "invoice"],
    "status": ["down", "offline", "unreachable", "tls", "site", "outage", "not loading"],
    "product": ["what is", "comfyui", "n8n", "portrait", "health report", "compute api",
                "private inference", "ops checklist", "power bundle", "revenue loop", "workflow"],
}

def score(qtext):
    t = qtext.lower()
    best_k, best_s = None, 0
    for k, kws in KEYWORDS.items():
        s = sum(1 for kw in kws if kw in t)
        if s > best_s:
            best_k, best_s = k, s
    return best_k, best_s

# ---- guardrail engine ----
def guardrails(text):
    hits = []
    if LEAK_RE.search(text): hits.append("key_leak")
    if MINOR_RE.search(text): hits.append("minor_safety")
    if INTERNAL_RE.search(text): hits.append("internal_infra_exposure")
    if ABUSE_RE.search(text): hits.append("abuse")
    return hits

def redact(text):
    return LEAK_RE.sub("<REDACTED>", text)

def escalate(severity, product, auth_event, symptom, tried, order_id, api_key_hint, transcript, flags):
    # REDACT every transcript line before it ever leaves the bot (no re-leak to GitHub).
    clean = [redact(line) for line in (transcript or [])]
    handoff = {
        "severity": severity,
        "product": product,
        "auth_event": auth_event,
        "symptom": redact(symptom),
        "tried": tried,
        "order_id": order_id,
        "api_key_hint": api_key_hint,  # already <REDACTED> at call site
        "transcript": clean[-5:],
        "flag": flags,
        "generated_by": "AU bot (hardonia)",
    }
    return ("[ESCALATION to Hardonian/hardonia-compute-api — label: auth]\n"
            + json.dumps(handoff, indent=2)
            + "\n\n— AU (Hardonia Auth/Access) routed this to a human. We do not handle this "
              "autonomously for safety.")

# ---- grounded generative fallback (local Ollama only; never invents) ----
def generate_grounded(qtext, faq_entry):
    """Use local Ollama to paraphrase/extend the FAQ answer in a helpful tone.
    Strictly grounded: the prompt includes the REAL FAQ answer; model may rephrase only.
    Runs in a thread with a hard timeout so the customer never waits > ~8s; on timeout
    or error we return None and the caller falls back to the exact FAQ text."""
    if not GEN_FALLBACK:
        return None
    prompt = (
        "You are AU, Hardonia's Auth/Access support assistant. Answer the customer's "
        "question using ONLY the facts in the APPROVED ANSWER below. Do not add steps, "
        "URLs, prices, or behavior not in the answer. Keep it under 80 words, friendly, "
        "no markdown code fences.\n\n"
        f"CUSTOMER: {qtext}\n\nAPPROVED ANSWER:\n{faq_entry['a']}\n\nAU:"
    )
    result = [None]
    def _call():
        # try only the first (primary) model to avoid 3x latency; resilience via thread timeout
        model = OLLAMA_MODELS[0].strip() if OLLAMA_MODELS else ""
        if not model:
            return
        try:
            body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                               "options": {"temperature": 0.2, "num_predict": 160}}).encode()
            req = urllib.request.Request(OLLAMA_URL + "/api/generate", data=body,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=6) as r:
                resp = json.load(r)
            text = (resp.get("response") or "").strip()
            if not text or len(text) < 10:
                return
            if re.search(r"http://|https://|\\$|price|cost|\$|internal|127\.0\.0\.1|root|vram",
                         text, re.I) and "X-API-Key" not in text:
                return
            result[0] = text
        except Exception:
            return
    import threading
    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=8)
    return result[0]



def log_interaction(qtext, answer_text, escalated):
    """Persist every interaction to disk for audit/feedback (no PII beyond the query)."""
    try:
        import datetime as _dt
        rec = {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
               "query": redact(qtext)[:200], "escalated": escalated,
               "answer_len": len(answer_text or "")}
        buf = []
        if os.path.exists(HISTORY_FILE):
            try:
                buf = json.load(open(HISTORY_FILE))
                if not isinstance(buf, list):
                    buf = []
            except Exception:
                buf = []
        buf.append(rec)
        # keep last 500
        json.dump(buf[-500:], open(HISTORY_FILE, "w"), indent=2)
    except Exception:
        pass

def answer(qtext, history=None):
    """Answer only from approved KB content; all caller-supplied context is untrusted."""
    qtext = str(qtext or "").strip()[:MAX_QUERY_CHARS]
    raw_history = history if isinstance(history, list) else []
    history = [str(item)[:MAX_HISTORY_CHARS] for item in raw_history[-MAX_HISTORY_ITEMS:]]
    if not qtext:
        return escalate("S3", "unknown", "empty_query", "empty query", "-", None, None,
                        history, ["invalid_input"])
    flags = guardrails(qtext)

    # Hard guardrails: never answer, escalate + go quiet.
    if "minor_safety" in flags or "abuse" in flags:
        return escalate("S1", "legal", "abuse_or_minor_safety", qtext[:200], "-", None, None,
                        history + [qtext], flags)
    if "key_leak" in flags:
        redacted = redact(qtext)
        return escalate("S2", "unknown", "leak", redacted[:200], "-", None, "<REDACTED>",
                        history + [qtext], flags)
    if "internal_infra_exposure" in flags:
        return escalate("S2", "unknown", "internal_infra_exposure", qtext[:200], "-", None, None,
                        history + [qtext], flags)

    # Live state (flag files + snapshot)
    st = live_state()
    if st["intel_block"]:
        return escalate("S2", "unknown", "intel_block", "intel block active", "-", None, None,
                        history + [qtext], ["intel_block"] + st["active_flags"])
    if not st["legal_clear"]:
        return escalate("S1", "legal", "legal_flag", "legal flag active", "-", None, None,
                        history + [qtext], ["legal_flag"] + st["open_legal"])

    k, s = score(qtext)
    if s == 0:
        return escalate("S3", "unknown", "low_confidence", qtext[:200], "-", None, None,
                        history + [qtext], flags)

    qmap = {
        "authenticate": "How do I authenticate to the Hardonia Compute API?",
        "403": "I get 403",
        "429": "I get 429",
        "credits": "My credits/quota ran out.",
        "rotate": "I lost my key",
        "delivery": "How do I get my download",
        "refund": "I need a refund.",
        "billing": "billing",
        "status": "Is hardonia.store down?",
        "product": "What is the ComfyUI Workflow Pack?",
    }
    PRODUCT_Q = {
        "ai lab health report": "What is AI Lab Health Report?",
        "comfyui workflow pack": "What is the ComfyUI Workflow Pack?",
        "comfyui workflow subscription": "What is the ComfyUI Workflow Subscription?",
        "ai portrait studio": "What is AI Portrait Studio?",
        "n8n automation kit": "What is the n8n Automation Kit?",
        "local ai ops checklist": "What is Local AI Ops Checklist?",
        "ai lab power bundle": "What is the AI Lab Power Bundle?",
        "autonomous revenue loop": "What is Autonomous Revenue Loop?",
        "hardonia compute api": "What is Hardonia Compute API Access?",
        "private inference": "What is Private Inference Access?",
    }
    target_q = qmap.get(k, "")
    # product questions: pick the specific product mentioned
    if k == "product":
        ql = qtext.lower()
        for slug, q in PRODUCT_Q.items():
            if slug in ql:
                target_q = q
                break
    entry = next((e for e in FAQ_ENTRIES if target_q.lower() in e["q"].lower()), None)
    if not entry:
        return escalate("S3", "unknown", "no_faq_match", qtext[:200], "-", None, None,
                        history + [qtext], flags)

    # capacity-aware override for access issuance
    if k in ("rotate", "authenticate", "403") and not st["capacity_ok"]:
        out = ("AU (Hardonia Auth/Access): key issuance is briefly paused — compute capacity is "
                "currently saturated. Check back shortly; your existing key (if any) still works. "
                "If you're blocked on a delivery, open a GitHub issue with your order ID.")
        log_interaction(qtext, out, False)
        return out

    # Primary: exact FAQ answer (grounded, safe).
    base = entry["a"].replace("\\", "")
    # Generative enhancement (LangChain agent harness preferred; legacy Ollama rephrase
    # as fallback). Both are strictly grounded in the retrieved FAQ/KB context and
    # never invent behavior. Only for auth buckets (avoids latency + drift on
    # catalog/billing answers).
    ans = None
    if k in ("authenticate", "403", "429", "credits", "rotate"):
        try:
            from au_bot_langchain import langchain_answer
            ans = langchain_answer(qtext, history)
        except Exception:
            ans = None
        if not ans:
            ans = generate_grounded(qtext, entry)
    ans = ans if ans else base
    sig = "\n\n— AU (Hardonia Auth/Access)"
    full = ans + sig
    log_interaction(qtext, full, False)
    return full

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", help="customer question (or '-' for stdin)")
    ap.add_argument("--interactive", action="store_true")
    args = ap.parse_args()

    if args.interactive:
        print("AU (Hardonia Auth/Access) — type a question, 'quit' to exit.")
        hist = []
        while True:
            try:
                q = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in ("quit", "exit"):
                break
            if not q:
                continue
            print(answer(q, hist))
            hist.append(q)
        return

    q = args.query
    if q in (None, "-"):
        q = sys.stdin.read().strip()
    if not q:
        print("No query provided.", file=sys.stderr)
        sys.exit(2)
    print(answer(q))

if __name__ == "__main__":
    main()
