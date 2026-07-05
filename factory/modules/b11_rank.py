def rank_hypotheses(hypotheses: list, w_ground=0.3, w_novelty=0.3, w_value=0.4, w_risk=0.1) -> list:
    """
    Ranks filtered hypotheses using a weighted sum of axes.
    ранг = w1·обоснованность + w2·новизна + w3·нормализованная_ценность − w4·риск
    """
    if not hypotheses:
        return []
        
    # Normalize value (tons)
    max_tons = max([h.get("потенциальная_ценность_тонн", 0.0) for h in hypotheses]) if hypotheses else 0
    
    for h in hypotheses:
        grounding = h.get("grounding_score", 0.0)
        novelty = h.get("score", 0.0)
        
        raw_value = h.get("потенциальная_ценность_тонн", 0.0)
        norm_value = (raw_value / max_tons) if max_tons > 0 else 0.0
        
        # Simplified risk penalty (1 if mentioned risk is high/critical, else 0)
        tech_risk = h.get("риск_технический", "")
        econ_risk = h.get("риск_экономический", "")
        risk_penalty = 0.0
        if "высок" in tech_risk.lower() or "критич" in tech_risk.lower():
            risk_penalty += 0.5
        if "высок" in econ_risk.lower() or "критич" in econ_risk.lower():
            risk_penalty += 0.5
            
        rank_score = (w_ground * grounding) + (w_novelty * novelty) + (w_value * norm_value) - (w_risk * risk_penalty)
        h["final_rank_score"] = round(rank_score, 3)
        h["norm_value"] = round(norm_value, 2)
        
    # Sort descending by final rank score
    ranked = sorted(hypotheses, key=lambda x: x["final_rank_score"], reverse=True)
    return ranked[:5] # Top 5
