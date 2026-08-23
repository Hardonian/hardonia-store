# Private AI Readiness Audit — Intake Form
**Complete this before our 90-minute call. Estimated time: 15 minutes.**

---

## 1. Contact & Logistics
- **Name:** 
- **Email:** 
- **Organization:** 
- **Role:** 
- **Preferred call times (timezone + 3 options):**
- **Calendly link (if you have one):** 

---

## 2. Infrastructure Overview
### Hardware
- **GPU count & models:** (e.g., 2× V100, 1× A100-80GB, 4× RTX 4090)
- **CPU/RAM:** 
- **Storage:** (NVMe capacity, HDD capacity, NAS details)
- **Network:** (bandwidth, VLAN segmentation, internet egress)
- **Location:** (on-prem rack, colocation, home lab, cloud hybrid)

### Orchestration
- **Container runtime:** (Docker, Podman, containerd, k3s, Nomad)
- **Orchestrator:** (none, Docker Compose, Kubernetes, HashiCorp Nomad, systemd)
- **Service mesh:** (none, Cilium, Istio, Linkerd, Tailscale)
- **GPU sharing:** (none, MIG, NVIDIA GPU Operator, custom)

### Inference Stack
- **Primary inference server:** (Ollama, vLLM, TGI, llama.cpp, TensorRT-LLM, custom)
- **Model registry:** (local filesystem, Hugging Face Hub private, Harbor, Nexus, S3)
- **Model formats:** (GGUF, safetensors, ONNX, TensorRT engines, custom)
- **API gateway:** (none, Kong, Traefik, Caddy, NGINX, Cloudflare Tunnel)

---

## 3. Data & Model Inventory
### Models in Production
| Model | Format | Size | License | Commercial Use? | Source | Last Updated |
|-------|--------|------|---------|-----------------|--------|--------------|
|       |        |      |         |                 |        |              |

### Data Sources
- **Training data:** (proprietary, public datasets, synthetic, customer data)
- **Inference data:** (user prompts, RAG documents, embeddings, logs)
- **Data classification:** (public, internal, confidential, regulated/PII)
- **Data residency requirements:** (country, region, on-prem only)

---

## 4. Current Security Posture
### Access Control
- [ ] SSH key-only access (no passwords)
- [ ] Tailscale/WireGuard for remote access
- [ ] Hardware tokens (YubiKey) for sudo
- [ ] Separate admin vs operator accounts
- [ ] Audit logging (auditd, syslog, central SIEM)

### Network
- [ ] Ingress blocked by default
- [ ] Egress allowlist for model downloads
- [ ] DNS filtering / sinkholing
- [ ] VLAN separation (mgmt, inference, storage, backup)
- [ ] TLS everywhere (mTLS between services)

### Secrets & Credentials
- [ ] No secrets in code / config files / Docker images
- [ ] Secret manager: (SOPS + age, HashiCorp Vault, 1Password CLI, Doppler, Infisical)
- [ ] API keys rotated: (frequency)
- [ ] Stripe/webhook secrets in env files only

### Monitoring & Logging
- [ ] GPU metrics: (DCGM, Prometheus, custom)
- [ ] Service health: (healthchecks, uptime monitoring)
- [ ] Audit trail: (who did what, when, on which resource)
- [ ] Alerting: (Telegram, Discord, email, PagerDuty, Opsgenie)

---

## 5. Compliance & Governance
### Regulatory Scope
- [ ] GDPR (EU personal data)
- [ ] CCPA/CPRA (California)
- [ ] HIPAA (healthcare)
- [ ] SOC 2 Type II
- [ ] ISO 27001
- [ ] FedRAMP / CMMC
- [ ] Industry-specific: (finance, legal, government, defense)
- [ ] None / Not sure

### Data Processing Agreements
- [ ] DPA with cloud providers
- [ ] DPA with model providers (OpenAI, Anthropic, etc.)
- [ ] DPA with subprocessors
- [ ] Standard contractual clauses for international transfer

### Model Licensing
- [ ] All models checked for commercial-use license
- [ ] Llama 2/3 community license compliance (attribution, 700M user limit)
- [ ] Mistral license compliance
- [ ] Custom model licenses reviewed by legal
- [ ] No "research only" models in production

---

## 6. Operational Maturity
### Deployment
- [ ] Infrastructure as Code: (Terraform, Ansible, Nix, Pulumi, shell scripts)
- [ ] GitOps: (ArgoCD, Flux, manual)
- [ ] Blue/green or canary deployments
- [ ] Rollback tested: (last tested)
- [ ] Disaster recovery RTO/RPO defined

### Observability
- [ ] Structured logging (JSON, Loki, Elasticsearch)
- [ ] Distributed tracing (Jaeger, Tempo, Zipkin)
- [ ] Metrics dashboards (Grafana, custom)
- [ ] SLOs defined (latency, availability, error rate)
- [ ] On-call rotation / runbooks

### Backup & Recovery
- [ ] Model weights backed up: (frequency, location, tested)
- [ ] Config/state backed up: (frequency, location, tested)
- [ ] Database backed up: (frequency, location, tested)
- [ ] Full restore tested: (date)

---

## 7. Pain Points & Goals
### Top 3 Current Pain Points
1. 
2. 
3. 

### Desired Outcomes (rank 1-5)
- [ ] **Sovereignty:** Zero data egress, full control
- [ ] **Compliance:** Audit-ready for [regulation]
- [ ] **Cost Control:** Predictable GPU spend, no surprises
- [ ] **Reliability:** 99.9%+ uptime, auto-recovery
- [ ] **Velocity:** New model deploy in <1 hour
- [ ] **Team Enablement:** Self-service for developers
- [ ] **Monetization:** Sell inference/API access
- [ ] **Other:** 

### Timeline
- **Immediate (0-30 days):** 
- **Near-term (30-90 days):** 
- **Strategic (90-365 days):** 

---

## 8. Budget & Resources
- **Monthly infra budget:** 
- **Team size (engineers/operators):** 
- **Internal security/compliance expertise:** (none, part-time, dedicated)
- **External audit budget:** 

---

## 9. Additional Context
Anything else we should know? (Legacy systems, vendor contracts, upcoming audits, team changes, etc.)

---

**Submit this form** → We'll schedule the call and prepare a tailored audit agenda.