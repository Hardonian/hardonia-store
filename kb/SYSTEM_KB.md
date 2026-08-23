# Hardonia AI-Lab — System Knowledge Base

> Living document. Generated 2026-07-12. Machine-readable companion: `system-inventory.json`.
> Scope: all apps, services, workers, bots, cron jobs, realtime routes, data flows, and operations.
> Secrets are redacted as `[REDACTED]`. Never paste live keys into this file.

---

## 1. Architecture at a glance

```
                          aiautomatedsystems.ca
        ┌─────────────────────────────────────────────────────┐
        │  HX370 (orchestration)    EPYC GPU server   edge     │
        └─────────────────────────────────────────────────────┘
   caddy(:80/443) ─► storefront(:8020)  command-center(:8000)
                                │
        checkout(:8012) ◄── Stripe ──► revenue-os.db
              │ HMAC-signed fanout
        workforce-control-plane(:8040) ── queue ──► executor ──► delivery-executor
              │
        compute-api(:8050) ◄── X-API-Key ──► GPU jobs (ollama-router :11438, comfyui :8188)
              │ metered usage_logs
        platform-control-plane(:8070) ◄── service_registry probes ALL services
```

**Trust boundaries**
- Public: storefront, caddy, n8n(:5678), open-webui(:3002)
- Internal (localhost): command-center, checkout, compute, workforce, audit, platform-control, ollama*, redis, node_exporter, vramd
- Cross-service calls are HMAC-signed (`signed_requests`); verification opt-in via `PLATFORM_ENFORCE_SIGNING=1`

---

## 2. Services (apps) — ports, purpose, auth

| Service | Port | PID | Purpose | Auth | Health |
|---|---|---|---|---|---|
| ai-lab-command-center | 8000 | 1293406 | Unified dashboard / operator console / self-healing orchestrator | JWT or shared dashboard token (`require_auth`) | `/health /live /ready` |
| hardonia-checkout-api | 8012 | 4173010 | Stripe checkout + webhook → purchases → workforce fanout | Operator key (revenue); Stripe sig on webhooks | `/health /live /ready` |
| hardonia-compute-api | 8050 | 4173121 | Paid GPU inference / image-gen; prepaid credits + metered usage | `X-API-Key`; admin `X-Admin-Key` | `/health /live /ready` |
| workforce-control-plane | 8040 | 11123 | Queue/status/complete + webhook ingest (HMAC opt-in) | `X-Workforce-Key` non-localhost; HMAC | `/health` |
| ai-lab-audit-api | 8011 | 10557 | Audit/snapshot/doctor API | internal | `/health` |
| storefront | 8020 | 10530 | Store, blog, landings, leads, Gumroad CTA | public + `STOREFRONT_DOWNLOAD_SECRET` | `/health` |
| platform-control-plane | 8070 | 10038 | `/platform/services /status /contracts /slos /actions` | HMAC or control admin token | `/platform/status` |
| stripe-webhook | — | — | Stripe webhook receiver | Stripe sig | internal |
| comfyui | 8188 | 42141 | Image diffusion | none (localhost) | `/system_stats` |
| open-webui | 3002 | — | Chat UI over Ollama | ui | `/api/health` |
| n8n | 5678 | 17171 | Workflow automation ⚠️ **creds compromised — rotate** | basic (rotate) | `/` |
| ollama-router | 11438 | 10538 | Model router across GPUs | none | `/api/tags` |
| ollama-v100 / p40 / 3060 | 11434 / — / — | — | Per-GPU Ollama | none | `/api/tags` |
| redis | 6380 | — | Cache/rate-limit ⚠️ **requires auth, apps use empty pw → fail-soft** | required (misconfig) | RESP ping |
| node_exporter | 9100 | 10278 | Prometheus host metrics | none | `/metrics` |
| caddy | 80/443 | — | Reverse proxy / TLS | n/a | `/` |
| vramd | 8001 | — | VRAM dashboard | internal | `/` |

**Repos:** `ai-lab-command-center`, `hardonia-checkout-api`, `hardonia-compute-api`, `storefront` (push `main`); `ai-lab` (push `gh-pages`, contains `workforce-control-plane`, `platform/`, `scripts/`, `agents/`).

---

## 3. Workers (background services)

