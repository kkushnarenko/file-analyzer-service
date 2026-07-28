import asyncio
import io
import logging
import zipfile
import zoneinfo
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import DownloadFile, DownloadProgress
from src.schemas import DownloadStatusResponse

logger = logging.getLogger(__name__)

MAX_RETRY_WAIT = 60

REQUEST_DELAY = 0.5


class DownloadService:
    def __init__(self):
        self.status = "idle"
        self.start_time_nsk: str | None = None
        self.received_names_count = 0
        self.downloaded_files_count = 0
        self.error_message: str | None = None

    def get_current_status(self):
        return {
            "status": self.status,
            "start_time_nsk": self.start_time_nsk,
            "total_names_count": self.received_names_count,
            "downloaded_files_count": self.downloaded_files_count,
            "error_message": self.error_message,
        }

    async def run_download_pipeline(self, db: AsyncSession, client: httpx.AsyncClient):
        self.status = "running"
        self.error_message = None

        nsk_tz = zoneinfo.ZoneInfo("Asia/Novosibirsk")
        self.start_time_nsk = datetime.now(nsk_tz).strftime("%d.%m.%Y %H:%M:%S")

        while True:
            try:
                response = await client.get("/api/files/names")

                if response.status_code in (429, 403):
                    retry_after = int(response.headers.get("Retry-After", 5))

                    if retry_after > MAX_RETRY_WAIT:
                        msg = f"Превышен лимит (Retry-After: {retry_after} сек). Прерываем скачивание."
                        logger.error(msg)
                        self.status = "error"
                        self.error_message = msg
                        break

                    logger.warning(f"Превышен лимит запросов. Ждем {retry_after} сек...")
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                file_names: list[str] = data.get("file_names", [])

                if not file_names:
                    self.status = "completed"
                    break

                self.received_names_count += len(file_names)

                batch_size = min(settings.MAX_FILES_PER_DOWNLOAD_BATCH, 3)

                for i in range(0, len(file_names), batch_size):
                    batch = file_names[i: i + batch_size]

                    await asyncio.sleep(REQUEST_DELAY)

                    dl_response = await client.post(
                        "/api/files/download",
                        json={"file_names": batch}
                    )

                    if dl_response.status_code in (429, 403):
                        retry_after = int(dl_response.headers.get("Retry-After", 5))

                        if retry_after > MAX_RETRY_WAIT:
                            msg = f"Сервер заблокировал скачивание на {retry_after} сек."
                            logger.error(msg)
                            self.status = "error"  # Заменено "failed" -> "error" для валидации Pydantic
                            self.error_message = msg
                            return

                        logger.warning(f"Превышен лимит скачивания. Ждем {retry_after} сек...")
                        await asyncio.sleep(retry_after)

                        dl_response = await client.post(
                            "/api/files/download",
                            json={"file_names": batch}
                        )

                    dl_response.raise_for_status()

                    with zipfile.ZipFile(io.BytesIO(dl_response.content)) as zf:
                        for filename in zf.namelist():
                            file_content = zf.read(filename).decode("utf-8").strip()

                            file_path = settings.STORAGE_DIR / filename
                            file_path.write_text(file_content, encoding="utf-8")

                            new_file = DownloadFile(
                                name=filename,
                                content=file_content,
                                downloaded_at=datetime.now(timezone.utc)
                            )
                            db.add(new_file)
                            self.downloaded_files_count += 1

                    await db.commit()

                    await asyncio.sleep(REQUEST_DELAY)

                    mark_resp = await client.post(
                        "/api/files/downloaded",
                        json={"file_names": batch}
                    )

                    # Проверяем 429 / 403 при отправке подтверждения
                    if mark_resp.status_code in (429, 403):
                        retry_after = int(mark_resp.headers.get("Retry-After", 5))

                        if retry_after > MAX_RETRY_WAIT:
                            msg = f"Сервер заблокировал подтверждение на {retry_after} сек."
                            logger.error(msg)
                            self.status = "error"
                            self.error_message = msg
                            return

                        logger.warning(f"Превышен лимит при подтверждении. Ждем {retry_after} сек...")
                        await asyncio.sleep(retry_after)

                        mark_resp = await client.post(
                            "/api/files/downloaded",
                            json={"file_names": batch}
                        )

                    mark_resp.raise_for_status()

            except Exception as e:
                self.status = "error"
                self.error_message = str(e)
                raise e


file_download_service = DownloadService()