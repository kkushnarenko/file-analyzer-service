from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import init_db
from pathlib import Path
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="File Analyzer Service", lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent

# Подключаем папку static, которая находится внутри src/
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")