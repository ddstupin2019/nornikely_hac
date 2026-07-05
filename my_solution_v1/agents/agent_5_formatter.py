import json
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from my_solution_v1.agents.base import get_llm
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

def format_hypothesis(hyp: dict, structured_task: dict, file_context: str = "", retriever=None) -> dict:
    parser = JsonOutputParser()
    
    # Query RAG
    rag_context = ""
    if retriever:
        query = f"{hyp.get('название', '')} {hyp.get('механизм', '')} {hyp.get('описание', '')}"
        try:
            docs = retriever.invoke(query)
            for d in docs:
                rag_context += f"Файл: {d.metadata.get('source', 'Неизвестно')}\nТекст: {d.page_content}\n\n"
        except Exception as e:
            logger.warning(f"Failed to query RAG in Agent 5: {e}")
    
    template = (
        "Ты R&D аналитик. Твоя задача - преобразовать предоставленную гипотезу в детальный формат JSON. "
        "Внимательно изучи исходную гипотезу, задачу, данные задачи и контекст из литературы, и сгенерируй JSON со следующими ключами:\n"
        "- 'id': уникальный идентификатор (например 'h_001')\n"
        "- 'воздействие': краткое описание действия\n"
        "- 'объект': на что направлено воздействие (например 'Собиратель', 'Пульпа')\n"
        "- 'параметр': какой параметр меняется (например 'Расход собирателя')\n"
        "- 'направление': 'Увеличение', 'Уменьшение' или 'Изменение'\n"
        "- 'механизм': текст механизма из исходной гипотезы\n"
        "- 'механизм_подтверждён': boolean (true/false) на основе обоснования валидатора\n"
        "- 'целевой_показатель': из описания проблемы\n"
        "- 'обоснование': массив объектов с ключами 'источник' (имя файла), 'локация' (например 'стр. 221-222', извлеки из текста если есть теги [стр. X]), 'тезис' (цитата из литературы)\n"
        "- 'оценки': объект с ключами 'обоснованность', 'новизна', 'ценность', 'риск_технический', 'риск_экономический'. Внутри каждого укажи:\n"
        "   - 'значение' (от 0 до 1)\n"
        "   - 'состояние' (используй 'из_данных' для обоснованности, для остальных 'оценка_LLM')\n"
        "   - 'обоснование' (текст)\n"
        "   - Для 'новизна' обязательно добавь ключ 'аналог' с примером ближайшего аналога из предоставленной литературы.\n"
        "- 'что_не_знаем': массив строк с открытыми вопросами по гипотезе\n"
        "- 'генератор': 'qwen' или 'deepseek'\n"
        "- 'статус_фильтра': 'прошла'\n\n"
        "Оригинальная гипотеза: {hypothesis}\n"
        "Задача: {task}\n"
        "Специфичные данные по задаче: {file_context}\n"
        "Контекст из литературы (RAG): {rag_context}\n\n"
        "ВНИМАНИЕ! Ты обязан вернуть СТРОГО валидный JSON, соответствующий инструкциям. Никакого текста до и после JSON.\n"
        "{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = get_llm(temperature=0.1, model_type="deepseek") # Используем deepseek для стабильной генерации JSON
    chain = prompt | llm | parser
    
    for attempt in range(2):
        try:
            result = chain.invoke({
                "hypothesis": json.dumps(hyp, ensure_ascii=False),
                "task": json.dumps(structured_task, ensure_ascii=False),
                "file_context": file_context[:2000],
                "rag_context": rag_context[:4000], # Ограничиваем RAG контекст чтобы Yandex API не падал
                "format_instructions": parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"Agent 5 failed to format hypothesis (attempt {attempt+1}): {e}")
    return hyp

import concurrent.futures

def format_hypotheses_batch(hypotheses: List[Dict[str, Any]], structured_task: dict, file_context: str = "", retriever=None) -> List[Dict[str, Any]]:
    formatted = [None] * len(hypotheses)
    
    def process_one(idx, hyp):
        logger.info(f"Agent 5 formatting hypothesis {idx+1}/{len(hypotheses)}...")
        formatted_hyp = format_hypothesis(hyp, structured_task, file_context, retriever)
        formatted_hyp['id'] = f"h_{idx+1:03d}"
        
        if 'total_score' in hyp:
            formatted_hyp['total_score'] = hyp['total_score']
        if 'итоговая_оценка_от_директора' in hyp:
            formatted_hyp['итоговая_оценка_от_директора'] = hyp['итоговая_оценка_от_директора']
        return idx, formatted_hyp

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_one, i, h) for i, h in enumerate(hypotheses)]
        for future in concurrent.futures.as_completed(futures):
            try:
                idx, res = future.result()
                formatted[idx] = res
            except Exception as e:
                logger.error(f"Error in formatting concurrently: {e}")
                
    return [h for h in formatted if h is not None]
