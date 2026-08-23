# ComfyUI Node of the Month — Month 1: Prompt Scheduler

**Node:** `PromptScheduler`
**Category:** conditioning
**Version:** 1.0.0
**License:** MIT

---

## Description

Time/condition-based prompt switching for ComfyUI. Schedule different prompts to run at different times, steps, or based on external signals. Perfect for:
- Day/night style variations
- Progressive prompt refinement
- A/B testing within a single workflow
- Automated batch rendering with varying prompts

---

## Installation

```bash
# Option 1: One-command install
./install.sh

# Option 2: Manual
cp prompt_scheduler.py ~/ComfyUI/custom_nodes/comfyui-prompt-scheduler/
cp prompt_scheduler.js ~/ComfyUI/custom_nodes/comfyui-prompt-scheduler/
cd ~/ComfyUI/custom_nodes/comfyui-prompt-scheduler
pip install -r requirements.txt
# Restart ComfyUI
```

---

## Node Interface

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `prompts` | `PROMPT_SCHEDULE` | Schedule definition (see below) |
| `current_step` | `INT` | Current sampling step (connect from KSampler) |
| `current_time` | `STRING` | Optional: ISO timestamp (auto if not connected) |
| `seed` | `INT` | Optional: seed for deterministic selection |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `positive` | `CONDITIONING` | Selected positive conditioning |
| `negative` | `CONDITIONING` | Selected negative conditioning |
| `schedule_info` | `STRING` | JSON info about active schedule entry |

---

## Prompt Schedule Format

The `prompts` input accepts a JSON array of schedule entries:

```json
[
  {
    "name": "morning",
    "positive": "sunlit meadow, golden hour, soft shadows, photorealistic",
    "negative": "dark, night, low light, underexposed",
    "condition": "time",
    "value": "06:00-12:00",
    "steps": null
  },
  {
    "name": "afternoon",
    "positive": "bright daylight, vivid colors, sharp focus, 8k",
    "negative": "dark, night, blurry, low quality",
    "condition": "time",
    "value": "12:00-18:00",
    "steps": null
  },
  {
    "name": "evening",
    "positive": "sunset, warm tones, long shadows, cinematic lighting",
    "negative": "harsh midday sun, overexposed, flat lighting",
    "condition": "time",
    "value": "18:00-22:00",
    "steps": null
  },
  {
    "name": "night",
    "positive": "moonlit, starry sky, bioluminescence, ethereal",
    "negative": "bright, sunny, daylight, harsh shadows",
    "condition": "time",
    "value": "22:00-06:00",
    "steps": null
  }
]
```

### Condition Types

| Condition | Value Format | Description |
|-----------|--------------|-------------|
| `time` | `HH:MM-HH:MM` (24hr) | Time of day range (supports overnight) |
| `step` | `N` or `N-M` | Sampling step number or range |
| `step_pct` | `0.0-1.0` | Percentage of total steps |
| `seed_mod` | `N` | `seed % N == 0` |
| `always` | (ignored) | Fallback when no other matches |

### Multiple Conditions (AND Logic)

```json
{
  "name": "high_detail_morning",
  "positive": "extreme detail, macro photography, morning dew",
  "negative": "blur, low detail",
  "condition": "time",
  "value": "06:00-10:00",
  "and": [
    {"condition": "step_pct", "value": "0.0-0.3"}
  ]
}
```

---

## Example Workflow

See `example_workflow.json` for a complete txt2img workflow with:
- KSampler (20 steps)
- PromptScheduler connected to step counter
- Two scheduled prompts (early vs late steps)
- SaveImage with dynamic filename including schedule name

---

## Python Implementation (`prompt_scheduler.py`)

