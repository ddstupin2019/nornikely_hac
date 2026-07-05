import base64
import os
import argparse
from openai import OpenAI

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_scheme(image_path, output_path):
    # Учетные данные Yandex Cloud
    api_key = os.getenv("YANDEX_API_KEY", "")
    folder_id = os.getenv("YANDEX_FOLDER_ID", "")
    
    # URI модели DeepSeek V4 Flash в Yandex AI Studio
    # Убедитесь, что модель поддерживает работу с изображениями (Vision)
    model_uri = f"gpt://{folder_id}/deepseek-v4-flash"
    
    # Yandex AI Studio предоставляет API, совместимое с OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://ai.api.cloud.yandex.net/v1"
    )

    # Кодируем изображение
    base64_image = image_to_base64(image_path)
    
    # Определяем MIME-тип на основе расширения
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/png" if ext == ".png" else "image/jpeg"

    print(f"Отправка запроса в Yandex AI Studio (модель {model_uri})...")
    print(f"Изображение: {image_path}")
    
    try:
        response = client.chat.completions.create(
            model=model_uri,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Пожалуйста, рассмотри эту схему и подробно расскажи, что на ней изображено. Опиши основные элементы и связи между ними."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        },
                    ],
                }
            ],
            temperature=0.3,
            max_tokens=4000
        )

        message_dict = response.choices[0].message.model_dump()
        result_text = message_dict.get('content')
        reasoning_text = message_dict.get('reasoning_content')
        
        final_text = ""
        if reasoning_text:
            final_text += f"### Анализ (рассуждения модели)\n{reasoning_text}\n\n"
        if result_text:
            final_text += f"### Итоговый ответ\n{result_text}\n"

        if not final_text.strip():
            print("Внимание: API вернуло пустой текст. Ответ сохранен в файл.")
            final_text = f"API вернуло неожиданный ответ:\n\n```json\n{response.model_dump_json(indent=2)}\n```"

        # Сохраняем результат в markdown файл
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Результат анализа схемы\n\n")
            f.write(f"**Исходный файл:** `{image_path}`\n\n")
            f.write("## Описание\n\n")
            f.write(final_text)
            
        print(f"\nУспешно! Ответ сохранен в файл: {output_path}")

    except Exception as e:
        print(f"\nПроизошла ошибка при обращении к API: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Анализ схемы через Yandex AI Studio (DeepSeek V4 Flash)")
    parser.add_argument("image_path", help="Путь к изображению со схемой (например, scheme.jpg или scheme.png)")
    parser.add_argument("--output", "-o", default="scheme_analysis.md", help="Путь к выходному файлу .md (по умолчанию scheme_analysis.md)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Ошибка: Файл '{args.image_path}' не найден.")
        exit(1)
        
    analyze_scheme(args.image_path, args.output)
