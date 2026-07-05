import os
import time
import uuid

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
    from pdf2image import convert_from_path
except ImportError:
    pytesseract = None
    convert_from_path = None

def chunk_text(text: str, chunk_size: int = 500) -> list:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def read_pdf(path: str, max_time_seconds: int = 600) -> list:
    """
    Читает PDF, извлекая текст. Если страница не содержит текста (скан),
    пытается использовать OCR. Ограничивает время работы.
    Возвращает список чанков.
    """
    start_time = time.time()
    chunks = []
    filename = os.path.basename(path)

    if not fitz:
        print(f"[{filename}] PyMuPDF (fitz) не установлен! Невозможно прочитать PDF.")
        return chunks

    print(f"[{filename}] Начинаем парсинг...")
    try:
        doc = fitz.open(path)
    except Exception as e:
        print(f"[{filename}] Ошибка открытия файла: {e}")
        return chunks

    for i, page in enumerate(doc):
        # Проверяем лимит времени
        if time.time() - start_time > max_time_seconds:
            print(f"[{filename}] Достигнут лимит времени ({max_time_seconds} с). Остановка на странице {i}.")
            break

        # Пробуем достать текстовый слой
        text = page.get_text().strip()
        
        # Если текста мало, предполагаем, что это скан без OCR слоя
        if len(text) < 50:
            if pytesseract and convert_from_path:
                try:
                    # Конвертируем только текущую страницу
                    images = convert_from_path(path, first_page=i+1, last_page=i+1)
                    if images:
                        text = pytesseract.image_to_string(images[0], lang='rus+eng')
                except Exception as e:
                    # Tesseract может быть не установлен
                    pass
        
        if text:
            page_chunks = chunk_text(text)
            for c in page_chunks:
                if len(c) > 30: # Игнорируем совсем короткие куски
                    chunks.append({
                        "chunk_id": str(uuid.uuid4()),
                        "текст": c,
                        "книга": filename,
                        "стр": i + 1
                    })
                    
    print(f"[{filename}] Завершен парсинг. Извлечено {len(chunks)} чанков за {time.time() - start_time:.1f} сек.")
    return chunks
