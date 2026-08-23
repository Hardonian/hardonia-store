#!/bin/bash
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
