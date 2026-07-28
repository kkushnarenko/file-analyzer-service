import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from src.config import settings
from src.database import get_db, AsyncSessionLocal
from src.services.downloader import file_download_service

router = APIRouter(prefix="/downloader", tags=["Downloader"])

@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_download_pipeline(background_tasks: BackgroundTasks,
                                  db: AsyncSession = Depends(get_db)):
    if file_download_service.status == "running":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File already downloaded")

    async def run_in_background():
        async with AsyncSessionLocal() as db_session:
            async with httpx.AsyncClient(base_url=settings.EXTERNAL_API_BASE_URL) as client:
                await file_download_service.run_download_pipeline(db=db_session, client=client)

    return {"message": "Пайплайн скачивания успешно запущен в фоновом режиме.",
        "status": file_download_service.status}

@router.get("/status")
async def status():
    return file_download_service.get_status()