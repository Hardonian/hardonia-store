from __future__ import annotations

from typing import Any

SENSITIVE = {"secret", "token", "password", "key", "authorization", "cookie"}


def _safe(value: Any, field: str = "") -> Any:
    if any(word in field.lower() for word in SENSITIVE):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(key): _safe(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def build_evidence_report(snapshot: dict[str, Any]) -> str:
    safe = _safe(snapshot)
    services = safe.get("services", []) if isinstance(safe, dict) else []
    lines = [
        "# Private AI Evidence Sprint",
        "",
        "## Evidence boundary",
        "This report summarizes customer-supplied or authorized telemetry. It is not a penetration test, legal opinion, compliance certification, savings guarantee, or continuous monitoring service.",
        "",
        "## Observed services",
    ]
    if isinstance(services, list) and services:
        for service in services:
            if isinstance(service, dict):
                lines.append(f"- {service.get('name', 'unnamed')}: {'healthy' if service.get('healthy') else 'not confirmed'}")
    else:
        lines.append("- No service telemetry supplied.")
    if isinstance(safe, dict) and "disk_free_gb" in safe:
        lines.extend(["", "## Capacity signal", f"- Reported free disk: {safe['disk_free_gb']} GB"])
    lines.extend(["", "## Next actions", "- Confirm data classification and approved workload boundaries.", "- Validate authentication, network exposure, backup recovery, and operator ownership before production use."])
    return "\n".join(lines) + "\n"
