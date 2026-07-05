import json
from b6_generate import get_client, MODEL_URI
from b3_embed_retrieve import retrieve

def score_novelty(hypothesis: dict) -> dict:
    """
    Evaluates novelty by retrieving similar solutions and asking LLM.
    Returns: {"score": float (0, 0.5, 1.0), "аналог": "описание аналога"}
    """
    client = get_client()
    
    # Retrieve related knowledge based on the action
    action = hypothesis.get("описание", "")
    chunks = retrieve(action, k=3)
    
    context_text = "\n".join([f"Источник {i+1}: {c.get('текст')}" for i, c in enumerate(chunks)])
    
    prompt = (
        f"Гипотеза: {action}\n\n"
        f"Известные решения (из базы):\n{context_text}\n\n"
        "Оцени новизну гипотезы по шкале:\n"
        "0 - идентично известному решению из базы.\n"
        "0.5 - вариация известного решения.\n"
        "1.0 - принципиально новое решение (нет в базе).\n\n"
        "СНАЧАЛА рассуждай, укажи ближайший аналог из базы (если есть). "
        "В САМОМ КОНЦЕ ОБЯЗАТЕЛЬНО напиши вердикт в формате 'РЕЗУЛЬТАТ: [0, 0.5 или 1.0]'."
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_URI,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000
        )
        msg_dict = response.choices[0].message.model_dump()
        content = msg_dict.get('content') or msg_dict.get('reasoning_content') or ""
        
        score = 1.0
        if "РЕЗУЛЬТАТ: 0.5" in content:
            score = 0.5
        elif "РЕЗУЛЬТАТ: 0" in content:
            score = 0.0
            
        # Extract the reasoning as the analog description
        analog = content.replace("РЕЗУЛЬТАТ:", "").strip()[:200] + "..."
        
        return {"score": score, "аналог": analog}
    except Exception as e:
        print(f"Error scoring novelty: {e}")
        return {"score": 1.0, "аналог": "Ошибка оценки"}

def score_value(hypothesis: dict, b1_data: dict) -> dict:
    """
    Calculates objective potential value based on B1 data limits.
    """
    client = get_client()
    
    # Extract target class from hypothesis (simplified logic)
    # The real system should either have B6 output the target class or infer it.
    desc = hypothesis.get("описание", "")
    target_class = None
    target_lost_tons = 0.0
    
    for cls in b1_data.get("классы", []):
        if cls["класс"] in desc:
            target_class = cls["класс"]
            ni = cls.get("никель_извлекаемый_т") or 0
            cu = cls.get("медь_извлекаемый_т") or 0
            try: target_lost_tons = float(ni) + float(cu)
            except: target_lost_tons = 0.0
            break
            
    if not target_class:
        # Default to the worst class if not explicitly mentioned
        max_lost = 0
        for cls in b1_data.get("классы", []):
            ni = cls.get("никель_извлекаемый_т") or 0
            cu = cls.get("медь_извлекаемый_т") or 0
            try: lost = float(ni) + float(cu)
            except: lost = 0.0
            if lost > max_lost:
                max_lost = lost
                target_class = cls["класс"]
                target_lost_tons = lost
                
    prompt = (
        f"Гипотеза: {desc}\n"
        f"Целевой класс: {target_class}\n"
        "Оцени, какую долю от максимально возможных потерь (от 0.0 до 1.0) реально предотвратить с помощью этого решения?\n"
        "Ответь только числом (например: 0.3)."
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_URI,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        msg_dict = response.choices[0].message.model_dump()
        content = msg_dict.get('content') or msg_dict.get('reasoning_content') or "0.2"
        fraction = float(content.strip().split()[-1])
        fraction = max(0.0, min(1.0, fraction))
    except Exception:
        fraction = 0.2
        
    value_tons = target_lost_tons * fraction
    
    return {
        "потенциальная_ценность_тонн": value_tons,
        "обоснование_ценности": f"Потолок {target_lost_tons} тонн (ОБЪЕКТИВНО из данных класса {target_class}); доля {fraction*100}% — оценка LLM."
    }

def score_risks(hypothesis: dict) -> dict:
    """
    Evaluates technical and economic risks.
    """
    client = get_client()
    desc = hypothesis.get("описание", "")
    
    prompt = (
        f"Гипотеза: {desc}\n\n"
        "Оцени технический и экономический риски внедрения. "
        "Ответь строго в формате JSON:\n"
        '{"технический_риск": "описание риска и оценка", "экономический_риск": "описание риска и оценка"}'
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_URI,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500
        )
        msg_dict = response.choices[0].message.model_dump()
        content = msg_dict.get('content') or msg_dict.get('reasoning_content') or "{}"
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        else:
            # If it's not wrapped in code blocks, try to find { and }
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end+1]
        
        parsed = json.loads(content)
        return {
            "риск_технический": parsed.get("технический_риск", "Н/Д"),
            "риск_экономический": parsed.get("экономический_риск", "Н/Д")
        }
    except Exception as e:
        print(f"Error scoring risks: {e}")
        return {"риск_технический": "Ошибка оценки", "риск_экономический": "Ошибка оценки"}

def evaluate_all_axes(hypothesis: dict, b1_data: dict) -> dict:
    novelty = score_novelty(hypothesis)
    value = score_value(hypothesis, b1_data)
    risks = score_risks(hypothesis)
    
    hypothesis.update(novelty)
    hypothesis.update(value)
    hypothesis.update(risks)
    
    return hypothesis
