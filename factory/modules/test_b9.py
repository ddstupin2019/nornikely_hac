import json
from b9_score_axes import evaluate_all_axes

def main():
    print("=== Тестирование B9: Оценщик осей ===")
    
    test_hyp = {
        "название": "Использование жидкого стекла",
        "описание": "Ввести жидкое стекло для диспергирования шламов класса -10 мкм."
    }
    
    b1_mock = {
        "классы": [
            {"класс": "+71", "никель_извлекаемый_т": 2100},
            {"класс": "-10", "никель_извлекаемый_т": 1500, "медь_извлекаемый_т": 300}
        ]
    }
    
    print("\nОцениваемая гипотеза:")
    print(test_hyp["описание"])
    
    print("\nЗапуск оценки осей (Новизна, Ценность, Риски)...")
    result = evaluate_all_axes(test_hyp, b1_mock)
    
    print("\nРезультат:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
