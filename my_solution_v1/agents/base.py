import requests
from typing import Any
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import SystemMessage, HumanMessage
from my_solution_v1.core.config import settings
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

import openai

def _yandex_qwen_call(prompt_val, temperature: float = 0.3, model_type: str = "qwen") -> str:
    messages = prompt_val.to_messages() if hasattr(prompt_val, 'to_messages') else prompt_val
    system_text = ""
    user_text = ""
    for msg in messages:
        if isinstance(msg, SystemMessage):
            system_text += msg.content + "\n"
        elif isinstance(msg, HumanMessage):
            user_text += msg.content + "\n"
    if model_type == "qwen":
        yandex_cloud_model = "qwen3.6-35b-a3b/latest"
    elif model_type == "deepseek":
        yandex_cloud_model = "deepseek-v4-flash/latest"
        
    import time
    
    # Используем только ключ из настроек
    configs = [
        (settings.API_KEY, settings.FOLDER_ID)
    ]
    
    for conf_idx, (current_key, current_folder) in enumerate(configs):
        client = openai.OpenAI(
            api_key=current_key,
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=current_folder
        )
        
        for attempt in range(5):
            start_time = time.time()
            try:
                response = client.responses.create(
                    model=f"gpt://{current_folder}/{yandex_cloud_model}",
                    temperature=temperature,
                    instructions=system_text.strip(),
                    input=user_text.strip(),
                    max_output_tokens=8000
                )
                out_text = response.output_text
                if not out_text:
                    raise ValueError("Yandex API returned an empty response (Length 0).")
                
                elapsed = time.time() - start_time
                logger.info(f"Yandex LLM ({model_type}) Response received in {elapsed:.2f}s. Length: {len(out_text)}")
                return out_text
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Error calling {model_type} via Yandex API (Key {conf_idx+1}, attempt {attempt+1}/5) after {elapsed:.2f}s: {e}")
                if attempt == 4:
                    raise # Падаем после последней попытки
                time.sleep(3 * (attempt + 1))

def get_llm(temperature: float = 0.3, model_type: str = "qwen"):
    """
    Возвращает LangChain Runnable, который вызывает Yandex Cloud API 
    и может использоваться в LCEL цепочках.
    """
    return RunnableLambda(lambda prompt_val: _yandex_qwen_call(prompt_val, temperature=temperature, model_type=model_type))
