# Portrait Generation Runbook

## Input
- Prompt: Studio portrait, soft rim light, clean dark background, 85mm, f/1.8
- Negative: blurry, watermark, text, distorted, low quality
- Seed: 0
- Steps: 30
- CFG: 7
- Batch size: 5

## Execution
- Model: sd_xl_base_1.0.safetensors
- Sampler: euler
- Scheduler: normal
- Denoise: 1.0

## Output
- 5 images saved as ai-portrait-00001_.png through ai-portrait-00005_.png
