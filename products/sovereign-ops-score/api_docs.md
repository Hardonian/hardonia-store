# Sovereign Ops Score API — Developer Documentation

**Base URL:** `https://api.aiautomatedsystems.ca/v1` (or your self-hosted instance)
**Authentication:** Bearer token (API key provided on purchase)
**Rate Limit:** 1000 requests/month (soft limit, contact for increase)
**Content-Type:** `application/json`

---

## Quick Start

```bash
# Set your API key
export SOVEREIGN_OPS_KEY="sk_your_key_here"

# Submit lab metrics for scoring
curl -X POST https://api.aiautomatedsystems.ca/v1/score \
  -H "Authorization: Bearer $SOVEREIGN_OPS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "gpus": [
      {"name": "V100", "util_pct": 45, "mem_used_mib": 8192, "mem_total_mib": 16384, "temp_c": 62},
      {"name": "P40", "util_pct": 12, "mem_used_mib": 2048, "mem_total_mib": 24576, "temp_c": 48}
    ],
    "disk": {"used_gb": 450, "total_gb": 1000, "iops_read": 1200, "iops_write": 800},
    "ollama": {"models_loaded": 3, "queue_depth": 0, "avg_latency_ms": 145},
    "services": [
      {"name": "ollama", "status": "healthy", "uptime_sec": 864000},
      {"name": "comfyui", "status": "healthy", "uptime_sec": 432000},
      {"name": "audit-api", "status": "degraded", "uptime_sec": 12000}
    ],
    "network": {"ingress_mbps": 45, "egress_mbps": 12, "latency_ms": 18}
  }'
```

---

## Endpoints

### `POST /v1/score` — Submit Metrics & Get Score

**Request Body:**
```json
{
  "gpus": [
    {
      "name": "string",           // GPU model name
      "util_pct": "number",       // 0-100
      "mem_used_mib": "integer",
      "mem_total_mib": "integer",
      "temp_c": "number",         // optional
      "power_watts": "number"     // optional
    }
  ],
  "disk": {
    "used_gb": "number",
    "total_gb": "number",
    "iops_read": "number",        // optional
    "iops_write": "number"        // optional
  },
  "ollama": {
    "models_loaded": "integer",
    "queue_depth": "integer",
    "avg_latency_ms": "number",
    "gpu_layers_avg": "number"    // optional
  },
  "services": [
    {
      "name": "string",
      "status": "healthy|degraded|down",
      "uptime_sec": "integer",
      "error_rate_pct": "number"  // optional
    }
  ],
  "network": {
    "ingress_mbps": "number",
    "egress_mbps": "number",
    "latency_ms": "number"        // optional
  },
  "metadata": {                   // optional, stored with result
    "lab_id": "string",
    "region": "string",
    "tags": ["string"]
  }
}
```

**Response (200 OK):**
```json
{
  "score": {
    "overall": 87,
    "breakdown": {
      "revenue_readiness": 92,
      "reliability": 84,
      "security": 78,
      "operability": 91,
      "cost_efficiency": 89
    },
    "trend": {
      "direction": "improving",
      "change_7d": +3,
      "change_30d": +8
    }
  },
  "findings": [
    {
      "category": "security",
      "severity": "medium",
      "title": "Audit API exposed without mTLS",
      "description": "The audit-api service accepts connections without mutual TLS verification.",
      "remediation": "Enable mTLS in Caddy config or restrict to Tailscale interface.",
      "effort_hours": 2
    },
    {
      "category": "reliability",
      "severity": "low",
      "title": "Single P40 GPU underutilized",
      "description": "P40 at 12% utilization while V100 at 45%. Consider model routing.",
      "remediation": "Configure Ollama lanes to route small models to P40.",
      "effort_hours": 1
    }
  ],
  "monetization_plays": [
    {
      "play": "Private Inference API",
      "description": "Expose Ollama via authenticated API with metering",
      "estimated_monthly_revenue_usd": 200,
      "setup_effort_hours": 8,
      "prerequisites": ["API gateway", "Stripe metering", "Auth"]
    },
    {
      "play": "Batch Image Generation",
      "description": "Sell ComfyUI workflow runs via webhook",
      "estimated_monthly_revenue_usd": 500,
      "setup_effort_hours": 16,
      "prerequisites": ["ComfyUI", "Queue worker", "Billing"]
    }
  ],
  "report_url": "https://api.aiautomatedsystems.ca/v1/report/abc123",
  "request_id": "req_abc123def456",
  "timestamp": "2026-08-07T18:30:00Z"
}
```

---

### `GET /v1/report/{report_id}` — Get HTML Report

Returns a full HTML report with charts, findings, and remediation steps.

**Response:** `text/html` (complete report page)

---

### `GET /v1/history` — Get Score History

**Query Parameters:**
- `limit` (default: 30, max: 365)
- `days` (default: 30)

