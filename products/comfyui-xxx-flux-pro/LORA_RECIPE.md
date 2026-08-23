# LoRA Training Recipe — FLUX/SDXL style & character identity (Pro)

Real, validated recipe derived from a successful local run (sovneon-class):
trained an identity LoRA at 1024×1024, flowmatch noise schedule, 2000 steps,
that renders consistently in the FLUX-lane workflows in this pack. Values
below are the ones that worked; tuning notes are flagged inline.

## What you need
- ai-toolkit (github.com/ostris/ai-toolkit) working with CUDA
- A GPU with 20-24GB VRAM; 1024×1024 latents, bf16 training
- 12-20 curated images of your subject/character/style (consent + rights owned)

## Training config (validated values)
```yaml
job: extension
config:
  name: "your-character-lora"
  process:
    - type: sd_trainer
      training_folder: ./out
      device: cuda:0
      trigger_word: "yourchar"
      network: {type: lora, linear: 16, linear_alpha: 16}
      save: {dtype: float16, save_every: 500, max_step_saves_to_keep: 4}
      datasets:
        - folder_path: ./train/yourchar
          caption_ext: txt
          caption_dropout_rate: 0.05
          cache_latents_to_disk: true
          resolution: [1024, 1024]
      train:
        batch_size: 1
        steps: 2000
        gradient_accumulation_steps: 1
        train_unet: true
        train_text_encoder: true
        gradient_checkpointing: true
        noise_scheduler: flowmatch
        optimizer: adamw8bit
        lr: 5e-5
        dtype: bf16
        ema_config: {use_ema: true, ema_decay: 0.99}
      model:
        name_or_path: /models/checkpoints/your-base.safetensors
        is_xl: true
      sample:
        sampler: flowmatch
        sample_every: 500
        width: 1024
        height: 1024
        prompts: ["yourchar, <describe subject the same way every sample>"]
```

## Captioning rule (works)
Each image gets a `.txt` caption: trigger word first, then a one-line plain
description used consistently. Do not vary the subject noun between captions —
that's what the model keys on.

## Validation (do this, don't trust loss)
After training, run the *sample prompts you never trained on* (different pose,
different lighting) through the FLUX/SDXL lane and inspect the render. If the
identity holds with a different pose → the LoRA learned the subject. If it
only reproduces the training angles, raise `steps` to 3000 once. Watch for
"LoRA bleed": background/style confusion means fewer training images or lower
`linear`.

## Pitfalls
- VRAM under 20GB: resolution 768 or grad_accum_steps 2; do not skip
  gradient_checkpointing.
- `push_to_hub` stays false — this is your private lane.
- The trigger word must be included in EVERY inference prompt or the LoRA is
  invisible (it only fires on the token).
- fp8 FLUX unet + LoRA: keep the LoRA at float16 (as saved above).

## Flow
train → sample at 500/1000/1500 → pick the checkpoint that holds identity
under novel angles → place `.safetensors` in ComfyUI models/loras/ → load with
LoraLoaderModelOnly in the workflow → render the batch.