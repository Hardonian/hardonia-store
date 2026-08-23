#!/usr/bin/env python3
"""
Sovereign Starter Bundle — Build Script
Auto-generates monthly bundle from latest factory outputs.
Run: python build_bundle.py
Output: bundle.zip + contents_manifest.json + install_all.sh
"""

from __future__ import annotations
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

BASE = Path("/home/scott/hardonia.store/products")
OUTPUT_DIR = BASE / "sovereign-starter-bundle-v2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Source product directories (latest ready versions)
SOURCES = {
    "skins": [
        BASE / "agent-skin-neon-sovereign",
        BASE / "agent-skin-heritage-quiet",
        BASE / "skin-neon-sovereign-20260807",
        BASE / "skin-violet-operator-20260807",
    ],
    "loras": [
        BASE / "lora-neon-line-art",
        BASE / "lora-cyber-chrome-20260807",
    ],
    "prompt_packs": [
        BASE / "prompt-pack-agent-ops",
        BASE / "prompt-pack-comfyui",
        BASE / "sop-incident-response",
        BASE / "checklist-model-launch",
        BASE / "template-rfp-response",
        BASE / "checklist-stripe-setup",
    ],
    "workflows": [
        BASE / "comfyui-workflow-pack",
        BASE / "pack-comfyui-20260807",
    ],
}

def get_latest_ready(sources: list[Path], count: int) -> list[Path]:
    """Pick the most recent 'ready' products from sources."""
    ready = []
    for src in sources:
        pj = src / "product.json"
        if pj.exists():
            try:
                data = json.loads(pj.read_text())
                if data.get("status") == "ready" or data.get("readiness_score", 0) >= 90:
                    ready.append((src, data.get("updated_at", "")))
            except Exception:
                pass
    # Sort by updated_at desc
    ready.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in ready[:count]]

def copy_assets(src: Path, dst: Path, category: str):
    """Copy deliverable assets from source product to bundle."""
    dst.mkdir(parents=True, exist_ok=True)
    
    # Read product.json for metadata
    pj = src / "product.json"
    meta = {}
    if pj.exists():
        meta = json.loads(pj.read_text())
    
    # Copy known asset types
    assets_copied = []
    
    # skin.yaml
    for f in src.glob("skin.yaml"):
        shutil.copy2(f, dst / f"{src.name}_skin.yaml")
        assets_copied.append(f"{src.name}_skin.yaml")
    
    # lora.yaml
    for f in src.glob("lora.yaml"):
        shutil.copy2(f, dst / f"{src.name}_lora.yaml")
        assets_copied.append(f"{src.name}_lora.yaml")
    
    # workflow.json
    for f in src.glob("workflow.json"):
        shutil.copy2(f, dst / f"{src.name}_workflow.json")
        assets_copied.append(f"{src.name}_workflow.json")
    
    # prompts.csv / prompts.md
    for f in src.glob("prompts.*"):
        shutil.copy2(f, dst / f"{src.name}_{f.name}")
        assets_copied.append(f"{src.name}_{f.name}")
    
    # README.md
    for f in src.glob("README.md"):
        shutil.copy2(f, dst / f"{src.name}_README.md")
        assets_copied.append(f"{src.name}_README.md")
    
    # preview.png / cover.png
    for f in src.glob("preview.png"):
        shutil.copy2(f, dst / f"{src.name}_preview.png")
        assets_copied.append(f"{src.name}_preview.png")
    for f in src.glob("cover.png"):
        shutil.copy2(f, dst / f"{src.name}_cover.png")
        assets_copied.append(f"{src.name}_cover.png")
    
    # install.sh if exists
    for f in src.glob("install.sh"):
        shutil.copy2(f, dst / f"{src.name}_install.sh")
        assets_copied.append(f"{src.name}_install.sh")
    
    return {
        "source": src.name,
        "category": category,
        "name": meta.get("name", src.name),
        "version": meta.get("updated_at", datetime.now().isoformat()),
        "assets_copied": assets_copied,
        "stripe_sku": meta.get("stripe_sku", ""),
        "price_id": meta.get("price_id", ""),
    }