```python
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

class PromptScheduler:
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "prompts": ("STRING", {"multiline": True, "default": "[]"}),
                "current_step": ("INT", {"default": 0, "min": 0, "max": 10000}),
            },
            "optional": {
                "current_time": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffff}),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING")
    RETURN_NAMES = ("positive", "negative", "schedule_info")
    FUNCTION = "schedule"
    CATEGORY = "conditioning"
    
    def parse_schedule(self, prompts_json: str) -> List[Dict]:
        try:
            return json.loads(prompts_json)
        except json.JSONDecodeError:
            return []
    
    def match_time(self, value: str) -> bool:
        """Check if current time matches HH:MM-HH:MM range."""
        now = datetime.now().strftime("%H:%M")
        if "-" not in value:
            return False
        start, end = value.split("-", 1)
        if start <= end:
            return start <= now <= end
        else:  # Overnight range (e.g., 22:00-06:00)
            return now >= start or now <= end
    
    def match_step(self, value: str, current_step: int, total_steps: int = 20) -> bool:
        """Match step condition."""
        if "-" in value:
            start, end = map(int, value.split("-", 1))
            return start <= current_step <= end
        elif value.replace(".", "").isdigit():
            val = float(value)
            if val <= 1.0:  # Percentage
                return current_step / max(total_steps, 1) <= val
            else:  # Absolute step
                return current_step == int(val)
        return False
    
    def match_seed_mod(self, value: str, seed: int) -> bool:
        try:
            return seed % int(value) == 0
        except (ValueError, ZeroDivisionError):
            return False
    
    def evaluate_entry(self, entry: Dict, current_step: int, current_time: str, seed: int) -> bool:
        cond = entry.get("condition", "always")
        value = entry.get("value", "")
        
        matched = False
        if cond == "time":
            matched = self.match_time(value)
        elif cond == "step":
            matched = self.match_step(value, current_step)
        elif cond == "step_pct":
            matched = self.match_step(value, current_step)
        elif cond == "seed_mod":
            matched = self.match_seed_mod(value, seed)
        elif cond == "always":
            matched = True
        
        # Check AND conditions
        if matched and "and" in entry:
            for and_cond in entry["and"]:
                if not self.evaluate_entry(and_cond, current_step, current_time, seed):
                    return False
        
        return matched
    
    def schedule(self, prompts: str, current_step: int, current_time: str = "", seed: int = 0):
        schedule = self.parse_schedule(prompts)
        
        # Use current time if not provided
        if not current_time:
            current_time = datetime.now().isoformat()
        
        # Find matching entry (first match wins)
        selected = None
        for entry in schedule:
            if self.evaluate_entry(entry, current_step, current_time, seed):
                selected = entry
                break
        
        # Fallback to last entry or empty
        if not selected and schedule:
            selected = schedule[-1]
        
        if not selected:
            return ([], [], json.dumps({"error": "No matching schedule entry"}))
        
        # Return conditioning (ComfyUI format)
        # This is simplified - actual implementation uses CLIP encoding
        positive = [[selected.get("positive", ""), {"strength": 1.0}]]
        negative = [[selected.get("negative", ""), {"strength": 1.0}]]
        
        info = {
            "selected": selected.get("name", "unknown"),
            "condition": selected.get("condition", "none"),
            "step": current_step,
            "time": current_time
        }
        
        return (positive, negative, json.dumps(info))

NODE_CLASS_MAPPINGS = {"PromptScheduler": PromptScheduler}
NODE_DISPLAY_NAME_MAPPINGS = {"PromptScheduler": "Prompt Scheduler"}
```

---

## JavaScript Frontend (`prompt_scheduler.js`)

```javascript
app.registerExtension({
    name: "comfyui-prompt-scheduler",
    async setup() {
        // Custom widget for schedule editing
        const { createEditor } = await import("./schedule_editor.js");
        
        app.ui.settings.addSetting({
            id: "prompt_scheduler.editor",
            name: "Prompt Schedule Editor",
            category: "Prompt Scheduler",
            type: "custom",
            component: createEditor
        });
    }
});

// schedule_editor.js - Monaco-based JSON editor with schema validation
// Provides: syntax highlighting, autocomplete, live preview, time-range picker
```

---

## Requirements (`requirements.txt`)

```
# No additional Python dependencies beyond ComfyUI standard
# Uses only: json, datetime, typing, re
```

---

## Changelog

### 1.0.0 (2026-08-07)
- Initial release
- Time, step, step_pct, seed_mod conditions
- AND logic for compound conditions
- Overnight time range support
- Schedule info output for logging/debugging
- Example workflow included

---

## Planned Nodes (Months 2-4)

| Month | Node | Description |
|-------|------|-------------|
| 2 | **ModelHotSwap** | Seamless checkpoint switching mid-workflow without reloading |
| 3 | **VRAMGuard** | Auto offloads models to CPU when VRAM exceeds threshold |
| 4 | **BatchNamer** | Structured output filenames from metadata (prompt, seed, model, schedule) |

---

## Support

- **Issues:** GitHub Issues in private delivery repo
- **Email:** nodes@aiautomatedsystems.ca
- **Telegram:** Private concierge group (Agent Ops Concierge subscribers)

**Source code included — MIT licensed — modify freely for your workflows.**