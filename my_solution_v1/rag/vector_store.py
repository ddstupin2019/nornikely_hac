import os
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_core.documents import Document
from my_solution_v1.core.config import settings
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

# Global instances
_vector_store = None
_retriever = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        logger.info("Initializing ChromaDB VectorStore with SentenceTransformer embeddings...")
        
        # You can replace this with OpenAIEmbeddings if you want to use Yandex/Qwen embeddings API
        # from langchain_openai import OpenAIEmbeddings
        # embeddings = OpenAIEmbeddings(
        #     model="qwen3.6",
        #     openai_api_base=settings.LLM_API_BASE,
        #     openai_api_key=settings.API_KEY
        # )
        
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        
        _vector_store = Chroma(
            collection_name="norilsk_hackathon",
            embedding_function=embeddings,
            persist_directory=settings.CHROMA_DB_DIR
        )
    return _vector_store

def get_retriever():
    global _retriever
    if _retriever is None:
        vs = get_vector_store()
        _retriever = vs.as_retriever(search_kwargs={"k": 4})
    return _retriever

def get_document_count():
    vs = get_vector_store()
    try:
        return vs._collection.count()
    except Exception:
        return 0

from langchain_text_splitters import RecursiveCharacterTextSplitter

def add_texts_to_store(texts: List[str], metadatas: List[Dict[str, Any]] = None):
    vs = get_vector_store()
    if metadatas is None:
        metadatas = [{}] * len(texts)
        
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    
    docs = []
    for text, meta in zip(texts, metadatas):
        # Разбиваем длинный текст на чанки
        chunks = splitter.split_text(text)
        for chunk in chunks:
            docs.append(Document(page_content=chunk, metadata=meta))
        
    if docs:
        vs.add_documents(docs)
        logger.info(f"Added {len(docs)} document chunks to ChromaDB.")
