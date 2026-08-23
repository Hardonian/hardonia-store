from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evidence import build_evidence_report
from .inference import assess_launch_config
from .passport import build_passport, verify_passport
from .provenance import create_sidecar, verify_sidecar
from .recovery import inspect_workflow


def _load_json(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON input must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-assurance-tools")
    sub = parser.add_subparsers(dest="command", required=True)
    evidence = sub.add_parser("evidence")
    evidence.add_argument("snapshot")
    evidence.add_argument("output")
    launch = sub.add_parser("launch-assess")
    launch.add_argument("config")
    launch.add_argument("output")
    passport = sub.add_parser("passport")
    passport.add_argument("workflow")
    passport.add_argument("destination")
    passport.add_argument("--comfyui-version", default="unknown")
    passport_verify = sub.add_parser("passport-verify")
    passport_verify.add_argument("destination")
    provenance = sub.add_parser("provenance")
    provenance.add_argument("asset")
    provenance.add_argument("model")
    provenance.add_argument("workflow_sha256")
    provenance.add_argument("--prompt")
    provenance_verify = sub.add_parser("provenance-verify")
    provenance_verify.add_argument("asset")
    provenance_verify.add_argument("sidecar")
    recovery = sub.add_parser("recovery")
    recovery.add_argument("workflow")
    recovery.add_argument("installed_nodes_json")
    recovery.add_argument("available_models_json")
    args = parser.parse_args(argv)
    if args.command == "evidence":
        Path(args.output).write_text(build_evidence_report(_load_json(args.snapshot)), encoding="utf-8")
        return 0
    if args.command == "launch-assess":
        Path(args.output).write_text(json.dumps(assess_launch_config(_load_json(args.config)), indent=2) + "\n", encoding="utf-8")
        return 0
    if args.command == "passport":
        print(json.dumps(build_passport(Path(args.workflow), Path(args.destination), comfyui_version=args.comfyui_version), indent=2))
        return 0
    if args.command == "passport-verify":
        print(json.dumps(verify_passport(Path(args.destination)), indent=2))
        return 0
    if args.command == "provenance":
        print(create_sidecar(Path(args.asset), model=args.model, workflow_sha256=args.workflow_sha256, prompt=args.prompt))
        return 0
    if args.command == "provenance-verify":
        print(json.dumps(verify_sidecar(Path(args.asset), Path(args.sidecar)), indent=2))
        return 0
    if args.command == "recovery":
        nodes = set(_load_json(args.installed_nodes_json).get("nodes", []))
        models = set(_load_json(args.available_models_json).get("models", []))
        print(json.dumps(inspect_workflow(Path(args.workflow), installed_nodes=nodes, available_models=models), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
