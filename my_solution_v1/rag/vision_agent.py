import base64
import requests
from my_solution_v1.core.config import settings
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def describe_image(image_path: str) -> str:
    """
    Agent 0: Vision Agent. Uses Yandex Qwen3.6 (or fallback Vision model) 
    to analyze images (schemes, diagrams) and return a text description.
    """
    logger.info(f"Analyzing image: {image_path}")
    try:
        base64_image = encode_image(image_path)
        
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {settings.API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Yandex Vision model URI format, pointing to qwen
        model_uri = f"vis://{settings.FOLDER_ID}/qwen3.6"
        
        payload = {
            "modelUri": model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": 1000
            },
            "messages": [
                {
                    "role": "user",
                    "text": "Опиши подробно, что изображено на этой схеме или диаграмме. Извлеки всю полезную техническую информацию."
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result_data = response.json()
        content = result_data.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
        
        return f"[ОПИСАНИЕ ИЗОБРАЖЕНИЯ {image_path}]:\n{content}"
        
    except Exception as e:
        logger.error(f"Vision agent failed to describe image: {e}")
        return f"[ОШИБКА АНАЛИЗА ИЗОБРАЖЕНИЯ {image_path}]"
