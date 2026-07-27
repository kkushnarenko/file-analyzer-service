from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "File Analyzer Service"
    DEBUG: bool = True
    DATABASE_URI: str = "sqlite+aiosqlite:///./src.db"

    EXTERNAL_API_BASE_URL: str
    CANDIDATE_ID : str = "123"
    MAX_FILES_PER_DOWNLOAD_BATCH: int = 3
    ADMIN_TOKEN: str | None = None

    STORAGE_DIR: str | Path = Path(__file__).resolve().parent / "storage"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)