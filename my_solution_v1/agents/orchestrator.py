from typing import List, Dict, Any
from my_solution_v1.core.logger import get_logger
from my_solution_v1.agents.agent_1_parser import parse_user_request
from my_solution_v1.agents.agent_2_generator import generate_hypotheses
from my_solution_v1.agents.agent_3_checker import check_hypotheses_batch
from my_solution_v1.agents.agent_4_ranker import rank_hypotheses

logger = get_logger(__name__)

def run_hypothesis_pipeline(raw_text: str, file_context: str = "", progress_callback=None) -> List[Dict[str, Any]]:
    """
    Main orchestrator logic to run the full pipeline.
    """
    logger.info("Starting pipeline...")
    
    def update_progress(stage: int, desc: str):
        if progress_callback:
            progress_callback(stage, desc)

    # Step 1: Parse
    update_progress(1, "Агент 1: Анализ ограничений задачи")
    structured_task = parse_user_request(raw_text, file_context)
    logger.info(f"Task structured: {structured_task}")
    
    verified_pool = []
    all_raw_hypotheses = []
    feedback = []
    MAX_ITERATIONS = 3
    for iteration in range(MAX_ITERATIONS):
        logger.info(f"--- Iteration {iteration+1}/{MAX_ITERATIONS} ---")
        update_progress(2, f"Агент 2: Генерация сырых гипотез (Попытка {iteration+1})")
        
        # На 3-й итерации генерируем только 5 гипотез на каждую модель
        target_count = 5 if iteration == 2 else 10
        
        logger.info("Agent 2: Генерация сырых гипотез...")
        raw_hypotheses = generate_hypotheses(structured_task, file_context, feedback, target_count=target_count)
        logger.info(f"Generated {len(raw_hypotheses)} raw hypotheses.")
        
        all_raw_hypotheses.extend(raw_hypotheses)
        
        # Step 3: Check hypotheses
        update_progress(3, f"Агент 3: Жесткая валидация и отсев (Попытка {iteration+1})")
        valid_hyps, current_feedbacks = check_hypotheses_batch(raw_hypotheses, structured_task, file_context)
        
        verified_pool.extend(valid_hyps)
        feedback = current_feedbacks # pass only the latest feedbacks to not overwhelm context
        
        logger.info(f"Valid in this batch: {len(valid_hyps)}. Total verified pool: {len(verified_pool)}")
        
        if len(verified_pool) >= 10:
            logger.info("Reached target of 10 verified hypotheses. Stopping generation loop.")
            break
            
    if len(verified_pool) == 0:
        logger.warning("No hypotheses passed validation. Falling back to the last 20 generated raw hypotheses.")
        verified_pool = all_raw_hypotheses[-20:]
        for h in verified_pool:
            if "обоснование" not in h:
                h["обоснование"] = "Гипотеза не прошла строгую валидацию, добавлена в качестве резерва."
            if "источники" not in h:
                h["источники"] = []
                
    # Step 4: Rank
    update_progress(4, "Агент 4: Математическое ранжирование (Выбор Топ-5)")
    logger.info("Ranking top hypotheses...")
    top_5 = rank_hypotheses(verified_pool, structured_task)
    
    # Step 5: Format to detailed JSON
    update_progress(5, "Агент 5: Итоговое форматирование и сбор цитат")
    logger.info("Formatting top 5 hypotheses to detailed JSON (with RAG lookup)...")
    from my_solution_v1.agents.agent_5_formatter import format_hypotheses_batch
    from my_solution_v1.rag.vector_store import get_retriever
    
    retriever = get_retriever()
    final_output = format_hypotheses_batch(top_5, structured_task, file_context, retriever)
    
    logger.info("Pipeline finished.")
    
    return final_output
