import requests

url = 'https://play.svix.com/view/c_Q0l1PbA3m6RbYHyiBlaJEVhW0Sl/'

payload = {"ticker": "BTCUSDT" ,"side" : 1,"time": "30m"}



r = requests.post(url, json=payload)

print(r.content)
