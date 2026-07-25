from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.database import init_db
from pathlib import Path
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="File Analyzer Service", lifespan=lifespan)
templates = Jinja2Templates(directory=BASE_DIR /"templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="base.html")
@app.get("/download", response_class=HTMLResponse)
async def download_page(request: Request):
    return templates.TemplateResponse(request=request, name="download.html")

@app.get("/files", response_class=HTMLResponse)
async def download_page(request: Request):
    return templates.TemplateResponse(request=request, name="files.html")