from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from src.api.routers import ui_router, api_router
from src.database import init_db
from pathlib import Path
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="File Analyzer Service", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


app.include_router(ui_router)
app.include_router(api_router)