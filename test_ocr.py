import os
import fitz
import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_ocr():
    # Create a dummy image
    img = Image.new('RGB', (100, 30), color = (255, 255, 255))
    try:
        text = pytesseract.image_to_string(img, lang="rus+eng")
        print("Tesseract works! Output:", text)
    except Exception as e:
        print("Tesseract error:", e)

if __name__ == "__main__":
    test_ocr()
