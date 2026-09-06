# Private AI Readiness Audit

A fixed-scope, evidence-led review for teams operating private or self-hosted AI workloads.

Status: draft service offer. This package is a delivery toolkit; it is not a compliance certification and it does not make a system secure by itself.

What the audit covers

- GPU, VRAM, driver, container-runtime, and workload ownership evidence
- local model-serving routing and service-health review
- data-residency and exposure-boundary review
- model-license inventory questions for the client to verify
- ranked remediation roadmap with owner, effort, dependency, and acceptance criteria

Delivery scope

1. Client completes `intake_form.md`.
2. Client runs the read-only collector in `scripts/` on the agreed host.
3. A 90-minute working session reviews the evidence and architecture.
4. Client receives a completed report based on `report_template.md` within the agreed delivery window.

Privacy boundary

The supplied collector does not read credentials, configuration files, customer data, prompts, model weights, or upload anything. Review its JSON output before sharing because hostnames, process names, and package versions can still be sensitive.

Run the collector

```bash
python3 scripts/collect_readiness_evidence.py --out private-ai-readiness-evidence.json
```

See `WALKTHROUGH.md` for the full procedure, `PREVIEW.md` for an example of the report structure, and `SUPPORT.md` for support boundaries.