**Response:**
```json
{
  "history": [
    {"date": "2026-08-01", "overall": 84, "revenue": 88, "reliability": 82, "security": 75, "operability": 89, "cost": 86},
    {"date": "2026-08-02", "overall": 85, "revenue": 89, "reliability": 83, "security": 76, "operability": 90, "cost": 87}
  ],
  "summary": {
    "avg_overall_30d": 86.2,
    "trend_30d": "+8",
    "best_category": "operability",
    "worst_category": "security"
  }
}
```

---

### `GET /v1/quota` — Check Usage Quota

**Response:**
```json
{
  "used_this_month": 47,
  "limit": 1000,
  "reset_date": "2026-09-01T00:00:00Z"
}
```

---

## Scoring Methodology

| Category | Weight | Key Factors |
|----------|--------|-------------|
| **Revenue Readiness** | 25% | API metering, billing integration, product catalog, checkout flow |
| **Reliability** | 25% | Service health, uptime, auto-recovery, redundancy, backups |
| **Security** | 20% | mTLS, secrets management, access control, audit logging, network segmentation |
| **Operability** | 15% | Observability, runbooks, deploy automation, GitOps, on-call |
| **Cost Efficiency** | 15% | GPU utilization, right-sizing, spend monitoring, reserved capacity |

**Score Bands:**
- 90-100: **Production Grade** — Ready to sell, minimal risk
- 75-89: **Hardening Needed** — Fix findings before monetizing
- 60-74: **Significant Gaps** — Structured remediation required
- <60: **Not Ready** — Foundational work needed first

---

## Python Client Example

```python
import os
import requests
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GPU:
    name: str
    util_pct: float
    mem_used_mib: int
    mem_total_mib: int
    temp_c: Optional[float] = None
    power_watts: Optional[float] = None

@dataclass
class Disk:
    used_gb: float
    total_gb: float
    iops_read: Optional[int] = None
    iops_write: Optional[int] = None

@dataclass
class Ollama:
    models_loaded: int
    queue_depth: int
    avg_latency_ms: float
    gpu_layers_avg: Optional[float] = None

@dataclass
class Service:
    name: str
    status: str  # healthy|degraded|down
    uptime_sec: int
    error_rate_pct: Optional[float] = None

class SovereignOpsClient:
    def __init__(self, api_key: str, base_url: str = "https://api.aiautomatedsystems.ca/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def score(self, gpus: List[GPU], disk: Disk, ollama: Ollama, 
              services: List[Service], network: dict, metadata: dict = None) -> dict:
        payload = {
            "gpus": [g.__dict__ for g in gpus],
            "disk": disk.__dict__,
            "ollama": ollama.__dict__,
            "services": [s.__dict__ for s in services],
            "network": network,
            "metadata": metadata or {}
        }
        resp = self.session.post(f"{self.base_url}/score", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    def history(self, days: int = 30) -> dict:
        resp = self.session.get(f"{self.base_url}/history", params={"days": days})
        resp.raise_for_status()
        return resp.json()
    
    def quota(self) -> dict:
        resp = self.session.get(f"{self.base_url}/quota")
        resp.raise_for_status()
        return resp.json()

# Usage
if __name__ == "__main__":
    client = SovereignOpsClient(os.getenv("SOVEREIGN_OPS_KEY"))
    
    result = client.score(
        gpus=[
            GPU("V100", 45, 8192, 16384, 62),
            GPU("P40", 12, 2048, 24576, 48)
        ],
        disk=Disk(450, 1000, 1200, 800),
        ollama=Ollama(3, 0, 145),
        services=[
            Service("ollama", "healthy", 864000),
            Service("comfyui", "healthy", 432000),
            Service("audit-api", "degraded", 12000)
        ],
        network={"ingress_mbps": 45, "egress_mbps": 12, "latency_ms": 18},
        metadata={"lab_id": "epyc-main", "region": "ca-toronto"}
    )
    
    print(f"Overall Score: {result['score']['overall']}")
    print(f"Report: {result['report_url']}")
    for finding in result['findings']:
        print(f"  [{finding['severity'].upper()}] {finding['title']}: {finding['remediation']}")
```

---

## Self-Hosted Deployment

If you run your own audit-api (`:8011`), the scoring endpoint is available at:

```
POST http://localhost:8011/api/score
```

Same request/response format. No API key required for local instance (uses `ALLOW_INSECURE_LOCAL_AUTH`).

---

## Support

- **Email:** api-support@aiautomatedsystems.ca
- **Docs:** https://aiautomatedsystems.ca/docs/sovereign-ops-score
- **Status:** https://status.aiautomatedsystems.ca

**Service target:** best-effort availability and support. No contractual uptime, latency, or response-time SLA is included unless a signed customer agreement explicitly defines one.