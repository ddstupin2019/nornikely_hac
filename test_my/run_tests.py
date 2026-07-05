import os
import json
import sys

# Добавляем родительскую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from my_solution_v1.rag.document_processor import process_document
from my_solution_v1.rag.vector_store import add_texts_to_store, get_document_count
from my_solution_v1.agents.orchestrator import run_hypothesis_pipeline
from my_solution_v1.core.logger import get_logger
import time

logger = get_logger("test_runner")

def load_all_to_rag(base_dir: str):
    count = get_document_count()
    if count > 0:
        logger.info(f"Векторная база уже содержит {count} фрагментов. Пропускаем повторную загрузку.")
        return

    logger.info(f"Загрузка всех документов из {base_dir} в RAG...")
    all_texts = []
    all_metas = []
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            logger.info(f"Обработка {file_path}")
            res = process_document(file_path)
            content = res.get("content", "")
            if content and content != "[IMAGE_FILE]":
                all_texts.append(content)
                all_metas.append({"source": file_path})
                
    if all_texts:
        add_texts_to_store(all_texts, all_metas)
        logger.info(f"Успешно загружено {len(all_texts)} документов в RAG.")
    else:
        logger.warning("Документы для RAG не найдены или пусты.")

tests = [
    {
        "name": "Пример 1. Снижение потерь на КГМК",
        "task": "Снизить потери цветных металлов (никель, медь) в отвальных хвостах флотации. Ограничения: Запрет на использование цианидов и дорогостоящих реагентов. Использовать текущее оборудование флотации, без капитального строительства.",
        "file": "exepmle/Пример 1/Хвосты КГМК.xlsx"
    },
    {
        "name": "Пример 2. Оптимизация схемы НОФ",
        "task": "Повысить извлечение ценных компонентов из вкрапленных руд Норильской обогатительной фабрики (НОФ). Ограничения: Бюджет до 5 млн руб. Запрет на полное изменение схемы измельчения (только точечные корректировки).",
        "file": "exepmle/Пример 2/Хвосты НОФ Вкр.xlsx"
    },
    {
        "name": "Пример 3. Снижение безвозвратных потерь меди на НОФ",
        "task": "Минимизация потерь меди с отвальными хвостами медной цепочки НОФ. Ограничения: Использовать стандартное оборудование. Время на проверку гипотезы в лаборатории — не более 1 месяца.",
        "file": "exepmle/Пример 3/Хвосты НОФ мед.xlsx"
    },
    {
        "name": "Пример 4. Сохранение качества концентрата ТОФ при снижении выхода хвостов",
        "task": "Уменьшить объем отвальных хвостов Талнахской обогатительной фабрики (ТОФ) без снижения качества итогового концентрата. Ограничения: Без применения токсичных депрессоров. Максимальное использование оборотной воды.",
        "file": "exepmle/Пример 4/Хвосты ТОФ_2.xlsx"
    },
    {
        "name": "Пример 5.1. Повышение предела прочности хромистой стали",
        "task": "Разработайте рекомендации по повышению предела прочности (σВ) с текущих 630–780 МПа до ≥850 МПа для хромистой стали 0.15–0.20 %C, сохранив относительное удлинение δ5 не ниже 10 %. Условные обозначения: σ₀.₂ – условный предел текучести; σВ – предел прочности при растяжении; δ₅ – относительное удлинение; ψ – относительное сужение; KCU – ударная вязкость; HB – твёрдость по Бринеллю.",
        "file": "exepmle/пример 5/Materialovedenie_2008.pdf"
    },
    {
        "name": "Пример 5.2. Повышение ударной вязкости стали",
        "task": "Повысить ударную вязкость KCU с текущих 50–80 Дж/см² до ≥120 Дж/см² для стали с 0,20 % C и σВ ≥ 750 МПа. Условные обозначения: σ₀.₂ – условный предел текучести; σВ – предел прочности при растяжении; δ₅ – относительное удлинение; KCU – ударная вязкость (работа разрушения образца с U-образным надрезом); HB – твёрдость по Бринеллю.",
        "file": "exepmle/пример 5/Materialovedenie_2008.pdf"
    },
    {
        "name": "Пример 5.3. Подбор температуры отпуска стали",
        "task": "Подберите температуру отпуска для стали 0,20 % C, 1 % Cr, чтобы получить σВ = 800 ± 30 МПа, δ5 ≥ 18 %, KCU ≥ 150 Дж/см². Условные обозначения: σ₀.₂ – условный предел текучести; σВ – предел прочности при растяжении; δ₅ – относительное удлинение; KCU – ударная вязкость; HB – твёрдость по Бринеллю.",
        "file": "exepmle/пример 5/Materialovedenie_2008.pdf"
    }
]

