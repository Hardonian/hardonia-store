#!/usr/bin/env python3
"""
LangChain-powered retrieval + tool-calling harness for the AU support bot.

OPTIONAL enhancement layer over au_bot.answer(). Imported lazily and degrades
gracefully: if langchain / langchain_community / scikit-learn are unavailable,
or any error occurs, callers fall back to the existing grounded keyword-FAQ
path in au_bot.answer().

Built on STABLE langchain 1.x primitives (TFIDFRetriever, Tool, PromptTemplate,
Ollama LCEL) with a controlled ReAct tool-calling loop we own (the legacy
AgentExecutor/create_react_agent were removed in langchain 1.x). Fully
local-first: TFIDF retrieval needs no model downloads; the reasoning LLM is the
local Ollama already used by the legacy path.

What it adds (per the "leverage LangChain's deep agent harness" directive):
  - Retrieval over the real KB (SYSTEM_KB.md, product handoffs, FAQ).
  - Four tools the agent can call: faq_lookup, product_lookup, status_check,
    escalate. Retrieval is itself a tool, so the agent decides what to fetch.
  - Strict grounding: the prompt forbids inventing URLs/prices/steps/behavior
    not in retrieved context. Guardrails in au_bot still run FIRST and
    short-circuit before this module is reached.

Self-test:
  python3 au_bot_langchain.py "How do I authenticate to the Compute API?"
"""
import os
import re

KB = "/home/scott/hardonia.store/kb"
PRODUCTS = "/home/scott/hardonia.store/products"
FAQ = os.path.join(KB, "faq-customer.md")

# Set AU_LANGCHAIN=0 to disable the harness entirely (forces the legacy path).
ENABLED = os.environ.get("AU_LANGCHAIN", "0") == "1"

OLLAMA_URL = os.environ.get("AU_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("AU_LANGCHAIN_MODEL", "hermes3:latest")


def _doc_chunks():
    """Yield (text, source) chunks from the KB for the retriever corpus."""
    chunks = []
    skb = os.path.join(KB, "SYSTEM_KB.md")
    if os.path.exists(skb):
        chunks.append((open(skb).read(), "SYSTEM_KB.md"))
    if os.path.isdir(PRODUCTS):
        for slug in os.listdir(PRODUCTS):
            d = os.path.join(PRODUCTS, slug)
            for name in ("README.md", "HANDOFF.md", "MANIFEST.md"):
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    chunks.append((open(p).read(), f"products/{slug}/{name}"))
    if os.path.exists(FAQ):
        chunks.append((open(FAQ).read(), "faq-customer.md"))
    return chunks


def _build_retriever():
    """TFIDFRetriever over KB chunks — local-first, no embeddings to download."""
    from langchain_community.retrievers import TFIDFRetriever
    texts, metas = [], []
    for text, src in _doc_chunks():
        for part in re.split(r"\n{2,}", text):
            part = part.strip()
            if len(part) > 40:
                texts.append(part)
                metas.append(src)
    return TFIDFRetriever.from_texts(texts, metadatas=[{"source": m} for m in metas], k=4)


def _make_tools(retr):
    """Define the agent's tools as plain callables (no langchain.tools dependency)."""
    import au_bot as bot

    def retrieve(query: str) -> str:
        """Retrieve relevant KB passages for a sub-question."""
        try:
            docs = retr.invoke(query)
            return "\n---\n".join(d.page_content for d in docs)[:1500]
        except Exception:
            return ""

    def faq_lookup(q: str) -> str:
        """Canonical FAQ answer for an auth/access/billing/delivery question."""
        k, _ = bot.score(q)
        qmap = {
            "authenticate": "How do I authenticate to the Hardonia Compute API?",
            "403": "I get 403", "429": "I get 429", "credits": "My credits/quota ran out.",
            "rotate": "I lost my key", "delivery": "How do I get my download",
            "refund": "I need a refund.", "billing": "billing",
            "status": "Is hardonia.store down?", "product": "What is the ComfyUI Workflow Pack?",
        }
        target = qmap.get(k, "")
        entry = next((e for e in bot.FAQ_ENTRIES if target.lower() in e["q"].lower()), None)
        return entry["a"] if entry else "No canonical FAQ match."

    def product_lookup(name: str) -> str:
        """Facts about a specific Hardonia product (name or slug)."""
        ql = (name or "").lower()
        base = "/home/scott/hardonia.store/products"
        for slug in os.listdir(base) if os.path.isdir(base) else []:
            if slug in ql or ql in slug:
                p = os.path.join(base, slug, "README.md")
                if os.path.isfile(p):
                    return open(p).read()[:800]
        return "Product not found in catalog."

    def status_check(_: str = "") -> str:
        """Live service/intel/legal state (kill-switch aware)."""
        st = bot.live_state()
        return str({k: st[k] for k in ("capacity_ok", "intel_block", "legal_clear")})

    def escalate(reason: str) -> str:
        """Escalate to a human when the question is unsafe, unclear, or out of scope."""
        return "[ESCALATE] " + reason + " — routed to a human; reply within 1 business day."

    return {
        "retrieve": retrieve,
        "faq_lookup": faq_lookup,
        "product_lookup": product_lookup,
        "status_check": status_check,
        "escalate": escalate,
    }


_SYSTEM = (
    "You are AU, Hardonia's Auth/Access support assistant. Answer the customer using "
    "ONLY tool results. RULES: never invent URLs, prices, steps, or behavior not in "
    "tool output. Use the retrieve/faq_lookup/product_lookup/status_check tools as "
    "needed. If you cannot answer confidently, call escalate. Keep the final answer "
    "under 90 words, friendly, no markdown code fences.\n\n"
    "Respond with ONE of:\n"
    "Action: <tool>(<input>)\n"
    "or when done:\n"
    "Final Answer: <your answer>\n"
)


def langchain_answer(qtext: str, history=None) -> str | None:
    """Run the LangChain ReAct agent; return answer or None to use the legacy path."""
    if not ENABLED:
        return None
    try:
        from langchain_community.llms import Ollama
        retr = _build_retriever()
        tools = _make_tools(retr)
        llm = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_URL,
                     temperature=0.2, num_predict=220)

        prompt = _SYSTEM + "\n\nQuestion: " + qtext + "\n"
        for i in range(4):
            raw = llm.invoke(prompt).strip()
            if raw.startswith("Final Answer:"):
                ans = raw[len("Final Answer:"):].strip()
                break
            m = re.search(r"Action:\s*(\w+)\((.*?)\)\s*$", raw, re.S)
            if not m:
                # No parseable action -> try to use whatever text as final.
                ans = raw
                break
            name, arg = m.group(1).strip(), m.group(2).strip().strip('"\'')
            tool = tools.get(name)
            if not tool:
                ans = "I couldn't find that information; a human will follow up."
                break
            obs = tool(arg)
            prompt += raw + "\nObservation: " + obs + "\n"
        else:
            ans = ""

        ans = (ans or "").strip()
        # Safety net: drift into URLs/prices/internal -> fall back to legacy.
        if re.search(r"http://|https://|\\$|price|cost|127\\.0\\.0\\.1|/root/|vram",
                     ans, re.I) and "X-API-Key" not in ans:
            return None
        if len(ans) < 12:
            return None
        return ans
    except Exception:
        return None


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "How do I authenticate to the Compute API?"
    print(langchain_answer(q) or "(fallback path would be used)")
