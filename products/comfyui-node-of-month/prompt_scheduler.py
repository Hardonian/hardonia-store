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