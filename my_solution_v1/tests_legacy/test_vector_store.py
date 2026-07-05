from my_solution_v1.rag.vector_store import VectorStore

def test_vector_store_add_and_search():
    vs = VectorStore()
    
    vs.add_texts(["Текст 1", "Текст 2"], [{"source": "doc1"}, {"source": "doc2"}])
    
    assert len(vs.documents) == 2
    
    docs = vs.similarity_search("Запрос", k=1)
    assert len(docs) == 1
    assert docs[0].page_content == "Текст 1"
