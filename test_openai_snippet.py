import logging
import sys
import urllib3
import requests
import openai

# Enable debug logging for HTTP requests
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

from my_solution_v1.core.config import settings

YANDEX_CLOUD_FOLDER = settings.FOLDER_ID
YANDEX_CLOUD_API_KEY = settings.API_KEY
YANDEX_CLOUD_MODEL = "qwen3.6-35b-a3b/latest"

try:
    client = openai.OpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        base_url="https://ai.api.cloud.yandex.net/v1",
        project=YANDEX_CLOUD_FOLDER
    )
    
    print("Testing chat completions API just in case:")
    try:
        chat_resp = client.chat.completions.create(
            model=f"gpt://{YANDEX_CLOUD_FOLDER}/{YANDEX_CLOUD_MODEL}",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("Chat completions success!", chat_resp.choices[0].message.content)
    except Exception as e:
        print("Chat completions failed:", e)

    print("\nTesting user snippet:")
    response = client.responses.create(
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/{YANDEX_CLOUD_MODEL}",
        temperature=0.3,
        instructions="",
        input="Отнеси отзыв на товар к одной из категорий: positive, neutral, negative. «Здорово! Уровень сервиса на высоте.» Отвечай только одним словом",
        max_output_tokens=500
    )
    print(response.output_text)
except Exception as e:
    print(f"Exception: {e}")