import concurrent.futures

def process_test(i, test, base_dir):
    logger.info(f"\n================ Запуск Теста {i}: {test['name']} ================")
    
    file_context = ""
    file_path = os.path.join(base_dir, test["file"])
    if os.path.exists(file_path):
        res = process_document(file_path)
        file_context = res.get("content", "")
        logger.info(f"Файл контекста прочитан: {test['file']} (размер: {len(file_context)} симв.)")
        
    test_start_time = time.time()
    
    try:
        final_hypotheses = run_hypothesis_pipeline(test["task"], file_context)
    except Exception as e:
        logger.error(f"Ошибка в тесте {i}: {e}")
        return
    
    elapsed_time = time.time() - test_start_time
    logger.info(f"Тест {i} завершен за {elapsed_time:.2f} сек.")
    
    out_dir = os.path.join(base_dir, "test_my")
    os.makedirs(out_dir, exist_ok=True)
    out_filename = os.path.join(out_dir, f"test_{i}.md")
    with open(out_filename, "w", encoding="utf-8") as f:
        f.write(f"# {test['name']}\n")
        f.write(f"**Задача:** {test['task']}\n\n")
        f.write(f"**Время выполнения:** {elapsed_time:.2f} сек.\n\n")
        f.write("## Топ Гипотез\n\n")
        for h in final_hypotheses:
            f.write(f"### {h.get('id', '')}: {h.get('воздействие', 'Без названия')}\n")
            f.write(f"- **Объект:** {h.get('объект')}\n")
            f.write(f"- **Параметр:** {h.get('параметр')}\n")
            f.write(f"- **Направление:** {h.get('направление')}\n")
            f.write(f"- **Генератор:** {h.get('генератор')}\n")
            f.write(f"- **Механизм:** {h.get('механизм')}\n")
            
            if "обоснование" in h and isinstance(h["обоснование"], list):
                f.write("\n**Обоснование из литературы:**\n")
                for ob in h["обоснование"]:
                    f.write(f"  - [{ob.get('источник')}, {ob.get('локация')}] {ob.get('тезис')}\n")
            elif "обоснование" in h:
                f.write(f"\n**Обоснование:** {h['обоснование']}\n")
                    
            if "оценки" in h and isinstance(h["оценки"], dict):
                f.write("\n**Детальные оценки (от 0 до 1):**\n")
                for k, v in h["оценки"].items():
                    if isinstance(v, dict):
                        score = v.get("значение", "-")
                        reason = v.get("обоснование", "")
                        f.write(f"  - **{k.capitalize()}**: {score} ({reason})\n")

            if "что_не_знаем" in h and isinstance(h["что_не_знаем"], list):
                f.write("\n**Открытые вопросы:**\n")
                for q in h["что_не_знаем"]:
                    f.write(f"  - {q}\n")
                    
            if "total_score" in h:
                f.write(f"\n**Общий балл Ранжировщика (из 40):** {h['total_score']}\n")
            if "итоговая_оценка_от_директора" in h:
                f.write(f"**Вердикт Директора:** {h['итоговая_оценка_от_директора']}\n")
                    
            f.write("\n---\n")
            
    logger.info(f"Результат сохранен в {out_filename}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    example_dir = os.path.join(base_dir, "exepmle")
    
    # 1. Подгружаем все данные в RAG
    if os.path.exists(example_dir):
        load_all_to_rag(example_dir)
    else:
        logger.error(f"Директория {example_dir} не найдена!")
        return

    # Выбираем какие тесты запускать. Вы можете изменить этот список (например, тесты 5, 6, 7).
    tests_to_run = [5, 6, 7]  # Индексы тестов, которые нужно запустить

    logger.info(f"Запускаем тесты {tests_to_run} параллельно...")
    
    # 2. Запускаем тесты параллельно
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i, test in enumerate(tests, 1):
            if i in tests_to_run:
                futures.append(executor.submit(process_test, i, test, base_dir))
                
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Test exception: {e}")

if __name__ == "__main__":
    main()
