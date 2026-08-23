#!/bin/bash
# ComfyUI Node of the Month — Install Script
# Run from the product directory

set -euo pipefail

NODE_NAME="comfyui-prompt-scheduler"
TARGET_DIR="${HOME}/ComfyUI/custom_nodes/${NODE_NAME}"

echo "=== Installing ${NODE_NAME} ==="
echo "Target: ${TARGET_DIR}"

# Create target directory
mkdir -p "${TARGET_DIR}"

# Copy Python node
cp "$(dirname "$0")/prompt_scheduler.py" "${TARGET_DIR}/"

# Create __init__.py for ComfyUI
cat > "${TARGET_DIR}/__init__.py" <<'EOF'
from .prompt_scheduler import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
EOF

# Create requirements.txt (empty for this node)
cat > "${TARGET_DIR}/requirements.txt" <<'EOF'
# No additional dependencies required
EOF

# Create example workflow
cat > "${TARGET_DIR}/example_workflow.json" <<'EOF'
{
  "3": {
    "inputs": {
      "seed": 123456789,
      "steps": 20,
      "cfg": 7,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["6", 1],
      "latent_image": ["5", 0]
    },
    "class_type": "KSampler",
    "_meta": {"title": "KSampler"}
  },
  "4": {
    "inputs": {
      "ckpt_name": "sdxl_base_1.0.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {"title": "Load Checkpoint"}
  },
  "5": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage",
    "_meta": {"title": "Empty Latent Image"}
  },
  "6": {
    "inputs": {
      "prompts": "[\n  {\n    \"name\": \"early_steps\",\n    \"positive\": \"masterpiece, best quality, detailed landscape, morning light, soft shadows\",\n    \"negative\": \"blur, low quality, dark, night\",\n    \"condition\": \"step_pct\",\n    \"value\": \"0.0-0.5\"\n  },\n  {\n    \"name\": \"late_steps\",\n    \"positive\": \"masterpiece, best quality, detailed landscape, golden hour, warm tones, long shadows\",\n    \"negative\": \"blur, low quality, harsh midday sun\",\n    \"condition\": \"step_pct\",\n    \"value\": \"0.5-1.0\"\n  }\n]",
      "current_step": ["3", 0]
    },
    "class_type": "PromptScheduler",
    "_meta": {"title": "Prompt Scheduler"}
  },
  "7": {
    "inputs": {
      "samples": ["3", 0],
      "vae": ["4", 2]
    },
    "class_type": "VAEDecode",
    "_meta": {"title": "VAE Decode"}
  },
  "8": {
    "inputs": {
      "filename_prefix": "prompt_scheduled_%schedule_name%",
      "images": ["7", 0]
    },
    "class_type": "SaveImage",
    "_meta": {"title": "Save Image"}
  }
}
EOF

echo "Files installed:"
echo "  ${TARGET_DIR}/prompt_scheduler.py"
echo "  ${TARGET_DIR}/__init__.py"
echo "  ${TARGET_DIR}/requirements.txt"
echo "  ${TARGET_DIR}/example_workflow.json"
echo ""

# Install any Python dependencies (none for this node)
if [[ -f "${TARGET_DIR}/requirements.txt" ]]; then
    echo "Checking Python dependencies..."
    pip install -q -r "${TARGET_DIR}/requirements.txt" 2>/dev/null || true
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Restart ComfyUI"
echo "2. Look for 'Prompt Scheduler' in the Conditioning category"
echo "3. Load example_workflow.json to test"
echo ""
echo "Node will appear at: Conditioning → Prompt Scheduler"