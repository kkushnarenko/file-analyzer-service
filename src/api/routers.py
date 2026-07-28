import asyncio
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Query, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from src.models import DownloadProgress
from src.services.analyzer import FileAnalyzerService

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
async def get_download_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DownloadProgress).order_by(DownloadProgress.id.desc())
    )
    progress = result.scalars().first()

    if not progress:
        return {
            "status": "idle",
            "started_at_nsk": "-",
            "total_names_count": 0,
            "downloaded_files_count": 0,
            "is_active": False,
            "status_message": "Готов к запуску"
        }

    return {
        "status": "running" if progress.is_active else "completed",
        "started_at_nsk": progress.started_at_nsk,
        "total_names_count": progress.total_names_count,
        "downloaded_files_count": progress.downloaded_count,
        "is_active": progress.is_active,
        "status_message": progress.status_message
    }


@api_router.get("/files", response_model=PaginatedResponse)  # Добавлен слэш
async def get_files(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
):
    analyzer = FileAnalyzerService(db)
    return await analyzer.get_files_paginated(page=page, page_size=page_size)


@api_router.post("/files/calculate", response_model=CalculateStatusResponse)
async def calculate_stats(
    payload: CalculateStatusRequest,
    db: AsyncSession = Depends(get_db)
):
    analyzer = FileAnalyzerService(db)
    file_ids = getattr(payload, "file_ids", None)
    select_all = getattr(payload, "select_all", False)

    return await analyzer.calculate_stats(file_ids=file_ids, select_all=select_all)