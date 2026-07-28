from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, computed_field


class FileNameResponse(BaseModel):
    file_names: list[str]


class FileBatchResponse(BaseModel):
    file_names: list[str]


class MarkDownloadedResponse(BaseModel):
    marked_now: int
    already_marked: int


class DownloadStatusResponse(BaseModel):
    status: Literal["idle", "running", "completed", "error"] = "idle"
    started_at_nsk: str | None = Field(default=None, alias="start_time_nsk")
    total_names: int = Field(default=0, alias="received_names_count")
    downloaded_count: int = Field(default=0, alias="downloaded_files_count")
    errors_messages: str | None = None

    @computed_field
    @property
    def is_active(self) -> bool:
        return self.status == "running"

    @computed_field
    @property
    def message(self) -> str:
        if self.status == "running":
            return "Скачивание выполняется..."
        if self.status == "completed":
            return "Завершено"
        if self.status == "error":
            return self.errors_messages or "Произошла ошибка"
        return "Ожидание"

    class Config:
        populate_by_name = True


class FileRead(BaseModel):
    id: int
    file_name: str
    downloaded_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: list[FileRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class CalculateStatusRequest(BaseModel):
    file_ids: list[int] = []
    selected_at: bool = False


class FileStatsItem(BaseModel):
    filename: str
    digit_counts: dict[str, int]


class CalculateStatusResponse(BaseModel):
    total_files_analyzed: int
    overall_stats: dict[str, int]
    file_stats: list[FileStatsItem]