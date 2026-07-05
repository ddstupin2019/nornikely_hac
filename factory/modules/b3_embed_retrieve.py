import os
import json
import math
from collections import Counter

# MOCK DB PATH
DB_PATH = "factory/data/mock_db.json"

def build_index(chunks: list, db_path: str = DB_PATH, collection_name: str = "science_docs"):
    """
    Builds a simple TF-IDF based index for the demo to avoid heavy pip dependencies 
    like ChromaDB or PyTorch which fail to build locally on this machine.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Load existing or create new
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = []
        
    db.extend(chunks)
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        
    print(f"Index built/updated at {db_path} with {len(chunks)} new chunks. Total: {len(db)}")

def retrieve(query: str, k: int = 5, db_path: str = DB_PATH, collection_name: str = "science_docs") -> list:
    if not os.path.exists(db_path):
        print("DB not found.")
        return []
        
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    if not db:
        return []
        
    # Simple TF-IDF scoring for the query
    query_words = set(query.lower().split())
    
    scored_chunks = []
    for chunk in db:
        text = chunk["текст"].lower()
        score = 0.0
        for qw in query_words:
            if len(qw) > 3 and qw in text:
                score += 1.0 # Simple term frequency
        scored_chunks.append((score, chunk))
        
    # Sort by score descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for score, chunk in scored_chunks[:k]:
        results.append({
            "chunk_id": chunk["chunk_id"],
            "текст": chunk["текст"],
            "книга": chunk.get("книга", "unknown"),
            "стр": chunk.get("стр", 0),
            "score": score
        })
        
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        q = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "флотация"
        res = retrieve(q)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("Usage: python b3_embed_retrieve.py search <query>")