def main():
    print("=== Building Sovereign Starter Bundle ===")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    # Select latest ready products
    skins = get_latest_ready(SOURCES["skins"], 3)
    lorass = get_latest_ready(SOURCES["loras"], 1)
    prompts = get_latest_ready(SOURCES["prompt_packs"], 3)
    workflows = get_latest_ready(SOURCES["workflows"], 1)
    
    print(f"Selected skins: {[s.name for s in skins]}")
    print(f"Selected LoRAs: {[s.name for s in lorass]}")
    print(f"Selected prompt packs: {[s.name for s in prompts]}")
    print(f"Selected workflows: {[s.name for s in workflows]}")
    print()
    
    # Build bundle directory
    bundle_dir = OUTPUT_DIR / "bundle"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True)
    
    manifest = {
        "bundle_name": "Sovereign Starter Bundle",
        "version": datetime.now().strftime("%Y.%m.%d"),
        "generated_at": datetime.now().isoformat(),
        "contents": []
    }
    
    # Copy all assets
    for src in skins:
        manifest["contents"].append(copy_assets(src, bundle_dir / "skins", "agent-skin"))
    for src in lorass:
        manifest["contents"].append(copy_assets(src, bundle_dir / "loras", "comfyui-lora"))
    for src in prompts:
        manifest["contents"].append(copy_assets(src, bundle_dir / "prompt-packs", "prompt-pack"))
    for src in workflows:
        manifest["contents"].append(copy_assets(src, bundle_dir / "workflows", "comfyui-workflow"))
    
    # Write manifest
    manifest_path = OUTPUT_DIR / "contents_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest written: {manifest_path}")
    
    # Create install_all.sh
    install_script = OUTPUT_DIR / "install_all.sh"
    install_script.write_text("""#!/bin/bash
# Sovereign Starter Bundle — One-Command Install
# Run from the extracted bundle directory

set -euo pipefail

echo "=== Installing Sovereign Starter Bundle ==="

# Agent Skins
if [[ -d "skins" ]]; then
    echo "Installing agent skins..."
    for skin in skins/*_skin.yaml; do
        [[ -f "$skin" ]] || continue
        name=$(basename "$skin" _skin.yaml)
        cp "$skin" ~/.config/hermes/skins/"$name.yaml"
        echo "  Installed: $name"
    done
fi

# LoRAs
if [[ -d "loras" ]]; then
    echo "Installing LoRAs..."
    for lora in loras/*_lora.yaml; do
        [[ -f "$lora" ]] || continue
        name=$(basename "$lora" _lora.yaml)
        cp "$lora" ~/ComfyUI/models/loras/"$name.yaml"
        echo "  Installed: $name"
    done
fi

# Workflows
if [[ -d "workflows" ]]; then
    echo "Installing ComfyUI workflows..."
    for wf in workflows/*_workflow.json; do
        [[ -f "$wf" ]] || continue
        name=$(basename "$wf" _workflow.json)
        cp "$wf" ~/ComfyUI/user/default/workflows/"$name.json"
        echo "  Installed: $name"
    done
fi

# Prompt packs (copy to a reference directory)
if [[ -d "prompt-packs" ]]; then
    echo "Installing prompt packs..."
    mkdir -p ~/ai-lab/prompt-packs
    cp -r prompt-packs/* ~/ai-lab/prompt-packs/
    echo "  Copied to ~/ai-lab/prompt-packs/"
fi

echo ""
echo "=== Installation Complete ==="
echo "Skins: ~/.config/hermes/skins/"
echo "LoRAs: ~/ComfyUI/models/loras/"
echo "Workflows: ~/ComfyUI/user/default/workflows/"
echo "Prompts: ~/ai-lab/prompt-packs/"
echo ""
echo "Restart Hermes/ComfyUI to pick up new assets."
""")
    install_script.chmod(0o755)
    print(f"Install script: {install_script}")
    
    # Create ZIP
    zip_path = OUTPUT_DIR / f"sovereign-starter-bundle-{datetime.now().strftime('%Y%m%d')}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in bundle_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(bundle_dir.parent)
                zf.write(file, arcname)
        # Add manifest and install script
        zf.write(manifest_path, "contents_manifest.json")
        zf.write(install_script, "install_all.sh")
    
    print(f"Bundle ZIP: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print()
    print("=== Bundle Build Complete ===")

if __name__ == "__main__":
    main()