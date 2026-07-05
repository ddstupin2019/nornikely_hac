import os
import json
from b2_parse_docs import parse_docs
from b3_embed_retrieve import build_index, retrieve

def main():
    pdf_path = "c:/Users/ddstu/Desktop/nor_hac/test/exepmle/Дополнительные материалы/geokniga-flotacionnye-metody-obogashcheniya_0.pdf"
    print("1. Parsing docs...")
    chunks = parse_docs(pdf_path)
    print(f"Total chunks: {len(chunks)}")
    
    # Take first 50 chunks for a quick test so embedding doesn't take forever locally
    test_chunks = chunks[:50]
    
    print("2. Building index (first 50 chunks)...")
    build_index(test_chunks)
    
    print("3. Querying...")
    results = retrieve("что такое флотация?", k=3)
    
    print("4. Results:")
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
