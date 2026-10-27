import urllib.request, urllib.error, json

req = urllib.request.Request(
    'https://api.groq.com/openai/v1/models',
    headers={'Authorization': 'Bearer your_groq_api_key_here'}
)
try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode())
    for m in data['data']:
        print(m['id'])
except urllib.error.HTTPError as e:
    print(e.read().decode())
