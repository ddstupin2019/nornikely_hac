import json
from b10_filter import filter_hypotheses
from b11_rank import rank_hypotheses

def main():
    print("=== Тестирование B10 (Фильтр) и B11 (Ранжировщик) ===")
    
    test_hyps = [
        {
            "название": "Хорошая гипотеза",
            "score": 1.0,
            "grounding_score": 0.8,
            "потенциальная_ценность_тонн": 1500,
            "риск_технический": "Низкий",
            "риск_экономический": "Средний"
        },
        {
            "название": "Мусорная гипотеза (известное)",
            "score": 0.0,
            "grounding_score": 0.9,
            "потенциальная_ценность_тонн": 500,
            "риск_технический": "Низкий"
        },
        {
            "название": "Слабо обоснованная гипотеза",
            "score": 0.5,
            "grounding_score": 0.2, # < 0.5 -> отсев
            "потенциальная_ценность_тонн": 3000
        },
        {
            "название": "Средняя гипотеза",
            "score": 0.5,
            "grounding_score": 0.6,
            "потенциальная_ценность_тонн": 800,
            "риск_технический": "Высокий риск поломки" # штраф за риск
        }
    ]
    
    print("\n1. ОТСЕВ (B10):")
    passed = filter_hypotheses(test_hyps)
    print(f"Осталось гипотез: {len(passed)} из {len(test_hyps)}")
    
    print("\n2. РАНЖИРОВАНИЕ (B11):")
    ranked = rank_hypotheses(passed)
    for i, h in enumerate(ranked):
        print(f"{i+1}. {h['название']} | Ранг: {h['final_rank_score']} | Обоснованность: {h['grounding_score']} | Ценность: {h['потенциальная_ценность_тонн']} т (норм: {h['norm_value']})")

if __name__ == "__main__":
    main()
