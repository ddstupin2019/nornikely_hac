import sys
import json
import asyncio
from my_solution_v1.agents.agent_5_formatter import format_hypothesis
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

dummy_hyp = {
    "id": "temp_0",
    "название": "Тестовая гипотеза об изменении расхода",
    "механизм": "Увеличение расхода собирателя на 10% позволит поднять извлечение меди, так как реагент лучше закрепится на минерале.",
    "описание": "Предлагается подавать больше собирателя.",
    "обоснование": "В контексте описано, что собиратель работает.",
    "источники": ["Materialovedenie_2008.pdf"]
}

dummy_task = {
    "Проблема": "Снижение потерь",
    "Оборудование": "Стандартное",
    "Бюджет": "Без бюджета",
    "Дополнительные_ограничения": "Нет"
}

print("Testing Agent 5 with DeepSeek...")
try:
    res = format_hypothesis(dummy_hyp, dummy_task, file_context="Пустой контекст")
    print("\n--- RESULT ---")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
