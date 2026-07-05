import fitz
import sys

pdf_path = r"c:\Users\ddstu\Desktop\nor_hac\test\exepmle\пример 5\Materialovedenie_2008.pdf"

try:
    doc = fitz.open(pdf_path)
    # the page index in fitz is 0-based. But the page numbers might be offset by the PDF structure.
    # usually people refer to printed page numbers, let's just get the text from the 0-based index first.
    pages_to_check = [629, 630, 631, 634, 635]
    for p in pages_to_check:
        # trying p-1 to account for 1-based to 0-based index, but just to be safe, I'll print both if needed.
        # Let's assume the citation is the physical printed page or pdf logical page. Let's do pdf index p and p-1.
        page = doc.load_page(p - 1)
        text = page.get_text()
        print(f"--- PAGE {p} ---")
        print(text[:1000]) # print first 1000 chars to see context
        print("...")
except Exception as e:
    print("Error:", e)
