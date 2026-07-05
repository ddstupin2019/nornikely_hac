import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "factory", "modules"))

from factory.modules.pdf_parser import read_pdf
from factory.modules.b3_embed_retrieve import build_index

def index_all_pdfs():
    materials_dir = os.path.join(os.path.dirname(__file__), "exepmle", "Дополнительные материалы")
    
    if not os.path.exists(materials_dir):
        print(f"Директория {materials_dir} не найдена!")
        return

    all_chunks = []
    
    for filename in os.listdir(materials_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(materials_dir, filename)
            print(f"\nОбработка файла: {filename}")
            
            # Читаем PDF, ограничивая время до 10 минут (600 секунд)
            chunks = read_pdf(pdf_path, max_time_seconds=600)
            all_chunks.extend(chunks)
            
    if all_chunks:
        print(f"\nИндексация {len(all_chunks)} чанков в RAG базу данных...")
        build_index(all_chunks)
        print("Индексация успешно завершена! Книги добавлены в RAG по умолчанию.")
    else:
        print("\nНе найдено чанков для индексации. Проверьте логи.")

if __name__ == "__main__":
    index_all_pdfs()
