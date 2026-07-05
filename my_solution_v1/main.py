import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from my_solution_v1.api.routes import router as api_router
from my_solution_v1.core.config import settings
from my_solution_v1.core.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Система генерации и приоритизации научных гипотез",
    version="1.0.0",
)

# Ensure templates and static directories exist
os.makedirs("my_solution_v1/static", exist_ok=True)
os.makedirs("my_solution_v1/templates", exist_ok=True)

# Mounting static files and setting up templates
app.mount("/static", StaticFiles(directory="my_solution_v1/static"), name="static")
templates = Jinja2Templates(directory="my_solution_v1/templates")

# Include API Router
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting application...")
    uvicorn.run("my_solution_v1.main:app", host="0.0.0.0", port=8000, reload=True)
