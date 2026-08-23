# Agent Ops Concierge — Onboarding Guide

**Welcome!** This guide gets you from purchase to first delivery in 24 hours.

---

## What You Get

| Deliverable | Frequency | Format |
|-------------|-----------|--------|
| 1 Agent Skin | Weekly | `skin.yaml` + `install.sh` + 1 operator skill |
| 1 LoRA Pack | Weekly | `lora.yaml` + preview grid + ComfyUI snippet |
| 1 ComfyUI Workflow | Weekly | `workflow.json` + prompts CSV + model slots |
| 1 Prompt/SOP Pack | Weekly | Markdown + CSV + checklist |
| **Priority Support** | Ongoing | Telegram/Email (4hr SLA business hours) |
| **Factory Monitoring** | 24/7 | We handle failures, retries, updates |

---

## Onboarding Checklist (You Do This Once)

### 1. Reply to Welcome Email
We'll send a Calendly link for a **30-minute onboarding call** (optional but recommended).

### 2. Share Your Preferences
Before or during the call, tell us:

**Agent Skins:**
- Color scheme preference: (cyan/amber/green/violet/monochrome)
- CLI/TUI/GUI target: (Hermes, Open WebUI, custom)
- Any branding elements to include: (logo, tagline, client names)

**LoRAs:**
- Primary model base: (SDXL, Flux, SD 1.5, Pony)
- Style preferences: (photorealistic, anime, line art, cyberpunk, minimal)
- Trigger word style: (descriptive, token-based, natural language)

**Workflows:**
- ComfyUI version: (stable, nightly, custom)
- GPU VRAM: (8GB, 12GB, 16GB, 24GB, 40GB+)
- Preferred samplers/schedulers:
- Model slots you use: (SDXL base, refiner, LoRA, ControlNet, etc.)

**Prompt Packs:**
- Use cases: (portraits, environments, product, text-to-video, upscaling)
- Complexity: (simple 1-liners, structured multi-section, chain-of-thought)
- Output format: (Markdown, CSV, JSON, Notion export)

### 3. Grant Shared Repo Access (Recommended)
We'll create a **private GitHub/Gitea repo** for deliveries:
- You get read access
- We push weekly commits with tagged releases
- You clone/pull whenever convenient
- Includes: `CHANGELOG.md`, `DELIVERY_NOTES.md`, install scripts

**Alternative:** Email delivery with ZIP attachments (less convenient for updates)

---

## Delivery Schedule

| Day | Deliverable |
|-----|-------------|
| **Day 1** | Onboarding call + preferences locked |
| **Day 2** | First batch: 1 skin + 1 LoRA + 1 workflow + 1 prompt pack |
| **Day 9** | Second batch |
| **Day 16** | Third batch |
| **Day 23** | Fourth batch |
| **Monthly** | Renewal check-in (15 min) — adjust preferences, review usage |

---

## How to Use Deliverables

### Agent Skin (`skin.yaml`)
```bash
# One-command install
./install.sh
# Or manual:
cp skin.yaml ~/.config/hermes/skins/
hermes theme apply skin-name
```

### LoRA Pack (`lora.yaml`)
```bash
# Drop into ComfyUI
cp lora.yaml ComfyUI/models/loras/
# Trigger word in lora.yaml: trigger: "neon-line-art-v1"
# Recommended strength in lora.yaml: strength: 0.85
```

### ComfyUI Workflow (`workflow.json`)
```bash
# Drag & drop in ComfyUI UI, or:
cp workflow.json ComfyUI/user/default/workflows/
# Load prompts from prompts.csv
```

### Prompt Pack
```markdown
# Copy prompts from prompts.md or prompts.csv
# CSV columns: category, positive, negative, steps, cfg, sampler, scheduler
```

---

## Support Channels

| Channel | Response Time | Best For |
|---------|---------------|----------|
| **Telegram** (private group) | < 4 hrs business hours | Quick questions, troubleshooting |
| **Email** (concierge@aiautomatedsystems.ca) | < 8 hrs business hours | Detailed issues, billing, renewals |
| **GitHub Issues** (private repo) | < 24 hrs | Bug reports, feature requests |

---

## Factory Monitoring (We Handle This)

You don't need to do anything, but here's what runs behind the scenes:

| Component | Schedule | What We Monitor |
|-----------|----------|-----------------|
| `overnight-agent-skin-factory` | Daily 02:00 UTC | Skin generation, validation, git push |
| `overnight-pack-generator` | Daily 03:00 UTC | LoRA/workflow/prompt generation |
| `dashboard-smoke` | Every 5 min | Service health, disk, GPU, API |
| `ollama-gpu-isolation-guard` | Every 15 min | GPU memory, process isolation |
| `hermes-runtime-guard` | Every 6 hrs | Runtime integrity, symlink protection |

**If something fails:** We get alerted, fix it, and re-run. You only hear about it if it affects your delivery.

---

## Renewal & Adjustments

- **Monthly renewal:** Automatic via Stripe subscription
- **Preference changes:** Anytime via Telegram/email — takes effect next batch
- **Pause/resume:** 1-click in Stripe customer portal
- **Cancel:** Anytime, access continues until period ends

---

## First Delivery Preview

Based on current factory output, your first batch will likely include:

1. **Skin:** "Violet Operator" or "Amber Archive" (cyan/amber/green/violet rotation)
2. **LoRA:** SDXL line-art or Flux photorealistic variant
3. **Workflow:** SDXL txt2img + ControlNet depth + upscale chain
4. **Prompt Pack:** "Agent Ops" or "ComfyUI Workflow" structured prompts

*Exact contents depend on your preferences and factory readiness scores.*

---

## Questions?

Reply to welcome email or message us on Telegram. We're here to make your agent operations sovereign, styled, and stress-free.

**— The Agent Ops Concierge Team**  
AI Automated Systems | aiautomatedsystems.ca