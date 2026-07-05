import json
import concurrent.futures
from openai import OpenAI
import os

# Configuration from analyze_scheme.py
API_KEY = os.getenv("YANDEX_API_KEY", "")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
MODEL_URI = f"gpt://{FOLDER_ID}/deepseek-v4-flash"
BASE_URL = "https://ai.api.cloud.yandex.net/v1"

def get_client():
    return OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

def generate_hypotheses_single(prompt: str, temperature: float) -> list:
    """Runs a single generation call."""
    client = get_client()
    
    # We enforce JSON response format in the system prompt
    system_message = (
        "Ты - генератор инженерных гипотез. "
        "Твой ответ должен содержать ТОЛЬКО валидный JSON-массив объектов гипотез. "
        "Никакого Markdown-форматирования (```json ... ```), просто сырой JSON массив. "
        "Структура каждого объекта:\n"
        '{"название": "...", "описание": "...", "обоснование": "...", '
        '"воздействие": "...", "объект": "...", "параметр": "...", '
        '"направление": "...", "механизм": "...", "что_не_знаем": ["..."]}'
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_URI,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        if not content:
            return []
            
        # Clean potential markdown wrapping
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "гипотезы" in parsed:
            return parsed["гипотезы"]
        elif isinstance(parsed, list):
            return parsed
        return [parsed]
        
    except Exception as e:
        print(f"Error generating with temp {temperature}: {e}")
        return []

def validate_hypothesis(hyp: dict) -> bool:
    """
    Validates the hypothesis structurally.
    Must have specific fields and not be abstract.
    """
    required_fields = ["название", "описание", "воздействие", "объект", "параметр", "направление", "механизм"]
    for field in required_fields:
        if not hyp.get(field) or len(str(hyp.get(field)).strip()) < 3:
            return False
            
    # Simple check for abstraction
    if "улучшить процесс" in hyp.get("описание", "").lower():
        return False
        
    return True

def generate_ensemble(prompt: str, ensemble_configs: list = None) -> list:
    """
    Runs an ensemble of generators in parallel.
    Default ensemble:
    - Temp 0.2 (Conservative)
    - Temp 0.7 (Balanced)
    - Temp 1.0 (Creative)
    """
    if ensemble_configs is None:
        ensemble_configs = [0.2, 0.7, 1.0]
        
    all_hypotheses = []
    
    # Run in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(generate_hypotheses_single, prompt, temp): temp for temp in ensemble_configs}
        for future in concurrent.futures.as_completed(futures):
            temp = futures[future]
            try:
                hypotheses = future.result()
                # Validate
                valid_hyps = [h for h in hypotheses if validate_hypothesis(h)]
                print(f"Generator (Temp {temp}): Generated {len(hypotheses)}, Valid: {len(valid_hyps)}")
                all_hypotheses.extend(valid_hyps)
            except Exception as e:
                print(f"Generator (Temp {temp}) failed: {e}")
                
    return all_hypotheses

if __name__ == "__main__":
    test_prompt = "Как снизить потери никеля в классе -10 мкм с помощью гидроциклонов?"
    results = generate_ensemble(test_prompt, [0.5])
    print(json.dumps(results, ensure_ascii=False, indent=2))
