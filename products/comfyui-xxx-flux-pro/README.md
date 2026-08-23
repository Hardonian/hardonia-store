# FLUX Fantasy PRO — Uncensored Workflows + LoRA Recipe

**18+ only. Fictional, consensual, adult creative content.**

The Pro tier of the FLUX Fantasy lane: everything in the base pack, plus a
validated local LoRA training recipe (character/style identity), 30 prompt
presets, and the same hardened headless generator.

## Contents
- workflows/flux-fantasy-workflow.json — drag-and-drop UI workflow
- workflows/flux-fantasy-workflow-api.json — headless API workflow
- scripts/generate_flux.py — prompt → PNG generator (verified)
- prompts/prompt-presets.txt — 30 presets (6 shared + 24 PRO)
- LORA_RECIPE.md — real LoRA training config + tuning guide
- buyer-docs/ — age verification, legal safeguards, license, walkthrough

## Model files you bring (free, from Black Forest Labs / mirrors)
See WALKTHROUGH.md for the exact filenames.

## Quick start
1. Drop `flux-fantasy-workflow.json` into ComfyUI/user/default/
2. Load the FLUX.1-dev fp8 weights (walkthrough lists them)
3. Queue a prompt, or headless:
   python3 scripts/generate_lora_style.py --count 4 --out ./art "your prompt"