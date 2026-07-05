import json
from b8_ground import evaluate_grounding

def main():
    print("=== Тестирование B8: Grounding-оценщик ===")
    
    test_hyp = {
        "название": "Использование жидкого стекла",
        "описание": "Ввести жидкое стекло для диспергирования шламов класса -10 мкм.",
        "механизм": "Жидкое стекло снижает силы сцепления между тонкими частицами, предотвращая их агрегацию."
    }
    
    print(f"\nОцениваемая гипотеза:\n{json.dumps(test_hyp, ensure_ascii=False, indent=2)}")
    
    print("\nЗапуск оценки обоснованности (разбиение на факты -> поиск -> entailment)...")
    result = evaluate_grounding(test_hyp)
    
    print(f"\nРезультат:")
    print(f"Обоснованность (Grounding Score): {result.get('grounding_score')}")
    print(f"Признана надежной (>= 0.5): {result.get('надежная')}")
    print("Найденные цитаты:")
    for cit in result.get('цитаты', []):
        print(f" - Факт: '{cit['утверждение']}' -> Источник: {cit['книга']}, стр. {cit['стр']}")

if __name__ == "__main__":
    main()
