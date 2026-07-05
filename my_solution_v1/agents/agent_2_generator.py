import re
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from my_solution_v1.agents.base import get_llm
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

def normalize_keys(hyp: dict) -> dict:
    """Нормализация ключей на случай, если модель возвращает синонимы."""
    mapping = {
        "название": "название",
        "имя": "название",
        "title": "название",
        "описание": "описание",
        "description": "описание",
        "механизм": "механизм",
        "mechanism": "механизм",
        "риск_технический": "риск_технический",
        "технический риск": "риск_технический",
        "технические риски": "риск_технический",
        "tech_risk": "риск_технический",
        "риск_экономический": "риск_экономический",
        "экономический риск": "риск_экономический",
        "экономические риски": "риск_экономический",
        "economic_risk": "риск_экономический"
    }
    
    normalized = {}
    for k, v in hyp.items():
        lower_k = k.lower().strip()
        new_k = mapping.get(lower_k, lower_k)
        normalized[new_k] = v
        
    # Ensure required keys exist
    for req in ["название", "описание", "механизм", "риск_технический", "риск_экономический"]:
        if req not in normalized:
            normalized[req] = "Не указано"
            
    return normalized

import concurrent.futures

def deduplicate_hypotheses(hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique = []
    seen_names = set()
    for hyp in hypotheses:
        name = hyp.get("название", "").strip().lower()
        if name and name not in seen_names:
            seen_names.add(name)
            unique.append(hyp)
    return unique

def _generate_with_model(structured_task: dict, file_context: str, feedback_section: str, parser: JsonOutputParser, model_type: str, target_count: int = 10) -> List[Dict[str, Any]]:
    template = (
        f"Ты R&D исследователь. Твоя задача сгенерировать ровно {target_count} научных гипотез для решения проблемы. "
        f"Верни результат в формате JSON - списка из {target_count} объектов. "
        "Каждый объект должен иметь ключи: 'название', 'описание', 'механизм', 'риск_технический', 'риск_экономический'.\n\n"
        "ВАЖНОЕ ПРАВИЛО: Если задача требует достижения точных математических или физических показателей (например МПа, °C, %), "
        "КАТЕГОРИЧЕСКИ ЗАПРЕЩАЕТСЯ выдумывать температурные режимы, химические пропорции и другие точные цифры из головы! "
        "Бери цифры ИСКЛЮЧИТЕЛЬНО из таблиц и текста в предоставленной литературе.\n\n"
        "Проблема: {problem}\nОборудование: {equipment}\nБюджет: {budget}\nОграничения: {constraints}\n\n"
        "Контекст файлов:\n{context}\n\n"
        "{feedback_section}"
        "ВНИМАНИЕ: ОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ! КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО ИСПОЛЬЗОВАТЬ КИТАЙСКИЕ ИЕРОГЛИФЫ ИЛИ ДРУГИЕ ЯЗЫКИ.\n"
        "Сгенерируй только валидный JSON-массив, без дополнительных комментариев и без блоков кода Markdown.\n"
        "{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = get_llm(temperature=0.7, model_type=model_type)
    chain = prompt | llm | parser
    
    try:
        logger.info(f"Generating with {model_type}...")
        hypotheses = chain.invoke({
            "problem": structured_task.get('Проблема', ''),
            "equipment": structured_task.get('Оборудование', ''),
            "budget": structured_task.get('Бюджет', ''),
            "constraints": structured_task.get('Дополнительные_ограничения', ''),
            "context": file_context[:8000],
            "feedback_section": feedback_section,
            "format_instructions": parser.get_format_instructions()
        })
        
        if not isinstance(hypotheses, list):
            hypotheses = [hypotheses]
            
        return [normalize_keys(hyp) for hyp in hypotheses]
    except Exception as e:
        logger.error(f"Agent 2 failed with model {model_type}: {e}")
        return []

def generate_hypotheses(structured_task: dict, file_context: str = "", feedback: List[str] = None, target_count: int = 10) -> List[Dict[str, Any]]:
    parser = JsonOutputParser()
    
    feedback_section = ""
    if feedback and len(feedback) > 0:
        feedback_str = "\n".join(feedback)
        feedback_section = f"ВНИМАНИЕ! Следующие гипотезы ранее были отклонены по указанным причинам. Не повторяй их!\nОшибки прошлых гипотез:\n{feedback_str}\n\n"
    
    all_hypotheses = []
    
    # Run both models concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_qwen = executor.submit(_generate_with_model, structured_task, file_context, feedback_section, parser, "qwen", target_count)
        future_ds = executor.submit(_generate_with_model, structured_task, file_context, feedback_section, parser, "deepseek", target_count)
        
        qwen_hyps = future_qwen.result()
        ds_hyps = future_ds.result()
        
    all_hypotheses.extend(qwen_hyps)
    all_hypotheses.extend(ds_hyps)
    
    # Deduplicate
    unique_hyps = deduplicate_hypotheses(all_hypotheses)
    logger.info(f"Generated {len(all_hypotheses)} raw hypotheses across models. After deduplication: {len(unique_hyps)}")
    
    return unique_hyps
