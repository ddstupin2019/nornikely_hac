import json
from b6_generate import get_client, MODEL_URI
from b3_embed_retrieve import retrieve

def extract_claims(hypothesis: dict) -> list:
    """
    Step 1: Break hypothesis and its mechanism into atomic claims.
    """
    client = get_client()
    text = f"Гипотеза: {hypothesis.get('описание')}\nМеханизм: {hypothesis.get('механизм')}"
    
    prompt = (
        "Разбей следующий текст на 3-5 простых атомарных утверждений (фактов/заявлений).\n\n"
        f"Текст:\n{text}\n\n"
        "Ответь ТОЛЬКО валидным JSON массивом строк (без ```json), например:\n"
        '["утверждение 1", "утверждение 2"]'
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_URI,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000
        )
        content = response.choices[0].message.content or response.choices[0].message.model_dump().get('reasoning_content') or ""
        
        # Cleanup potential markdown
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Error extracting claims: {e}")
        return [hypothesis.get('механизм', '')] # Fallback to just the mechanism

def check_entailment(claim: str, context: list) -> dict:
    """
    Step 3: Check if the context supports the claim.
    Returns {"supported": bool, "citation": dict or None}
    """
    if not context:
        return {"supported": False, "citation": None}
        
    client = get_client()
    
    context_text = "\n\n".join([f"Источник {i+1} ({c.get('книга')} стр {c.get('стр')}): {c.get('текст')}" for i, c in enumerate(context)])
    
    prompt = (
        f"Утверждение: {claim}\n\n"
        f"Документы:\n{context_text}\n\n"
        "Подтверждают ли документы это утверждение? Ответь 'ДА' если подтверждают или 'НЕТ' если не подтверждают или информации недостаточно.\n"
        "СНАЧАЛА кратко рассуждай, а в самом конце ОБЯЗАТЕЛЬНО напиши вердикт в формате 'РЕЗУЛЬТАТ: ДА' или 'РЕЗУЛЬТАТ: НЕТ'."
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
        answer = content.strip().upper()
        
        is_supported = "РЕЗУЛЬТАТ: ДА" in answer
        
        # If supported, just return the first context as citation for demo 
        # (In a real system, we'd ask LLM WHICH document supported it)
        citation = {"книга": context[0].get("книга"), "стр": context[0].get("стр")} if is_supported else None
        
        return {"supported": is_supported, "citation": citation}
    except Exception as e:
        print(f"Error checking entailment: {e}")
        return {"supported": False, "citation": None}

def evaluate_grounding(hypothesis: dict) -> dict:
    """
    Evaluates the grounding of a hypothesis against the knowledge base.
    """
    claims = extract_claims(hypothesis)
    if not claims:
        hypothesis["grounding_score"] = 0.0
        hypothesis["цитаты"] = []
        return hypothesis
        
    supported_count = 0
    all_citations = []
    
    for claim in claims:
        # Step 2: Retrieve
        chunks = retrieve(claim, k=2)
        # Step 3: Entailment
        result = check_entailment(claim, chunks)
        
        if result["supported"]:
            supported_count += 1
            if result["citation"]:
                all_citations.append({
                    "утверждение": claim,
                    "книга": result["citation"]["книга"],
                    "стр": result["citation"]["стр"]
                })
                
    # Step 4: Calculate score
    score = supported_count / len(claims)
    
    hypothesis["grounding_score"] = score
    hypothesis["цитаты"] = all_citations
    hypothesis["надежная"] = score >= 0.5
    
    return hypothesis
