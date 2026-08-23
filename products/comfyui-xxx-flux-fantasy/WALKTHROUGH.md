# WALKTHROUGH — Setup & Usage

## 1. Install the model files (one-time)
Into your ComfyUI `models/` directory:

| File | Destination |
|---|---|
| `flux1_devFP8Kijai11GB.safetensors` | `models/diffusion_models/` (or `models/unet/`) |
| `t5xxl_fp8_e4m3fn.safetensors` | `models/text_encoders/` |
| `clip_l.safetensors` | `models/text_encoders/` |
| `ae.safetensors` | `models/vae/` |

~11 GB VRAM is the comfortable floor for 1024×1024.

## 2. UI workflow (human mode)
1. Copy `workflows/flux-fantasy-workflow.json` → `ComfyUI/user/default/`
2. Start ComfyUI, open the workflow, click **Queue**.
3. Set width/height (1024×1024 default), steps (20), guidance (3.5).

## 3. API workflow (headless)
Copy `workflows/flux-fantasy-workflow-api.json` to a known path, then:

```bash
python3 scripts/generate_flux.py \
  --count 4 \
  --out ./my-art \
  --prompt "fictional adult fantasy portrait, consensual scene, adult model, dark moody lighting, cinematic" \
  --seed 42 --width 1024 --height 1024 --steps 20
```

What you get:
- prompt → ComfyUI → completed PNGs (976 bytes… big ones)
- errors surfaced as real exceptions, exit code non-zero on failure (no fake "success")

## 4. Prompt basics
FLUX uses natural language; no need for SDXL tag soup. Put the quality words at
the END. Negative prompt is optional with FLUX (dmging uses guidance, not CFG).

## 5. Troubleshooting
- "unkd" / Node workflows not loading: `ComfyUI-Manager → Install Missing Nodes`
- OOM: lower `--width`/`--height` to 768, or set `--steps 16`
- Output empty: check `FILE` paths, model names in the JSON match your actual files
- See SUPPORT.md