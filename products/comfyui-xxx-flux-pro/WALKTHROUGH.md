# WALKTHROUGH — Setup & Usage (PRO)

## 1. Model files (one-time)
| File | Destination |
|---|---|
| flux1_devFP8Kijai11GB.safetensors | models/diffusion_models/ |
| t5xxl_fp8.safetensors | models/clip/ |
| clip_l.safetensors | models/clip/ |
| ae.safetensors | models/vae/ |

## 2. ComfyUI workflow
Open workflows/flux-fantasy-workflow.json in ComfyUI. Node graph is
UNETLoader + DualCLIPLoader + VAELoader + FluxGuidance(3.5) + KSampler.
Verified 81s at 832×832, ~50s at 1024 with fp8 11GB UNet.

## 3. Headless
python3 scripts/generate_flux.py --count N --out ./dir "prompt"
arg list: --count 1-8, --out dir, --prompt "...", --width/--height,
--steps (default 22), --cfg 3.5, --seed.

## 4. Train a character/style LoRA (PRO differentiator)
Follow LORA_RECIPE.md. 12-20 images with consistent captions, run the
ai-toolkit config, sample every 500 steps, choose the checkpoint that holds
identity under novel angles, then drop it in models/loras/ and wire with
LoraLoaderModelOnly in the workflow.

## Expected cost per render
~1-2 min/render on 12GB VRAM at 1024²; batch N via --count.