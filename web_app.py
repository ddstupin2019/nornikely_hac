import streamlit as st
import os
import tempfile
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from my_solution_v1.rag.document_processor import process_document
from my_solution_v1.rag.vector_store import add_texts_to_store, get_retriever

st.set_page_config(page_title="RAG Web UI", layout="wide")

st.title("📚 Управление литературой для RAG (Hypothesis Factory)")

# Section 1: Upload new documents
st.header("Загрузить новую литературу")
uploaded_file = st.file_uploader("Выберите файл (PDF, DOCX, XLSX)", type=["pdf", "docx", "xlsx"])

if uploaded_file is not None:
    if st.button("Обработать и добавить в RAG"):
        with st.spinner("Обработка документа..."):
            # Save uploaded file to temp file
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
                
            try:
                res = process_document(tmp_path)
                content = res.get("content", "")
                if content and content != "[IMAGE_FILE]":
                    add_texts_to_store([content], [{"source": uploaded_file.name}])
                    st.success(f"Файл '{uploaded_file.name}' успешно добавлен в базу знаний!")
                else:
                    st.warning("Не удалось извлечь текст из файла или он пуст.")
            except Exception as e:
                st.error(f"Ошибка при обработке файла: {e}")
            finally:
                os.unlink(tmp_path)

st.markdown("---")

# Section 2: View Document / RAG search
st.header("🔍 Поиск по базе знаний (Чтение сканов)")
search_query = st.text_input("Введите запрос для поиска по текстам книг и статей:")

if search_query:
    retriever = get_retriever()
    if retriever:
        docs = retriever.invoke(search_query)
        if docs:
            st.subheader(f"Найдено {len(docs)} фрагментов:")
            for i, doc in enumerate(docs):
                with st.expander(f"📖 Фрагмент {i+1} (Источник: {doc.metadata.get('source', 'Неизвестно')})"):
                    st.text_area("Текст из скана/книги:", value=doc.page_content, height=200, disabled=True)
        else:
            st.info("По данному запросу ничего не найдено.")
    else:
        st.warning("Векторная база не инициализирована.")
