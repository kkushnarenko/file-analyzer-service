from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Column, Integer, DateTime, Text

class Base(DeclarativeBase):
    pass

class DownloadFile(Base):
    __tablename__ = 'download_file'
    id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    content : Mapped[str] = mapped_column(Text)
    downloaded_at : Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class DownloadProgress(Base):
    __tablename__ = 'download_progress'
    id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at_nsk: Mapped[str] = mapped_column(String)
    total_names_count: Mapped[int] = mapped_column(Integer, default=0)
    downloaded_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    status_message: Mapped[str] = mapped_column(String, default="Инициализация...")