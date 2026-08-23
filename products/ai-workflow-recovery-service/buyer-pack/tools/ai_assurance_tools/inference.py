from __future__ import annotations

from typing import Any


def assess_launch_config(config: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    listen = str(config.get("listen", "127.0.0.1"))
    if listen in {"0.0.0.0", "::"}:
        blockers.append("public_bind")
    if not config.get("auth"):
        blockers.append("authentication")
    if not config.get("rate_limit"):
        blockers.append("rate_limiting")
    if not config.get("logs"):
        blockers.append("audit_logging")
    if not config.get("backup"):
        warnings.append("No backup/restore verification recorded.")
    if not config.get("gpu_isolation"):
        warnings.append("No GPU isolation evidence recorded.")
    return {
        "schema": "ai-assurance.private-inference-launch/v1",
        "ready": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "boundary": "Assessment only. Do not expose an inference endpoint or issue customer credentials until blockers are resolved and human review approves launch.",
    }
