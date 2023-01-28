import requests

url = 'https://play.svix.com/in/c_2AjQV9k38x6YQ8Zg9WgQsRj7XnM/'

payload = {"ticker": "BTCUSDT" ,
"side" : 1,
"time": "30m"}



r = requests.post(url, json=payload)

print(r.content)