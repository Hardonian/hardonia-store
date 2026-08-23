#!/usr/bin/env bash
# Local AI Lab Audit — report generator.
# Produces the customer deliverable for local-ai-lab-audit:
#   ranked findings + repair list + APVA ROI estimate.
# Safe, read-only against the live lab; writes only the report file.
set -Eeuo pipefail
OUT="${1:-$HOME/ai-lab/audits/local-ai-lab-audit-report.md}"
mkdir -p "$(dirname "$OUT")"
{
  echo "# Local AI Lab Audit"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## 1. Lab inventory"
  echo
  # GPU cards
  if command -v nvidia-smi >/dev/null 2>&1; then
    echo "### GPU (nvidia-smi)"
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null \
      | sed 's/^/ - /' || echo " - nvidia-smi failed"
  fi
  echo
  echo "### Ollama / model endpoints"
  for p in 11434 11435 11436 11437; do
    if curl -s -m2 -o /dev/null "http://127.0.0.1:$p/api/tags" 2>/dev/null; then
      echo " - port $p: responding"
    else
      echo " - port $p: no response"
    fi
  done
  echo
  echo "### Service ports"
  for p in 8011 8012 8020 8188 8080 3002; do
    CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$p/" 2>/dev/null || echo dead)
    printf ' - %s HTTP %s\n' "$p" "$CODE"
  done
  echo
  echo "### Disk / storage"
  df -h / /home 2>/dev/null | awk 'NR==1{print " - "$0} NR>1{print " - "$0}'
  echo
  echo "## 2. Findings (ranked)"
  echo
  echo " - Filled from the operator's on-site pass (the generator snapshots lab state)."
  echo
  echo "## 3. Repair plan"
  echo
  echo " - Ranked fixes with owner + effort + estimated ROI (filled by operator)."
  echo
  echo "## 4. APVA ROI estimate"
  echo
  echo " - Dashboard + monitoring setup notes (optional add-on)."
} > "$OUT"
echo "Wrote $OUT"