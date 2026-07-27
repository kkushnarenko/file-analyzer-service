from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class FileNameResponse(BaseModel):
    file_names: list[str]

class FileBatchResponse(BaseModel):
    file_names: list[str]
class MarkDownloadedResponse(BaseModel):
    marked_now: int
    already_marked: int

class DownloadStatusResponse(BaseModel):
    status: Literal["idle","running", "completed", "error"]
    start_time_nsk: str | None = None
    received_names_count: int = 0
    downloaded_files_count: int = 0
    errors_messages : str | None = None

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
    file_ids : list[int] = []
    selected_at : bool = False

class FileStatsItem(BaseModel):
    filename: str
    digit_counts: dict[str, int]


class CalculateStatusResponse(BaseModel):
    total_files_analyzed : int
    overall_stats: dict[str, int]
    file_stats: list[FileStatsItem]
