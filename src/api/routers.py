import asyncio
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Query, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.api.dependencies import get_db
from src.schemas import (
    CalculateStatusRequest, 
    CalculateStatusResponse, 
    DownloadStatusResponse, 
    PaginatedResponse,
)
from src.services.downloader import file_download_service
from src.database import AsyncSessionLocal

ui_router = APIRouter()
api_router = APIRouter(prefix="/api", tags=["API"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")



@ui_router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="base.html")


@ui_router.get("/download", response_class=HTMLResponse)
async def download_page(request: Request):
    return templates.TemplateResponse(request=request, name="download.html")


@ui_router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    return templates.TemplateResponse(request=request, name="files.html")



async def _run_download_in_background():
    async with AsyncSessionLocal() as db_session:
        # Передаем внешний URL из конфига!
        async with httpx.AsyncClient(
            base_url=settings.EXTERNAL_API_BASE_URL,
            timeout=30.0,
        ) as client:
            await file_download_service.run_download_pipeline(db=db_session, client=client)


@api_router.post("/download/start", status_code=status.HTTP_202_ACCEPTED)
async def start_download(background_tasks: BackgroundTasks):
    if file_download_service.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Процесс скачивания уже запущен."
        )

    background_tasks.add_task(_run_download_in_background)

    return {
        "message": "Пайплайн скачивания успешно запущен.",
        "status": file_download_service.status,
    }


@api_router.get("/download/status", response_model=DownloadStatusResponse)
async def get_download_status():
    return file_download_service.get_current_status()


@api_router.get("/files", response_model=PaginatedResponse)  # Добавлен слэш
async def get_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # TODO: Реализовать получение списка файлов из БД с пагинацией
    pass


@api_router.post("/files/calculate", response_model=CalculateStatusResponse)  # Добавлен слэш
async def calculate_stats(
    payload: CalculateStatusRequest, 
    db: AsyncSession = Depends(get_db)
):
    # TODO: Реализовать подсчет статистики по файлам
    pass