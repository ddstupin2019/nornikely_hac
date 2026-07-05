import json
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from my_solution_v1.agents.base import get_llm
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

def rank_hypotheses(hypotheses: List[Dict[str, Any]], structured_task: Dict[str, str]) -> List[Dict[str, Any]]:
    if not hypotheses:
        return []
        
    parser = JsonOutputParser()
    # Назначаем временные ID для сопоставления
    for i, h in enumerate(hypotheses):
        h["_rank_id"] = f"rank_{i}"
        
    template = (
        "Ты R&D директор и главный эксперт. Твоя задача - математически оценить и отранжировать список гипотез.\n\n"
        "ЦЕЛЬ И ОГРАНИЧЕНИЯ ИСХОДНОЙ ЗАДАЧИ:\n"
        "Проблема: {problem}\n"
        "Требования к оборудованию: {equipment}\n"
        "Бюджет: {budget}\n"
        "Дополнительные ограничения: {constraints}\n\n"
        "СИСТЕМА ОЦЕНОК (от 0 до 10 баллов для каждого критерия):\n"
        "1. score_alignment (0-10): Соответствие целям и жестким ограничениям задачи.\n"
        "2. score_feasibility (0-10): Практическая реализуемость.\n"
        "3. score_quality (0-10): Качество гипотезы и обоснования.\n"
        "4. score_business (0-10): Бизнес-ценность.\n\n"
        "ВАЖНОЕ ПРАВИЛО ШТРАФОВ ЗА ГАЛЛЮЦИНАЦИИ:\n"
        "Если в Обосновании гипотезы присутствует текст '[НЕПОДТВЕРЖДЕННЫЕ ДАННЫЕ]', СТРОГО снижай score_quality до 1-3 баллов. Максимальный total_score не должен превышать 15 из 40.\n\n"
        "ЗАДАЧА:\n"
        "1. Оцени каждую гипотезу из списка.\n"
        "2. Верни массив JSON объектов, содержащих ТОЛЬКО результаты оценки для каждой гипотезы.\n"
        "Формат каждого объекта:\n"
        "{{\n"
        "  \"_rank_id\": \"идентификатор гипотезы из списка (обязательно!)\",\n"
        "  \"score_alignment\": число,\n"
        "  \"score_feasibility\": число,\n"
        "  \"score_quality\": число,\n"
        "  \"score_business\": число,\n"
        "  \"total_score\": сумма_баллов,\n"
        "  \"итоговая_оценка_от_директора\": \"краткий текстовый вердикт\"\n"
        "}}\n"
        "Верни ТОЛЬКО валидный JSON массив без текста до и после.\n\n"
        "Входящий список проверенных гипотез (содержит _rank_id):\n{hypotheses_text}\n"
        "{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = get_llm(temperature=0.1)
    chain = prompt | llm | parser
    
    try:
        results = chain.invoke({
            "problem": structured_task.get("Проблема", "Не указано"),
            "equipment": structured_task.get("Оборудование", "Не указано"),
            "budget": structured_task.get("Бюджет", "Не указано"),
            "constraints": structured_task.get("Дополнительные_ограничения", "Не указано"),
            "hypotheses_text": json.dumps([{"_rank_id": h["_rank_id"], "название": h.get("название"), "механизм": h.get("механизм"), "обоснование": h.get("обоснование")} for h in hypotheses], ensure_ascii=False),
            "format_instructions": parser.get_format_instructions()
        })
        
        if isinstance(results, list):
            result_map = {r.get("_rank_id"): r for r in results if isinstance(r, dict)}
            
            for h in hypotheses:
                rid = h.get("_rank_id")
                res = result_map.get(rid, {})
                
                # Merge scores back into the original hypothesis
                h["score_alignment"] = float(res.get("score_alignment", 0))
                h["score_feasibility"] = float(res.get("score_feasibility", 0))
                h["score_quality"] = float(res.get("score_quality", 0))
                h["score_business"] = float(res.get("score_business", 0))
                h["total_score"] = float(res.get("total_score", h["score_alignment"] + h["score_feasibility"] + h["score_quality"] + h["score_business"]))
                h["итоговая_оценка_от_директора"] = res.get("итоговая_оценка_от_директора", "")
                
                # Cleanup temporary ID
                h.pop("_rank_id", None)
            
            hypotheses.sort(key=lambda x: x.get("total_score", 0), reverse=True)
            return hypotheses[:5]
        else:
            logger.warning("Agent 4 didn't return a list.")
            for h in hypotheses:
                h.pop("_rank_id", None)
            return hypotheses[:5]
            
    except Exception as e:
        logger.error(f"Agent 4 failed to rank hypotheses: {e}")
        return hypotheses[:5]
