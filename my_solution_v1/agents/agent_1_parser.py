from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from my_solution_v1.agents.base import get_llm
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

def parse_user_request(request_text: str, file_context: str = "") -> dict:
    parser = JsonOutputParser()
    
    template = (
        "Ты R&D системный аналитик. Извлеки структурированную информацию из запроса пользователя. "
        "Верни результат СТРОГО в формате JSON с ключами: "
        "'Проблема', 'Оборудование', 'Бюджет', 'Дополнительные_ограничения'. "
        "Если информации нет, пиши 'Не указано'. Выведи только валидный JSON, без блоков кода.\n\n"
        "Запрос пользователя: {request_text}\nКонтекст из файлов: {file_context}\n\n"
        "{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = get_llm(temperature=0.0)
    chain = prompt | llm | parser
    
    try:
        return chain.invoke({
            "request_text": request_text,
            "file_context": file_context[:4000],
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        logger.error(f"Agent 1 failed to parse request: {e}")
        return {
            "Проблема": request_text,
            "Оборудование": "Не указано",
            "Бюджет": "Не указано",
            "Дополнительные_ограничения": "Не указано"
        }
