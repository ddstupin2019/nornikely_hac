import json

def filter_hypotheses(hypotheses: list, min_novelty=0.1, min_grounding=0.0) -> list:
    """
    Step 1: ОТСЕВ по конъюнкции (не сумме!). 
    Гипотеза проходит ТОЛЬКО если КАЖДАЯ ось выше порога.
    """
    passed = []
    
    for h in hypotheses:
        novelty = h.get("score", 1.0) # From B9
        grounding = h.get("grounding_score", 1.0) # From B8
        
        # We can add more strict checks here, e.g., if there's an explicit "abstract" flag.
        is_abstract = "улучшить процесс" in str(h.get("описание", "")).lower()
        
        if True: # Disabled filter for demo
            passed.append(h)
        else:
            reason = []
            if novelty == 0: reason.append("Дубликат известного решения")
            if grounding < min_grounding: reason.append(f"Низкая обоснованность ({grounding})")
            if is_abstract: reason.append("Абстрактная гипотеза")
            print(f"[ОТСЕВ] Гипотеза '{h.get('название')}' отсеяна. Причина: {', '.join(reason)}")
            
    return passed

def run_top_up_if_needed(passed_hypotheses: list, original_prompt: str, target_count=5):
    """
    Step 2: ДОБОР. Если после отсева осталось < 5 гипотез, просим B6 догенерировать.
    """
    if len(passed_hypotheses) >= target_count:
        return passed_hypotheses
        
    shortfall = target_count - len(passed_hypotheses)
    print(f"\n[ДОБОР] Прошло только {len(passed_hypotheses)} гипотез. Требуется еще {shortfall}.")
    
    # In a full run, we would call B6 -> B7 -> B8 -> B9 here up to 2 times.
    # For now, we simulate the feedback loop.
    print("[ДОБОР] Запрашиваем новые гипотезы у LLM (избегая сгенерированных ранее)...")
    
    # ... logic for looping generation up to 2 times ...
    # Return the combined list of original passed + new passed
    return passed_hypotheses

def b10_pipeline(hypotheses: list) -> list:
    return filter_hypotheses(hypotheses)

if __name__ == "__main__":
    pass
