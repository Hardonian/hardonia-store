# Private Inference Access — Usage

## Start Ollama proxy
curl http://localhost:11438/api/generate -d '{"model":"llama3","prompt":"Hello"}'

## Check API key
curl http://localhost:11438/api/tags -H "Authorization: Bearer YOUR_KEY"
