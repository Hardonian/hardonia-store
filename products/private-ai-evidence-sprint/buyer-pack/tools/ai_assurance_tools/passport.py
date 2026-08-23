from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import sha256_file

MODEL_INPUT_KEYS = {"ckpt_name", "vae_name", "lora_name", "unet_name", "clip_name", "model_name"}


def _workflow_dependencies(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    nodes: set[str] = set()
    models: set[str] = set()
    for node in payload.values():
        if not isinstance(node, dict):
            continue
        class_type = node.get("class_type")
        if isinstance(class_type, str):
            nodes.add(class_type)
        inputs = node.get("inputs", {})
        if isinstance(inputs, dict):
            for key, value in inputs.items():
                if key in MODEL_INPUT_KEYS and isinstance(value, str) and value:
                    models.add(value)
    return sorted(nodes), sorted(models)


def build_passport(workflow: Path, destination: Path, *, comfyui_version: str = "unknown") -> dict[str, Any]:
    workflow = workflow.resolve()
    if not workflow.is_file() or workflow.suffix.lower() != ".json":
        raise ValueError("workflow must be an existing JSON file")
    payload = json.loads(workflow.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "nodes" in payload:
        raise ValueError("workflow must use ComfyUI API JSON format")
    destination.mkdir(parents=True, exist_ok=True)
    bundled_workflow = destination / "workflow.json"
    shutil.copyfile(workflow, bundled_workflow)
    nodes, models = _workflow_dependencies(payload)
    manifest = {
        "schema": "ai-assurance.workflow-passport/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "comfyui_version": comfyui_version,
        "workflow_file": bundled_workflow.name,
        "workflow_sha256": sha256_file(bundled_workflow),
        "required_nodes": nodes,
        "models": models,
        "boundary": "Dependency inventory only. Model weights and private prompts are not copied into this passport.",
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (destination / "README.md").write_text(
        "# Workflow Handoff Passport\n\n"
        "This bundle inventories a ComfyUI API workflow and verifies its byte integrity. "
        "It does not contain model weights, licenses, private prompts, or an execution guarantee.\n",
        encoding="utf-8",
    )
    return manifest


def verify_passport(destination: Path) -> dict[str, Any]:
    manifest_path = destination / "manifest.json"
    if not manifest_path.is_file():
        return {"valid": False, "reason": "manifest_missing"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = destination / str(manifest.get("workflow_file", "workflow.json"))
    if not workflow.is_file():
        return {"valid": False, "reason": "workflow_missing"}
    actual = sha256_file(workflow)
    return {"valid": actual == manifest.get("workflow_sha256"), "expected_sha256": manifest.get("workflow_sha256"), "actual_sha256": actual}
