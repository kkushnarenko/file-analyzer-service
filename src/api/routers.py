from pathlib import Path
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.schemas import CalculateStatusRequest, PaginatedResponse, DownloadStatusResponse, CalculateStatusResponse

ui_router = APIRouter()

api_router = APIRouter(prefix="/api", tags=["API"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR /"templates")


@ui_router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="base.html")

@ui_router.get("/download", response_class=HTMLResponse)
async def download_page(request: Request):
    return templates.TemplateResponse(request=request, name="download.html")

@ui_router.get("/files", response_class=HTMLResponse)
async def download_page(request: Request):
    return templates.TemplateResponse(request=request, name="files.html")


@api_router.post("/download/start", response_model=PaginatedResponse)
async def start_download(db: AsyncSession = Depends(get_db)):
    pass

@api_router.get("/download/status", response_model=DownloadStatusResponse)
async def get_download_status(db: AsyncSession = Depends(get_db)):
    pass

@api_router.get("files", response_model=PaginatedResponse)
async def get_files(page : int = Query(1, ge=1),
                    page_size: int = Query(10, ge=1, le=100),
                    db: AsyncSession = Depends(get_db)):
    pass

@api_router.post("files/calculate", response_model=CalculateStatusResponse)
async def calculate_stats(payload: CalculateStatusRequest, db: AsyncSession = Depends(get_db)):
    pass
