# Neon Line Art — ComfyUI LoRA Pack

A sovereign SDXL line-art LoRA. One trigger word produces crisp neon contour
illustrations — no checkpoint swap required.

## Install
```
mkdir -p ~/ComfyUI/models/loras
cp neon-line-art.safetensors ~/ComfyUI/models/loras/
```

## Use
Load the LoRA in your SDXL loader with strength ~0.72, then include the
trigger word in the prompt:

```
prompt: neonlineart, a silent city skyline at midnight, contour glow
strength: 0.72
base: SDXL 1.0
```

## What you get
- `lora.yaml` — metadata: base model, trigger word, recommended strength.
- `README.md` — this file.
- `preview.png` — sample render.

## Compatibility
ComfyUI · SDXL 1.0 · Automatic1111 (lora load).
