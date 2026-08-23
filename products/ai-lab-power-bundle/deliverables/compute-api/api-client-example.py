import requests

base_url = 'http://localhost:8050'
headers = {'Authorization': 'Bearer YOUR_API_KEY'}

# Create job
resp = requests.post(f'{base_url}/api/v1/jobs', json={
    'prompt': 'Hello from AI Lab Power Bundle',
    'model': 'llama3',
    'provider': 'ollama'
}, headers=headers)
print(resp.json())
