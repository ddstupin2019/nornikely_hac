def find_problematic_class(b1_data: dict) -> dict:
    """
    Finds the class with the maximum amount of extractable metal (nickel/copper)
    lost in tailings.
    """
    worst_class = None
    max_lost = 0.0
    
    for cls_data in b1_data.get("классы", []):
        ni = cls_data.get("никель_извлекаемый_т") or 0.0
        cu = cls_data.get("медь_извлекаемый_т") or 0.0
        total_lost = ni + cu
        
        if total_lost > max_lost:
            max_lost = total_lost
            worst_class = cls_data
            
    return worst_class

def build_prompt(user_request: str, b1_data: dict, b3_chunks: list, b4_constraints: dict) -> str:
    """
    Builds the final prompt for the LLM based on all the collected data.
    """
    problem = find_problematic_class(b1_data)
    
    prompt = f"Ты опытный инженер-обогатитель и металлург.\n\n"
    prompt += f"ЗАДАЧА ОТ ПОЛЬЗОВАТЕЛЯ:\n{user_request}\n\n"
    
    if problem:
        cls_name = problem['класс']
        ni_lost = problem.get('никель_извлекаемый_т', 0)
        cu_lost = problem.get('медь_извлекаемый_т', 0)
        prompt += f"ПРОБЛЕМА ПО ДАННЫМ ОТЧЕТА:\n"
        prompt += f"Основная потеря извлекаемого металла происходит в классе {cls_name}.\n"
        prompt += f"Потеряно: {ni_lost} т никеля и {cu_lost} т меди (которые можно было извлечь).\n"
        prompt += f"Твоя задача — предложить гипотезы, как снизить потери ИМЕННО в этом классе.\n\n"
    
    prompt += f"ОГРАНИЧЕНИЯ (ОБОРУДОВАНИЕ И РЕСУРСЫ):\n"
    prompt += f"Доступное оборудование: {', '.join(b4_constraints.get('доступное_оборудование', []))}\n"
    prompt += f"Бюджет: {b4_constraints.get('бюджет', 'Не указан')}\n"
    prompt += f"Сроки: {b4_constraints.get('сроки', 'Не указаны')}\n"
    prompt += f"Предлагай ТОЛЬКО реализуемые гипотезы, используя доступное оборудование.\n\n"
    
    if b3_chunks:
        prompt += f"БАЗА ЗНАНИЙ (Справочная информация из книг и статей):\n"
        for i, chunk in enumerate(b3_chunks):
            prompt += f"--- Источник {i+1} ({chunk.get('книга')} стр. {chunk.get('стр')}) ---\n"
            prompt += f"{chunk.get('текст')}\n"
        prompt += "\nИспользуй эти знания для теоретического обоснования своих предложений.\n\n"
    
    prompt += "ПРИМЕРЫ ХОРОШИХ ГИПОТЕЗ:\n"
    prompt += "1. «Уменьшить размер ячейки сита классификатора с 2 мм до 1 мм, чтобы доизмельчить сростки пентландита в классе +71».\n"
    prompt += "2. «Заменить реагент собиратель на бутиловый ксантогенат для повышения селективности в тонком классе -10 мкм».\n"
    prompt += "3. «Добавить операцию доизмельчения хвостов флотации в бисерной мельнице».\n\n"
    
    prompt += "ОЖИДАЕМЫЙ ФОРМАТ ОТВЕТА:\n"
    prompt += "Выдай ответ в формате JSON:\n"
    prompt += '{\n  "название": "...",\n  "описание": "...",\n  "обоснование": "..."\n}'
    
    return prompt

if __name__ == "__main__":
    import json
    # Mock data to test
    b1_mock = {
        "классы": [
            {"класс": "+71", "никель_извлекаемый_т": 2100},
            {"класс": "-10", "никель_извлекаемый_т": 500}
        ]
    }
    b4_mock = {"доступное_оборудование": ["гидроциклоны", "мельницы"]}
    b3_mock = [{"текст": "Флотация крупных частиц затруднена...", "книга": "Учебник"}]
    
    out = build_prompt("Как снизить потери никеля в хвостах?", b1_mock, b3_mock, b4_mock)
    print(out)
