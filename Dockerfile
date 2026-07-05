# Используем официальный легковесный образ Python
FROM python:3.10-slim

# Установка системных зависимостей (Tesseract OCR и языковые пакеты)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории в контейнере
WORKDIR /app

# Копирование файла зависимостей
COPY my_solution_v1/requirements.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего исходного кода в контейнер
# (Исключения прописаны в .dockerignore, поэтому venv и тяжелые исходники не попадут)
COPY . .

# Прописываем путь к Tesseract (Linux default)
ENV TESSERACT_CMD=/usr/bin/tesseract

# Устанавливаем переменные окружения, чтобы Python не буферизовал вывод (полезно для логов)
ENV PYTHONUNBUFFERED=1

# Открываем порт 8000 для доступа
EXPOSE 8000

# Запуск FastAPI через Uvicorn (без опции --reload для продакшена)
CMD ["uvicorn", "my_solution_v1.main:app", "--host", "0.0.0.0", "--port", "8000"]
