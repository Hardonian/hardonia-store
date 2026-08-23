# API Usage Sample

## Create a job
curl -X POST http://localhost:8050/api/v1/jobs \
  -H "Authorization: Bearer [REDACTED]" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello","model":"llama3","provider":"ollama"}'

## Run a job
curl -X POST http://localhost:8050/api/v1/jobs/JOB_ID/run \
  -H "Authorization: Bearer [REDACTED]"

## Download result
curl http://localhost:8050/api/v1/delivery/TOKEN \
  -H "Authorization: Bearer [REDACTED]"