| Worker | Timer | Interval | Role |
|---|---|---|---|
| workforce-executor | workforce-executor.{s,t} | 60s | Pops queue, runs mapped command, records completion |
| ai-agent-orchestrator | ai-agent-orchestrator.{s,t} | — | Spawns/monitors sub-agents; self-heal loop |
| platform-recovery | platform-recovery.timer | 5m | Lease reclaim, poison quarantine, bounded restart, reconcile |
| platform-delivery | platform-delivery.timer | 10m | Idempotent bundle assembly + DLQ |
| delivery-executor | delivery-executor.timer | 15m | On purchase: customize bundle → `store/sent/<order>/` |
| revenue-os-sync | revenue-os-sync.timer | 30m | Sync events/purchases → snapshot |
| autonomous-hour | autonomous-hour.timer | daily 04:00 | Self-driving plan: priority sort + execute safe tasks |
| profit-operator | profit-operator.timer | daily 06:05 | Generate ≤120-min human agenda |
| suite-verify | suite-verify.timer | daily 03:30 | Run all test suites + qa_harness |
| revenue-watch | revenue-watch.timer | hourly | funnel-watch + conversion-auditor + approval-queue |
| idle-gpu-watch | idle-gpu-watch.timer | 30m | Flag idle GPU for monetization |
| gumroad-publish | gumroad-publish.timer | daily 14:00 | Publish queued products (10/24h cap) |
| security-scan | security-scan.timer | — | Secret/expiry/dep drift |
| kb-ecosystem-update | kb-ecosystem-update.timer | 30m | Ingest intel/analytics/compute → snapshot.json |
| platform-contracts-refresh | platform-contracts-refresh.timer | 6h | Refresh contracts/manifest.json |

---

## 4. Bots

- **au-bot (Auth/Access Unit)** — `hardonia.store/kb/tools/au_bot.py`; served by `au-bot-server.service` (active). Answers auth/access questions grounded in real `auth.py` (`X-API-Key`, 401/403/429 lockout, `ApiKeyCreate`). Reads `kb/feeds/snapshot.json`.
- **agent-orchestrator** — `ai-lab/agents/orchestrator/agent-orchestrator.py`; autonomous agent loop.
- **hermes-gateway** — Hermes operator gateway (active).

---

## 5. Cron jobs (timers) by function

- **Revenue:** revenue-os-sync, revenue-watch, revenue-dashboard, revenue-pnl, daily-pnl, morning-profit-brief, profit-operator, gumroad-publish, money-factory, money-lane, financial-tracker
- **AI-lab health:** ai-doctor, ai-heal, ai-lab-watchdog, ai-lab-cleanup, ai-disk-pressure, ai-metrics, ai-service-data-truth, ai-asset-truth, hardware-os-truth, service-watchdog, workforce-self-heal, auto-remediation, config-drift, dep-drift-guard, cuda-x-doctor, comfyui-symlink-check
- **Growth:** seo-pages, seo-auto-submit, seo-rank-tracker, content-generator, content-queue-review, newsletter-draft, lead-scoring, lead-nurture, lead-connector, abandoned-checkout, opportunity-ranker, competitor-monitor, readme-backlinks, social-poster, social-content
- **Platform:** suite-verify, platform-recovery, platform-delivery, platform-contracts-refresh, cross-layer-verify, service-dependency, kb-ci, knowledge-base, sandbox-reconcile
- **Workforce:** workforce-executor, ai-agent-orchestrator, autonomous-hour, autonomous-workforce-daily/weekly/monthly, task-priority-sort, self-driving-plan, proactive-loop
- **Security:** security-scan, secret-expiry, backup-drill, backup-restore-test, backup-revenue-os, incident-postmortem, log-watcher, au-watchdog
- **Intel:** kb-ecosystem-update, analytics-summary, ops-status, lab-monitor, lab-memory, ecosystem-gap-audit, night-skill-scout, capacity-planner

(~130 timers total; see `system-inventory.json` for the full list.)

---

## 6. Realtime / HTTP routes (key surfaces)

