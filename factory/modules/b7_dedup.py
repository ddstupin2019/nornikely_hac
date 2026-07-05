import json
import concurrent.futures
from b6_generate import get_client, MODEL_URI

def check_duplicate(hyp_a: dict, hyp_b: dict) -> bool:
    """
    Uses LLM to check if two hypotheses are conceptually identical.
    Returns True if they propose the same core action, False otherwise.
    """
    client = get_client()
    
    prompt = (
        "Сравни две инженерные гипотезы.\n\n"
        f"Гипотеза A:\nНазвание: {hyp_a.get('название')}\nДействие: {hyp_a.get('описание')}\n\n"
        f"Гипотеза B:\nНазвание: {hyp_b.get('название')}\nДействие: {hyp_b.get('описание')}\n\n"
        "Они предлагают концептуально ОДНО И ТО ЖЕ физическое/химическое воздействие на процесс (даже если сказано разными словами)?\n"
        "СНАЧАЛА кратко рассуждай, а в самом конце ОБЯЗАТЕЛЬНО напиши вердикт в формате 'РЕЗУЛЬТАТ: ДА' или 'РЕЗУЛЬТАТ: НЕТ'."
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_URI,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000
        )
        
        message_dict = response.choices[0].message.model_dump()
        content = message_dict.get('content') or message_dict.get('reasoning_content') or ""
        answer = content.strip().upper()
        # print(f"LLM Answer for {hyp_a['название']} vs {hyp_b['название']}:\n{answer}\n")
        return "РЕЗУЛЬТАТ: ДА" in answer
    except Exception as e:
        print(f"Error in deduplication check: {e}")
        return False

def deduplicate_hypotheses(hypotheses: list) -> list:
    """
    Deduplicates a list of hypotheses.
    If a duplicate is found, keeps the one with the longer description 
    (assuming longer = more specific/grounded).
    """
    if not hypotheses:
        return []
        
    unique_hyps = []
    
    for current_hyp in hypotheses:
        is_dup = False
        
        # Check against already accepted hypotheses
        for i, accepted_hyp in enumerate(unique_hyps):
            if check_duplicate(current_hyp, accepted_hyp):
                is_dup = True
                
                # Keep the more detailed one
                len_curr = len(current_hyp.get("описание", "")) + len(current_hyp.get("обоснование", ""))
                len_acc = len(accepted_hyp.get("описание", "")) + len(accepted_hyp.get("обоснование", ""))
                
                if len_curr > len_acc:
                    print(f"[DEDUP] '{current_hyp['название']}' ЗАМЕНИЛА '{accepted_hyp['название']}' (более детальная)")
                    unique_hyps[i] = current_hyp
                else:
                    print(f"[DEDUP] '{current_hyp['название']}' ПРОПУЩЕНА (дублирует '{accepted_hyp['название']}')")
                break
                
        if not is_dup:
            unique_hyps.append(current_hyp)
            
    return unique_hyps

if __name__ == "__main__":
    pass
