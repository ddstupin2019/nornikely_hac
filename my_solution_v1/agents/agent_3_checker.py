import json
from typing import List, Dict, Any, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from my_solution_v1.agents.base import get_llm
from my_solution_v1.rag.vector_store import get_retriever
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

def check_hypotheses_chunk(hypotheses_chunk: List[dict], structured_task: dict, file_context: str = "") -> Tuple[List[dict], List[str]]:
    # 1. Fetch RAG context for all hypotheses in the chunk
    retriever = get_retriever()
    context_text = ""
    if retriever:
        for h in hypotheses_chunk:
            query = f"{h.get('название', '')} {h.get('механизм', '')}"
            try:
                docs = retriever.invoke(query)
                for doc in docs[:2]:
                    context_text += f"Источник: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}\n\n"
            except Exception:
                pass
    else:
        context_text = "Векторная база пока пуста или отключена."
        
    # Ограничиваем размер контекста, чтобы не переполнять LLM
    context_text = context_text[:10000]
    file_context_trunc = file_context[:10000]
    combined_context = f"{context_text}\n\nДополнительные материалы к задаче:\n{file_context_trunc}"
    
    parser = JsonOutputParser()
    
    template = (
        "Ты R&D эксперт-валидатор. Твоя задача - проверить список из {count} гипотез на реалистичность "
        "с учетом предоставленных выдержек из базы знаний (источников) и ОГРАНИЧЕНИЙ ЗАДАЧИ.\n"
        "ВАЖНО: Если в ограничениях задачи или требованиях к оборудованию указано 'стандартное оборудование', "
        "а гипотеза предлагает внедрение НОВОГО оборудования, ты ОБЯЗАН ОТКЛОНИТЬ гипотезу.\n\n"
        "ТРЕБОВАНИЯ К ОБОСНОВАНИЮ И ПРОВЕРКЕ:\n"
        "- Обоснование должно опираться на КОНКРЕТНЫЕ факты, методы или физико-химические процессы из контекста.\n"
        "- МАТЕМАТИЧЕСКАЯ ТОЧНОСТЬ: Если гипотеза предлагает точные цифры (например градусы, проценты, МПа, кг/т), СТРОГО сверь их с контекстом. Если цифры взяты с потолка или отсутствуют в контексте - ОТКЛОНЯЙ гипотезу (Вердикт: false).\n"
        "- ЖЕСТКИЙ ФИЛЬТР 'ВОДЫ': Если гипотеза содержит только общие, размытые фразы без четкого инженерного/физико-химического механизма действия — ОТКЛОНЯЙ её (Вердикт: false).\n"
        "- НЕРЕЛЕВАНТНОСТЬ И АБСУРД: Если гипотеза вообще не решает проблему пользователя или предлагает антинаучный/абсурдный бред — ОТКЛОНЯЙ её (Вердикт: false).\n"
        "- ЖЕСТКИЕ ОГРАНИЧЕНИЯ: Если гипотеза прямо нарушает жесткие ограничения задачи (например, требует нового оборудования при запрете) - ОТКЛОНЯЙ её (Вердикт: false).\n"
        "- Если гипотеза логична, имеет смысл и не нарушает ограничений — пропускай её (Вердикт: true), НО пиши конкретное обоснование. Кроме того, ТЫ ДОЛЖЕН ДОУТОЧНИТЬ гипотезу: сделай ее название и механизм максимально конкретными, техническими и опирающимися на найденные факты из базы знаний.\n\n"
        "Оцени КАЖДУЮ гипотезу из списка. Верни JSON МАССИВ объектов. Для каждой гипотезы верни объект:\n"
        "{{\"id\": \"идентификатор_гипотезы\", \"is_valid\": true/false, \"justification_or_reason\": \"Обоснование...\", \"refined_title\": \"Уточненное название\", \"refined_mechanism\": \"Уточненный, более детальный механизм...\", \"sources\": [\"имя_файла, стр. X\"]}} \n"
        "ВНИМАНИЕ! Для поля sources ОБЯЗАТЕЛЬНО находи в тексте теги [стр. X] и указывай номер страницы или листа. Возвращай только валидный JSON массив без текста до и после.\n\n"
        "ОГРАНИЧЕНИЯ ЗАДАЧИ:\n"
        "Требуемое Оборудование: {equipment}\n"
        "Доп. Ограничения: {constraints}\n\n"
        "Гипотезы для проверки:\n{hypotheses_text}\n\nКонтекст из базы знаний:\n{context_text}\n\n"
        "{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = get_llm(temperature=0.1)
    chain = prompt | llm | parser
    
    # Даем гипотезам временные ID для сопоставления
    for i, h in enumerate(hypotheses_chunk):
        h["_temp_id"] = f"temp_{i}"
        
    valid_hyps = []
    feedbacks = []
    
    for attempt in range(2):
        try:
            results = chain.invoke({
                "count": len(hypotheses_chunk),
                "equipment": structured_task.get("Оборудование", "Не указано"),
                "constraints": structured_task.get("Дополнительные_ограничения", "Не указано"),
                "hypotheses_text": json.dumps([{"id": h["_temp_id"], "название": h.get("название"), "механизм": h.get("механизм")} for h in hypotheses_chunk], ensure_ascii=False),
                "context_text": combined_context,
                "format_instructions": parser.get_format_instructions()
            })
            
            # Проверяем что вернулся список
            if not isinstance(results, list):
                raise ValueError("Expected a JSON array")
                
            result_map = {r.get("id"): r for r in results if isinstance(r, dict)}
            
            for h in hypotheses_chunk:
                temp_id = h.pop("_temp_id", None)
                res = result_map.get(temp_id)
                if not res:
                    feedbacks.append(f"Гипотеза '{h.get('название')}' пропущена валидатором.")
                    continue
                    
                if res.get("is_valid"):
                    h["обоснование"] = res.get("justification_or_reason", "")
                    h["источники"] = res.get("sources", [])
                    if res.get("refined_title"):
                        h["название"] = res.get("refined_title")
                    if res.get("refined_mechanism"):
                        h["механизм"] = res.get("refined_mechanism")
                    valid_hyps.append(h)
                else:
                    reason = res.get("justification_or_reason", "Без причины.")
                    logger.info(f"Rejected: '{h.get('название')}' - Reason: {reason}")
                    feedbacks.append(f"Гипотеза '{h.get('название')}' отклонена: {reason}")
            
            return valid_hyps, feedbacks
            
        except Exception as e:
            logger.error(f"Agent 3 failed to check batch (attempt {attempt+1}): {e}")
            
    # Если всё упало, возвращаем пустые списки, гипотезы просто отбрасываются
    for h in hypotheses_chunk:
        h.pop("_temp_id", None)
        feedbacks.append(f"Ошибка валидации гипотезы '{h.get('название')}'.")
        
    return [], feedbacks

import concurrent.futures

def check_hypotheses_batch(hypotheses: List[Dict[str, Any]], structured_task: dict, file_context: str = "") -> Tuple[List[Dict[str, Any]], List[str]]:
    valid_hypotheses = []
    feedbacks = []
    
    # Разбиваем на чанки по 5 штук
    chunk_size = 5
    chunks = [hypotheses[i:i + chunk_size] for i in range(0, len(hypotheses), chunk_size)]
    
    def process_chunk(idx, chunk):
        logger.info(f"Checking hypotheses chunk {idx+1} (size {len(chunk)})...")
        return check_hypotheses_chunk(chunk, structured_task, file_context)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_chunk, i, chunk) for i, chunk in enumerate(chunks)]
        for future in concurrent.futures.as_completed(futures):
            try:
                v_hyps, f_backs = future.result()
                valid_hypotheses.extend(v_hyps)
                feedbacks.extend(f_backs)
            except Exception as e:
                logger.error(f"Error checking chunk concurrently: {e}")
            
    return valid_hypotheses, feedbacks