**checkout-api (:8012)** — `/health /live /ready /metrics`, `/api/v1/products`, `/api/v1/checkout/session`, `/api/v1/checkout/subscription`, `/api/v1/webhooks/stripe`, `/api/v1/refund`, `/api/v1/affiliate/*`, `/api/v1/coupon/validate`, `/api/v1/revenue/*` (operator-key), `/api/v1/validate`
**compute-api (:8050)** — `/health /live /ready /metrics`, `/v1/models`, `/v1/gpu`, `/api/v1/jobs` (+`/{id}`, `/{id}/run`), `/api/v1/delivery/request`, `/api/v1/delivery/{token}`, `/api/v1/credits/*`, `/api/v1/webhooks/stripe`, `/api/v1/usage`, `/admin/billing/usage-report`, `/admin/keys`, `/api/v1/metering/gpu`
**storefront (:8020)** — `/`, `/p/{slug}`, `/pricing`, `/blog`, `/blog/rss.xml`, `/sitemap.xml`, `/api/products`, `/api/ask`, `/api/lead`, `/api/leads`, `/api/contact`, `/api/subscribe`, `/api/track`, `/api/gpu-status`, `/api/analytics`, `/metrics/funnel`, `/api/privacy/erase`
**command-center (:8000)** — `/health`, `/api/revenue/status` (token), `/api/disk/rescue`, `/gpu-status`, `/ollama-status`, `/scan`, `/api/v1/webhooks/*`
**workforce-control-plane (:8040)** — `/health`, `/workforce/queue`, `/workforce/complete`, `/workforce/status`, `/workforce/webhooks/{workflow}`
**platform-control-plane (:8070)** — `/platform/services`, `/platform/status`, `/platform/contracts`, `/platform/slos`, `/platform/actions/log`, `POST /platform/actions/<name>` (authed, audited)

---

## 7. Data flows

1. **Purchase:** Stripe → checkout-api `/webhooks/stripe` (sig verified) → `revenue-os.purchases` → workforce fanout (**HMAC-signed**) → `:8040/workforce/webhooks/{workflow}` → queue → executor → delivery-executor (`customize_bundle`) → `store/sent/<order>/`
2. **Usage metering:** compute-api job complete → `db.log_usage(job_id)` → `usage_logs` → `/admin/billing/usage-report` (admin). Future: Stripe `usage_record`.
3. **Intel:** kb-ecosystem-update ingests intel/analytics/compute → `kb/feeds/snapshot.json` → au-bot reads it.
4. **Platform control:** service_registry probes all services → `:8070/platform/status`; recovery_watchdog on timer.

---

## 8. Operations runbooks

**Restart a service (user-space):**
```
systemctl --user restart <name>.service
```
**Check health:** `curl -s http://127.0.0.1:<port>/health` (or `/live` `/ready` `/platform/status`).
**Queue depth:** `curl -s http://127.0.0.1:8040/workforce/status`.
**Platform status:** `curl -s http://127.0.0.1:8070/platform/status`.
**Contracts:** `curl -s http://127.0.0.1:8070/platform/contracts` (after control-plane restart picks up new code).
**Run all tests:** `cd ai-lab/platform && python3 tests/test_platform.py && python3 tests/test_resilience.py && python3 tests/test_contracts.py && python3 tests/contract_test_checkout_delivery.py && python3 tests/chaos_harness.py && python3 tests/test_controlplane_auth.py`
**Pen/stress:** `python3 ai-lab/scripts/bin/qa_harness.py` (localhost-only).
**Cross-layer verify:** `python3 ai-lab/productization/gumroad-listings/cross_layer_verify.py`.

**Known blockers (external):**
- Domain TLS down (`aiautomatedsystems.ca`) — Cloudflare token rejected 9109; needs sudo/Caddy or new token. Blocks external traffic to SEO/blog/compute.
- Gumroad publish capped 10 creates/24h (timer @14:00).
- **n8n password compromised** (`/home/scott/.local/etc/n8n.env` plaintext) — rotate + move to secret store.
- Redis `:6380` requires auth but apps use empty pw → rate-limiter fail-soft (no 500); creds not injected.
- Sudo needed for: Caddy edit/reload, Prometheus/Grafana, pen-test tooling, AV/rootkit (clamav/rkhunter/lynis).

**Secrets policy:** Never expose Stripe keys, Redis auth, n8n pw, Gumroad token, API keys, PATs. Redact as `[REDACTED]`. Workforce control plane is localhost-only.

---

## 9. Platform maturity (what was built)

- Service registry + control plane (`:8070`) with health/version/contracts/SLOs + authed safe-actions + audit.
- Signed inter-service auth (emit **and** verify — full loop; checkout/relay sign, control-plane verifies).
- Shared resilience (`platform/resilience.py`): correlation-id, error envelopes, `/live`+`/ready` probes, graceful shutdown.
- Consumer-driven contract test (caught real delivery schema bug), isolated chaos harness, metered usage logging.
- Startup brownout fix (bounded Ollama health), 65 command-center tests (was 46 + 19 hanging).
