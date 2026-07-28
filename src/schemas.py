from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, computed_field, ConfigDict


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

    model_config = ConfigDict(populate_by_name=True)


class FileRead(BaseModel):
    id: int
    file_name: str
    downloaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    items: list[FileRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class CalculateStatusRequest(BaseModel):
    file_ids: list[int] = []
    select_all: bool = Field(default=False, validation_alias="selected_at")

    model_config = ConfigDict(populate_by_name=True)


class FileStatsItem(BaseModel):
    id: int
    filename: str = Field(validation_alias="name")
    digit_counts: dict[str, int] = Field(validation_alias="digits")

    model_config = ConfigDict(populate_by_name=True)


class CalculateStatusResponse(BaseModel):
    selected_count: int = Field(validation_alias="total_files_analyzed")
    total_stats: dict[str, int] = Field(validation_alias="overall_stats")
    files_stats: list[FileStatsItem] = Field(validation_alias="file_stats")

    model_config = ConfigDict(
        populate_by_name=True,
        by_alias=False  
    )