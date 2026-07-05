import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

from my_solution_v1.core.logger import get_logger
from my_solution_v1.rag.document_processor import process_document
# (Import removed)
from my_solution_v1.rag.vector_store import add_texts_to_store
from my_solution_v1.agents.orchestrator import run_hypothesis_pipeline

logger = get_logger(__name__)
router = APIRouter()

# Simple in-memory store for task results
task_results = {}

class HypothesisRequest(BaseModel):
    task_description: str

@router.get("/status")
def get_status():
    return {"status": "ok"}

@router.post("/upload_knowledge")
async def upload_knowledge(files: List[UploadFile] = File(...)):
    """Uploads files to the RAG knowledge base."""
    upload_dir = "my_solution_v1/temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    processed_count = 0
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process document
        doc_info = process_document(file_path)
        content = doc_info["content"]
        
        # process_document now directly parses images using OCR, no need for describe_image.
            
        if content:
            add_texts_to_store(
                texts=[content], 
                metadatas=[{"source": file.filename}]
            )
            processed_count += 1
            
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
            
    return {"message": f"Successfully processed and indexed {processed_count} files."}

def run_pipeline_bg(task_id: str, raw_text: str, file_context: str):
    def update_stage(stage: int, desc: str):
        task_results[task_id]["stage"] = stage
        task_results[task_id]["stage_desc"] = desc
        
    try:
        task_results[task_id]["stage"] = 0
        task_results[task_id]["stage_desc"] = "Инициализация"
        results = run_hypothesis_pipeline(raw_text, file_context, progress_callback=update_stage)
        
        # Save to Markdown
        out_dir = os.path.join(os.getcwd(), "test_my")
        os.makedirs(out_dir, exist_ok=True)
        out_filename = os.path.join(out_dir, f"ui_result_{task_id[:8]}.md")
        
        with open(out_filename, "w", encoding="utf-8") as f:
            f.write(f"# Результат из веб-интерфейса\n")
            f.write(f"**Задача:** {raw_text}\n\n")
            f.write("## Топ Гипотез\n\n")
            for h in results:
                title = h.get("название") or h.get("воздействие", "Без названия")
                f.write(f"### {h.get('id', '')}: {title}\n")
                f.write(f"- **Объект:** {h.get('объект')}\n")
                f.write(f"- **Параметр:** {h.get('параметр')}\n")
                f.write(f"- **Направление:** {h.get('направление')}\n")
                f.write(f"- **Генератор:** {h.get('генератор')}\n")
                f.write(f"- **Механизм:** {h.get('механизм')}\n")
                
                if "обоснование" in h and isinstance(h["обоснование"], list):
                    f.write("\n**Обоснование из литературы:**\n")
                    for ob in h["обоснование"]:
                        f.write(f"  - [{ob.get('источник')}, {ob.get('локация')}] {ob.get('тезис')}\n")
                elif "обоснование" in h:
                    f.write(f"\n**Обоснование:** {h['обоснование']}\n")
                        
                if "оценки" in h and isinstance(h["оценки"], dict):
                    f.write("\n**Детальные оценки (от 0 до 1):**\n")
                    for k, v in h["оценки"].items():
                        if isinstance(v, dict):
                            score = v.get("значение", "-")
                            reason = v.get("обоснование", "")
                            f.write(f"  - **{k.capitalize()}**: {score} ({reason})\n")

                if "что_не_знаем" in h and isinstance(h["что_не_знаем"], list):
                    f.write("\n**Открытые вопросы:**\n")
                    for q in h["что_не_знаем"]:
                        f.write(f"  - {q}\n")
                        
                if "total_score" in h:
                    f.write(f"\n**Общий балл Ранжировщика (из 40):** {h['total_score']}\n")
                if "итоговая_оценка_от_директора" in h:
                    f.write(f"**Вердикт Директора:** {h['итоговая_оценка_от_директора']}\n")
                        
                f.write("\n---\n")
        logger.info(f"UI result saved to {out_filename}")

        task_results[task_id]["status"] = "completed"
        task_results[task_id]["data"] = results
        task_results[task_id]["stage"] = 6
        task_results[task_id]["stage_desc"] = f"Готово. Сохранено в {os.path.basename(out_filename)}"
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        task_results[task_id] = {"status": "failed", "error": str(e), "stage": -1, "stage_desc": "Ошибка выполнения"}

@router.post("/generate_hypotheses")
async def generate_hypotheses_api(
    background_tasks: BackgroundTasks,
    task_description: str = Form(...),
    files: List[UploadFile] = File(None)
):
    """Starts the hypothesis generation pipeline."""
    import uuid
    task_id = str(uuid.uuid4())
    task_results[task_id] = {"status": "processing"}
    
    file_context = ""
    # Process attached files immediately to extract text for this specific task
    if files:
        upload_dir = f"my_solution_v1/temp_uploads/{task_id}"
        os.makedirs(upload_dir, exist_ok=True)
        for file in files:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            doc_info = process_document(file_path)
            content = doc_info["content"]
            if not content:
                logger.warning(f"File {file.filename} is empty.")
            
            file_context += f"Файл {file.filename}:\n{content}\n\n"
    
    background_tasks.add_task(run_pipeline_bg, task_id, task_description, file_context)
    
    return {"task_id": task_id, "message": "Pipeline started"}

@router.get("/result/{task_id}")
def get_result(task_id: str):
    """Retrieves the result of a hypothesis generation task."""
    result = task_results.get(task_id)
    if not result:
        return {"status": "not_found"}
    return result
