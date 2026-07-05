from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import uuid

# Import our pipeline modules
from b1_parse_xlsx import parse_xlsx
from b3_embed_retrieve import retrieve
from b4_constraints import parse_constraints
from b5_context import build_prompt
from b6_generate import generate_ensemble
from b7_dedup import deduplicate_hypotheses
from b8_ground import evaluate_grounding
from b9_score_axes import evaluate_all_axes
from b10_filter import b10_pipeline
from b11_rank import rank_hypotheses

app = FastAPI(title="Hypothesis Factory API")

# Request Models
class GenerateRequest(BaseModel):
    kpi_goal: str
    constraints_text: str
    xlsx_path: str
    equipment_json_path: Optional[str] = "factory/data/equipment.json"
    
class FeedbackRequest(BaseModel):
    hypothesis_id: str
    expert_score: float
    correction: Optional[str] = ""

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Hypothesis Factory API is running."}

@app.post("/generate")
def generate_hypotheses(req: GenerateRequest):
    if not os.path.exists(req.xlsx_path):
        raise HTTPException(status_code=400, detail=f"File not found: {req.xlsx_path}")
        
    try:
        # B1: Parse Excel
        b1_data = parse_xlsx(req.xlsx_path)
        
        # B4: Parse constraints
        b4_data = parse_constraints(req.equipment_json_path or "", req.constraints_text)
        
        # B3: Retrieve knowledge (initial broad query based on KPI)
        b3_chunks = retrieve(req.kpi_goal, k=2)
        
        # B5: Build context
        prompt = build_prompt(req.kpi_goal, b1_data, b3_chunks, b4_data)
        
        # B6: Generate (Using single temp for speed in API, can be expanded)
        hypotheses = generate_ensemble(prompt, ensemble_configs=[0.5])
        
        # Give them IDs
        for h in hypotheses:
            h["id"] = str(uuid.uuid4())
            
        # B7: Deduplicate
        unique_hyps = deduplicate_hypotheses(hypotheses)
        
        # B8 & B9: Evaluate grounding and axes
        evaluated_hyps = []
        for h in unique_hyps:
            h = evaluate_grounding(h)
            h = evaluate_all_axes(h, b1_data)
            evaluated_hyps.append(h)
            
        # B10: Filter
        passed_hyps = b10_pipeline(evaluated_hyps)
        
        # B11: Rank
        ranked_hyps = rank_hypotheses(passed_hyps)
        
        return {
            "status": "success",
            "count": len(ranked_hyps),
            "top_hypotheses": ranked_hyps
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """
    Saves expert feedback for future few-shot injection or weight adjustments.
    """
    feedback_file = "factory/data/feedback.json"
    os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
    
    feedbacks = []
    if os.path.exists(feedback_file):
        with open(feedback_file, "r", encoding="utf-8") as f:
            feedbacks = json.load(f)
            
    feedbacks.append({
        "hypothesis_id": req.hypothesis_id,
        "expert_score": req.expert_score,
        "correction": req.correction
    })
    
    with open(feedback_file, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        
    return {"status": "success", "message": "Feedback saved successfully"}

if __name__ == "__main__":
    import uvicorn
    print("Starting API on http://127.0.0.1:8000")
    uvicorn.run("b12_api:app", host="127.0.0.1", port=8000, reload=True)
