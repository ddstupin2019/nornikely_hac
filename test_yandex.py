import os
import requests
import json
from my_solution_v1.core.config import settings

def test_endpoint(url_base):
    print(f"\nTesting endpoint: {url_base}")
    url = f"{url_base.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {settings.API_KEY}"
    }
    data = {
        "model": "qwen3.6-35b-a3b/latest",
        "messages": [
            {"role": "user", "content": "Привет, скажи 'ok'"}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Response: {r.json()['choices'][0]['message']['content']}")
        else:
            print(f"Error text: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")

endpoints = [
    "https://llm.api.cloud.yandex.net/foundationModels/v1",
    "https://message.api.cloud.yandex.net/v1",
    "https://message-api.yandexcloud.net/v1"
]

for ep in endpoints:
    test_endpoint(ep)
