import os
import json
import uuid
from pypdf import PdfReader
from langdetect import detect

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        if lang in ['ru', 'en', 'zh-cn', 'zh-tw']:
            return lang[:2] if lang.startswith('zh') else lang
        return lang
    except:
        return 'ru' # Default fallback

def parse_pdf(filepath: str) -> list:
    results = []
    try:
        reader = PdfReader(filepath)
    except Exception as e:
        print(f"Failed to read PDF {filepath}: {e}")
        return results
        
    book_name = os.path.basename(filepath)
    
    # Approximate tokens using words (1 token ~ 0.75 words, so 600 words ~ 800 tokens)
    CHUNK_WORDS = 600
    OVERLAP_WORDS = 75
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
            
        text = text.strip()
        if not text:
            continue
            
        words = text.split()
        
        # Split words into chunks
        start = 0
        while start < len(words):
            end = start + CHUNK_WORDS
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "текст": chunk_text.strip(),
                "книга": book_name,
                "стр": page_num + 1,
                "язык": detect_language(chunk_text)
            }
            results.append(chunk)
            
            # Move forward by chunk size minus overlap
            start += (CHUNK_WORDS - OVERLAP_WORDS)
            
    return results

def parse_docs(path: str) -> list:
    all_chunks = []
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file.lower().endswith(".pdf"):
                all_chunks.extend(parse_pdf(os.path.join(path, file)))
    elif path.lower().endswith(".pdf"):
        all_chunks.extend(parse_pdf(path))
    return all_chunks

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python b2_parse_docs.py <path_to_pdf_or_folder>")
        sys.exit(1)
        
    chunks = parse_docs(sys.argv[1])
    print(f"Total chunks extracted: {len(chunks)}")
    if chunks:
        print(json.dumps(chunks[:3], ensure_ascii=False, indent=2))
