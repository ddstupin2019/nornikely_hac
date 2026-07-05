import os
import json
from b1_parse_xlsx import parse_xlsx
from b3_embed_retrieve import retrieve
from b4_constraints import parse_constraints
from b5_context import build_prompt
from b6_generate import generate_ensemble

def main():
    print("=== Запуск сквозного тестирования (B1 -> B6) ===")
    
    # 1. B1 Data
    xlsx_path = "c:/Users/ddstu/Desktop/nor_hac/test/exepmle/Пример 1/Хвосты КГМК.xlsx"
    print("\n1. Извлечение данных B1...")
    b1_data = parse_xlsx(xlsx_path)
    
    # 2. B4 Constraints
    eq_path = "c:/Users/ddstu/Desktop/nor_hac/test/factory/data/equipment.json"
    print("\n2. Парсинг ограничений B4...")
    user_req = "Снизить потери извлекаемого никеля. Бюджет 50 млн руб, срок 6 месяцев."
    b4_data = parse_constraints(eq_path, user_req)
    
    # 3. B3 Retrieval
    print("\n3. Поиск знаний B3...")
    b3_chunks = retrieve("обогащение пентландита в тонких классах -10 мкм")
    if not b3_chunks:
        b3_chunks = [{"текст": "Флотация тонких шламов класса -10 мкм часто требует применения селективных собирателей или изменения гидродинамического режима флотомашин.", "книга": "Теория флотации", "стр": 120}]
        
    # 4. B5 Context
    print("\n4. Сборка промпта B5...")
    prompt = build_prompt(user_req, b1_data, b3_chunks, b4_data)
    
    print("\n--- Сгенерированный Промпт ---")
    print(prompt[:500] + "...\n[урезано для читаемости]\n")
    
    # 5. B6 Generate
    print("5. Запуск ансамбля генераторов B6 (вызов LLM API)...")
    # Используем только один генератор (0.5) для быстрого теста, чтобы не нагружать API и лимиты
    hypotheses = generate_ensemble(prompt, ensemble_configs=[0.5])
    
    print(f"\nСгенерировано {len(hypotheses)} валидных гипотез.")
    print(json.dumps(hypotheses, ensure_ascii=False, indent=2))
    
    # Сохраняем в файл для проверки
    out_path = "c:/Users/ddstu/Desktop/nor_hac/test/factory/data/b6_output_example.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(hypotheses, f, ensure_ascii=False, indent=2)
    print(f"Результат сохранен в {out_path}")

if __name__ == "__main__":
    main()
