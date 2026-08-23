# Runbook — Product Catalog & Packaging Ownership

Source of truth for what Hardonia sells. Update this FIRST when a product changes; the AU bot and
FAQ read from it.

## Catalog (real slugs)
| slug | title | type | deliverable | owner |
|------|-------|------|-------------|-------|
| private-inference-access | Private Inference Access | access | API key + endpoint docs | Scott |
| hardonia-compute-api-access | Hardonia Compute API Access | API key | key + api-usage.md | Scott |
| ai-lab-power-bundle | AI Lab Power Bundle | bundle | multi-pack zip | Scott |
| n8n-automation-kit | n8n Automation Kit | pack | n8n JSON workflows | Scott |
| local-ai-ops-checklist | Local AI Ops Checklist | pack | checklist + systemd templates | Scott |
| comfyui-workflow-pack | ComfyUI Workflow Pack | pack | workflows + prompts | Scott |
| comfyui-workflow-subscription | ComfyUI Workflow Subscription | subscription | monthly workflows | Scott |
| ai-portrait-studio | AI Portrait Studio | pack | local portrait gen pack | Scott |
| ai-lab-health-report | AI Lab Health Report | report | generated report | Scott |
| autonomous-revenue-loop | Autonomous Revenue Loop | playbook | playbook + skills | Scott |
| legal | Legal | reference | licenses/terms | Scott |

## Each product folder contains
README.md · WALKTHROUGH.md · DELIVERABLE-SNAPSHOT.md · PREVIEW.md · SUPPORT.md · product.json ·
LICENSE · CHANGELOG · deliverables/ · assets/ · templates/ (some).

## Packaging ownership rule
Every product has exactly one owner (currently all Scott). As we hire, assign owner in this table
and in `product.json` ("owner" field). Owner is accountable for: SUPPORT.md accuracy, delivery,
and FAQ entry.

## Adding a product
1. `mkdir products/<slug>`; copy structure from an existing pack.
2. Write product.json (title, type, price, owner).
3. Add row here + FAQ entry in `faq-customer.md`.
4. If access/subscription: register delivery + key path in `runbooks/storefront.md`.
5. Run `tools/kb-lint.sh` — must pass (no unresolved template tokens remaining).

## Deprecation
If `feeds/snapshot.json` financial shows cost > revenue for 2 months → flag Scott → move to
`products/legal/DEPRECATED/` or mark `product.json: active=false`. Keep FAQ honest (say retired).
