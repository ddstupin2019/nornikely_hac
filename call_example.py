import json
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "factory", "modules"))
from b12_api import generate_hypotheses, GenerateRequest

def main():
    req = GenerateRequest(
        kpi_goal="Снизить потери цветных металлов (никель, медь) в отвальных хвостах флотации",
        constraints_text="Запрет на использование цианидов и дорогостоящих реагентов. Использовать текущее оборудование флотации, без капитального строительства.",
        xlsx_path="c:/Users/ddstu/Desktop/nor_hac/test/exepmle/Пример 1/Хвосты КГМК.xlsx",
        equipment_json_path="factory/data/equipment.json"
    )
    
    print("Локальный вызов generate_hypotheses()...")
    start = time.time()
    try:
        data = generate_hypotheses(req)
        print(f"Ответ получен за {time.time() - start:.1f} сек.")
        print("=== СГЕНЕРИРОВАННЫЕ ГИПОТЕЗЫ (ОТВЕТЫ) ===")
        
        for i, hyp in enumerate(data.get("top_hypotheses", [])):
            print(f"\n--- Гипотеза {i+1} ---")
            print(f"Название: {hyp.get('название')}")
            print(f"Описание: {hyp.get('описание')}")
            print(f"Механизм: {hyp.get('механизм')}")
            print(f"Оценка Обоснованности: {hyp.get('grounding_score')}")
            print(f"Ценность: {hyp.get('потенциальная_ценность_тонн', 0):.1f} тонн ({hyp.get('обоснование_ценности')})")
            print(f"Новизна: {hyp.get('score')} ({hyp.get('аналог')})")
            print(f"Технический риск: {hyp.get('риск_технический')}")
            print(f"Экономический риск: {hyp.get('риск_экономический')}")
            print("Цитаты (Grounding):")
            for cit in hyp.get("цитаты", []):
                print(f"  - {cit['утверждение']} -> {cit['книга']} (стр. {cit['стр']})")
                
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
