#!/usr/bin/env python3
"""Headless FLUX.1-dev (uncensored lane) generator via the local ComfyUI REST API.

Drop-in sibling of generate_sovneon.py but for the FLUX graph lane:
UNETLoader (Kijai fp8 11GB) + DualCLIPLoader (t5xxl_fp8 + clip_l) + FluxGuidance
+ VAELoader(ae.safetensors). Uses the ComfyUI /prompt -> /history REST API, so
no UI, no browser; works headless. Errors are surfaced, never masked: a job
that errors raises and the batch exits non-zero.

Usage:
  python3 generate_flux.py --count 4 --out /path [--prompt "…"] [--seed N]
      [--width 1024] [--height 1024] [--steps 20] [--guidance 3.5]
      [--negative "…"] [--model flux1_devFP8Kijai11GB.safetensors]

Requires ComfyUI running on COMFY_URL (default http://127.0.0.1:8188) with
models/ diffmodel + text_encoders + vae/ae.safetensors present.

Exit codes: 0 = all requested images generated; 1 = any failure.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
WORKFLOW = "flux-uncensored-workflow-api.json"


def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:600]
        # surface validation errors unambiguously
        raise RuntimeError(f"[{e.code}] ComfyUI: {body}")


def _get(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{COMFY_URL}{path}", timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:600]
        raise RuntimeError(f"[{e.code}] ComfyUI: {body}")


def load_workflow(kind: str) -> dict:
    """Resolve a workflow JSON: absolute path, ./<kind>.json, or the user
    default dir next to this script."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        kind,
        os.path.join(here, f"{kind}.json"),
        os.path.join(here, "..", "default", f"{kind}.json"),
        f"/home/scott/ai-lab/ComfyUI/user/default/{kind}.json",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return json.load(open(c))
    raise FileNotFoundError(f"workflow {kind!r} not found (tried {candidates})")


def submit(workflow: dict, prompt: str, seed: int, prefix: str, **overrides) -> str:
    wf = json.loads(json.dumps(workflow))  # deep copy
    # FLUX graph node inventory (see flux-uncensored-workflow-api.json):
    # 3=positive CLIPTextEncode, 4=negative, 5=FluxGuidance, 7=KSampler,
    # 10=SaveImage filename_prefix
    wf["3"]["inputs"]["text"] = prompt
    wf["4"]["inputs"]["text"] = overrides.get("negative", "")
    wf["5"]["inputs"]["guidance"] = overrides.get("guidance", 3.5)
    wf["6"]["inputs"]["width"] = overrides.get("width", 1024)
    wf["6"]["inputs"]["height"] = overrides.get("height", 616)
    wf["6"]["inputs"]["batch_size"] = overrides.get("batch_size", 1)
    wf["7"]["inputs"]["seed"] = seed
    wf["7"]["inputs"]["steps"] = overrides.get("steps", 25)
    wf["7"]["inputs"]["sampler_name"] = overrides.get("sampler", "euler")
    wf["7"]["inputs"]["scheduler"] = overrides.get("scheduler", "simple")
    wf["10"]["inputs"]["filename_prefix"] = prefix
    resp = _post("/prompt", {"prompt": wf, "client_id": "hermes-flux"})
    return resp["prompt_id"]


def wait(prompt_id: str, timeout: int = 600, poll: float = 5.0) -> list[str]:
    """Wait for the ComfyUI execution to finish; returns the output filenames or
    raises RuntimeError with the underlying error message. Never pretends
    success on failure."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            hist = _get(f"/history/{prompt_id}")
        except RuntimeError as e:
            last = e
            time.sleep(poll)
            continue
        if hist:
            entry = next(iter(hist.values()))
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                msgs = [str(m[1]) for m in status.get("messages", []) if m[0] == "execution_error"]
                raise RuntimeError(msgs[0] if msgs else "unknown ComfyUI error")
            if (status.get("status_str") == "success") or status.get("completed"):
                files = []
                for node_out in entry.get("outputs", {}).values():
                    for img in node_out.get("images", []):
                        files.append(img["filename"])
                return files
        time.sleep(poll)
    raise TimeoutError(f"timed out after {timeout}s (last: {last})")


def download(fname: str, dest_dir: str) -> str:
    """Fetch an output image from ComfyUI /view into dest_dir; returns the
    local path. Raises on failure so batches never silently miss a file."""
    url = f"{COMFY_URL}/view?filename={urllib.parse.quote(fname)}&type=output&subfolder="
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, fname)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        if not data:
            raise RuntimeError(f"empty download for {fname}")
        return dest
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"[{e.code}] failed to download {fname}: {e.read().decode(errors='replace')[:200]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--out", default="/home/scott/ai-lab/generated/flux_uncensored")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--negative", default="lowres, blurry, text, watermark")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--constant-seed", action="store_true", help="keep seed identical across the batch")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--guidance", type=float, default=3.5)
    ap.add_argument("--prefix", default="flux_client")
    args = ap.parse_args()

    if args.seed < 0:
        import random
        args.seed = random.SystemRandom().randint(0, 2**32 - 1)

    workflow = load_workflow(WORKFLOW.replace(".json", ""))
    os.makedirs(args.out, exist_ok=True)

    ok = 0
    for i in range(args.count):
        seed = args.seed if args.constant_seed else args.seed + i * 7189
        try:
            pid = submit(workflow, args.prompt, seed, args.prefix,
                         negative=args.negative, width=args.width, height=args.height,
                         steps=args.steps, guidance=args.guidance)
            print(f"[{i+1}/{args.count}] submitted seed={seed} prompt_id={pid}")
            files = wait(pid)
            print(f"  -> success: {files}")
            for fn in files:
                local = download(fn, args.out)
                print(f"  -> saved {local}")
            ok += 1
        except Exception as e:
            print(f"  -> FAILED ({type(e).__name__}): {e}", file=sys.stderr)
            ok -= 1
    print(f"DONE: {ok}/{args.count} succeeded")
    return 0 if ok == args.count else 1


if __name__ == "__main__":
    raise SystemExit(main())