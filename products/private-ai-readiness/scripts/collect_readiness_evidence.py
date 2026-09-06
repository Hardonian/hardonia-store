#!/usr/bin/env python3
"""Read-only evidence collector for a Private AI Readiness Audit.

The script does not install packages, start/stop services, alter GPU clocks,
read secrets, upload data, or contact external services. It writes a JSON report
containing only command output needed for an operator review.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def command(args: list[str]) -> dict[str, object]:
    if not shutil.which(args[0]):
        return {"available": False, "command": args, "output": "not installed"}
    try:
        proc = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=20, check=False)
        return {"available": True, "command": args, "exit_code": proc.returncode,
                "output": proc.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"available": True, "command": args, "exit_code": 124, "output": "timed out"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect read-only local AI readiness evidence.")
    parser.add_argument("--out", required=True, type=Path, help="JSON report path")
    args = parser.parse_args()

    report = {
        "schema_version": "1.0",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "host": platform.node(),
        "kernel": platform.release(),
        "privacy_note": "Review before sharing. The collector does not intentionally read secrets, but host and process names can be sensitive.",
        "evidence": {
            "os_release": Path("/etc/os-release").read_text(errors="replace") if Path("/etc/os-release").exists() else "unavailable",
            "gpu": command(["nvidia-smi", "--query-gpu=index,name,driver_version,compute_cap,memory.total,memory.used,temperature.gpu,power.draw,power.limit,utilization.gpu", "--format=csv,noheader"]),
            "gpu_topology": command(["nvidia-smi", "topo", "-m"]),
            "gpu_processes": command(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv,noheader"]),
            "cpu": command(["lscpu"]),
            "memory": command(["free", "-h"]),
            "swap": command(["swapon", "--show"]),
            "docker": command(["docker", "info", "--format", "{{json .Runtimes}} {{.DefaultRuntime}}"]),
            "container_toolkit": command(["nvidia-container-cli", "--version"]),
        },
        "review_prompts": [
            "Confirm every workload has an explicit GPU ownership policy.",
            "Confirm current model licenses and deployment terms independently.",
            "Confirm public ingress, authentication, and webhook verification from the actual deployed configuration.",
            "Treat this evidence as a point-in-time observation, not a compliance certification.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    tmp.write_text(json.dumps(report, indent=2) + "\n")
    tmp.replace(args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
