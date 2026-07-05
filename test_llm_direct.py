from my_solution_v1.agents.agent_2_generator import generate_hypotheses
import logging

logging.basicConfig(level=logging.DEBUG)

print("Running Agent 2 directly...")
try:
    task = {'Проблема': 'Снизить потери', 'Оборудование': 'флотация', 'Бюджет': '', 'Дополнительные_ограничения': ''}
    context = "Пример контекста"
    res = generate_hypotheses(task, context)
    print("Result:")
    print(res)
except Exception as e:
    print("Error:", e)
