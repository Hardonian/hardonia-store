from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .passport import _workflow_dependencies


def inspect_workflow(workflow: Path, *, installed_nodes: set[str], available_models: set[str]) -> dict[str, Any]:
    if not workflow.is_file():
        raise ValueError("workflow must exist")
    payload = json.loads(workflow.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "nodes" in payload:
        raise ValueError("workflow must use ComfyUI API JSON format")
    required_nodes, required_models = _workflow_dependencies(payload)
    missing_nodes = sorted(set(required_nodes) - installed_nodes)
    missing_models = sorted(set(required_models) - available_models)
    return {
        "schema": "ai-assurance.workflow-recovery/v1",
        "workflow": workflow.name,
        "ready": not missing_nodes and not missing_models,
        "required_nodes": required_nodes,
        "required_models": required_models,
        "missing_nodes": missing_nodes,
        "missing_models": missing_models,
        "next_actions": [
            "Install only trusted, reviewed custom nodes." if missing_nodes else "Required nodes are present.",
            "Acquire models only from sources with compatible licenses." if missing_models else "Required models are present.",
        ],
    }
