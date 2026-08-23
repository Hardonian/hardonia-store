# FLUX Fantasy — Uncensored Adult-Fantasy ComfyUI Workflow Pack

**Age requirement: you must be 18 or older to purchase, download, or use this pack.**

Real, validated FLUX.1-dev workflows for creating **fictional, consensual,
adult-only fantasy artwork** on your own ComfyUI installation. Everything runs
100% locally; no cloud, no external services, no account.

## What's inside
- `workflows/flux-fantasy-workflow.json` — drag-and-drop UI workflow (ComfyUI editor)
- `workflows/flux-fantasy-workflow-api.json` — headless API workflow (REST)
- `scripts/generate_flux.py` — headless generator: prompt → PNG, with real error surfacing and retries
- `prompts/prompt-presets.txt` — 10 fictional-fantasy presets with consensual framing
- Buyer docs: `AGE_VERIFICATION.md`, `LEGAL_SAFEGUARDS.md`, `WALKTHROUGH.md`, `SUPPORT.md`, `LICENSE.md`, `PREVIEW.md`, `CHANGELOG.md`, `MANIFEST.json`

## Requirements
- ComfyUI running locally (any recent build)
- Model files in ComfyUI models dirs:
  - `diffusion_models/flux1_devFP8Kijai11GB.safetensors` (Kijai fp8)
  - `text_encoders/t5xxl_fp8_e4m3fn.safetensors` and `text_encoders/clip_l.safetensors`
  - `vae/ae.safetensors`
- ~11GB VRAM for fp8 (RTX 3060 12GB / V100 / P40 verified)

## Quick start
1. Place `workflows/flux-fantasy-workflow.json` into `ComfyUI/user/default/` and open it in the UI.
2. Type a fictional fantasy prompt, click Queue, done.
3. Or run headless:
   ```bash
   python3 scripts/generate_flux.py --count 4 --out ./my-art \
     --prompt "fictional fantasy portrait, consensual scene, adult model, professional lighting" \
     --width 1024 --height 1024 --steps 20
   ```
4. Images land in `ComfyUI/output/` and a copy in `./my-art/`.

See `WALKTHROUGH.md` for the full setup and `AGE_VERIFICATION.md` + `LEGAL_SAFEGUARDS.md` for rules of use.