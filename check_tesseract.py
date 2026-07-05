import os
import sys
import subprocess

def check_tesseract():
    print("Проверка Tesseract OCR...")
    try:
        result = subprocess.run(['tesseract', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("Tesseract OCR найден в PATH!")
            print(result.stdout.strip())
            return True
    except FileNotFoundError:
        pass
    
    # Пытаемся проверить стандартные пути Windows
    standard_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]
    
    for path in standard_paths:
        if os.path.exists(path):
            print(f"Tesseract найден по пути: {path}")
            print("\nВам нужно добавить этот путь в системную переменную PATH или")
            print(f"в начале вашего скрипта добавить строку: ")
            print(f"pytesseract.pytesseract.tesseract_cmd = r'{path}'")
            return True
            
    print("\n[ВНИМАНИЕ] Tesseract OCR НЕ УСТАНОВЛЕН!")
    print("Для корректного извлечения текста из полностью отсканированных страниц (без текстового слоя) установите Tesseract OCR:")
    print("1. Скачайте инсталлятор для Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Установите его (выберите поддержку русского языка во время установки - 'Additional language data' -> 'Russian').")
    print("3. Убедитесь, что папка установки (обычно C:\\Program Files\\Tesseract-OCR) добавлена в переменную PATH, либо укажите путь явно в pdf_parser.py.")
    return False

if __name__ == "__main__":
    check_tesseract()
