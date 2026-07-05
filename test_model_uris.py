import requests
from my_solution_v1.core.config import settings

def test_uri(uri):
    print(f"\nTesting: {uri}")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {settings.API_KEY}"
    }
    data = {
        "modelUri": uri,
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 100
        },
        "messages": [
            {"role": "user", "text": "test"}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("SUCCESS")
        else:
            print(r.text)
    except Exception as e:
        print(f"Exception: {e}")

uris = [
    f"gpt://{settings.FOLDER_ID}/qwen3.6-35b-a3b/latest",
    "gpt://qwen3.6-35b-a3b/latest",
    "ds://qwen3.6-35b-a3b/latest",
    f"ds://{settings.FOLDER_ID}/qwen3.6-35b-a3b/latest",
    "qwen3.6-35b-a3b/latest",
    f"yandexgpt://{settings.FOLDER_ID}/qwen3.6-35b-a3b/latest"
]

for u in uris:
    test_uri(u)
