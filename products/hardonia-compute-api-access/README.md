# Hardonia Compute API Access

Private GPU compute, billed by the job.

## What you get
- Pay-by-the-job API with credits
- API key auth + rate limiting
- Ollama chat + ComfyUI workflow execution
- Webhook delivery + admin controls
- SQLite-backed persistence

## How to use
1. Get an API key from the operator
2. Set base URL: the configured service endpoint
3. Create job: `POST /api/v1/jobs`
4. Run job: `POST /api/v1/jobs/{job_id}/run`
5. Download result: `GET /api/v1/delivery/{token}`

## Support
Open an issue or contact the operator.

**Price:** $20 starter / $99 pro / $299 enterprise
