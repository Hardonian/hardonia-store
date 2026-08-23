from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import sha256_file


def create_sidecar(asset: Path, *, model: str, workflow_sha256: str, prompt: str | None = None) -> Path:
    if not asset.is_file():
        raise ValueError("asset must exist")
    payload: dict[str, Any] = {
        "schema": "ai-assurance.provenance-sidecar/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "asset_filename": asset.name,
        "asset_sha256": sha256_file(asset),
        "model_identifier": model,
        "workflow_sha256": workflow_sha256,
        "boundary": "Integrity/provenance record only; not a C2PA manifest, watermark, legal opinion, or compliance certification.",
    }
    if prompt is not None:
        payload["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    sidecar = asset.with_name(asset.name + ".provenance.json")
    sidecar.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sidecar


def verify_sidecar(asset: Path, sidecar: Path) -> dict[str, Any]:
    if not asset.is_file() or not sidecar.is_file():
        return {"valid": False, "reason": "asset_or_sidecar_missing"}
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    actual = sha256_file(asset)
    return {"valid": actual == payload.get("asset_sha256"), "expected_sha256": payload.get("asset_sha256"), "actual_sha256": actual}
