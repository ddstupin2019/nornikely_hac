import os
import sys

# Добавляем родительскую директорию в PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from my_solution_v1.rag.document_processor import process_document
from my_solution_v1.rag.vector_store import add_texts_to_store, get_document_count
from my_solution_v1.core.logger import get_logger

logger = get_logger("build_rag")

def build_rag():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    example_dir = os.path.join(base_dir, "exepmle")
    
    count = get_document_count()
    if count > 0:
        logger.info(f"Векторная база уже содержит {count} фрагментов. Пропускаем.")
        return

    logger.info(f"Загрузка всех документов из {example_dir} в RAG...")
    all_texts = []
    all_metas = []
    
    for root, _, files in os.walk(example_dir):
        for file in files:
            file_path = os.path.join(root, file)
            logger.info(f"Обработка {file_path}")
            res = process_document(file_path)
            content = res.get("content", "")
            
            # Print a small preview of the content to verify tables/OCR
            if content:
                preview = content[:200].replace('\n', ' ')
                logger.info(f"Успешно извлечено {len(content)} символов. Превью: {preview}...")
                all_texts.append(content)
                all_metas.append({"source": file_path})
            else:
                logger.warning(f"Файл {file_path} оказался пустым после обработки.")
                
    if all_texts:
        add_texts_to_store(all_texts, all_metas)
        logger.info(f"Успешно загружено {len(all_texts)} документов в RAG.")
    else:
        logger.warning("Документы для RAG не найдены или пусты.")

if __name__ == "__main__":
    build_rag()
