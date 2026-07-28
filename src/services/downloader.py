import asyncio
import io
import logging
import zipfile
import zoneinfo
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import DownloadFile, DownloadProgress

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

    async def update_db_progress(self, db: AsyncSession, is_active: bool = True,
                                  status_msg: str = "Скачивание выполняется..."):
        stmt = select(DownloadProgress).order_by(DownloadProgress.id.desc())
        result = await db.execute(stmt)
        progress = result.scalars().first()

        if not progress:
            progress = DownloadProgress(
                started_at_nsk=self.start_time_nsk or "-",
                total_names_count=self.received_names_count,
                downloaded_count=self.downloaded_files_count,
                is_active=is_active,
                status_message=status_msg
            )
            db.add(progress)
        else:
            progress.started_at_nsk = self.start_time_nsk or "-"
            progress.total_names_count = self.received_names_count
            progress.downloaded_count = self.downloaded_files_count
            progress.is_active = is_active
            progress.status_message = status_msg

        await db.commit()

    async def run_download_pipeline(self, db: AsyncSession, client: httpx.AsyncClient):
        self.status = "running"
        self.error_message = None

        nsk_tz = zoneinfo.ZoneInfo("Asia/Novosibirsk")
        self.start_time_nsk = datetime.now(nsk_tz).strftime("%H:%M:%S (%d.%m.%Y)")

        await self.update_db_progress(db, is_active=True, status_msg="Скачивание выполняется...")

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
                        await self._update_db_progress(db, is_active=False, status_msg=msg)
                        break

                    logger.warning(f"Превышен лимит запросов. Ждем {retry_after} сек...")
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                file_names: list[str] = data.get("file_names", [])

                if not file_names:
                    self.status = "completed"
                    await self.update_db_progress(db, is_active=False, status_msg="Завершено")
                    break

                self.received_names_count += len(file_names)
                await self.update_db_progress(db, is_active=True, status_msg="Скачивание выполняется...")

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
                            self.status = "error"
                            self.error_message = msg
                            await self._update_db_progress(db, is_active=False, status_msg=msg)
                            return

                        logger.warning(f"Превышен лимит скачивания. Ждем {retry_after} сек...")
                        await asyncio.sleep(retry_after)

                        dl_response = await client.post(
                            "/api/files/download",
                            json={"file_names": batch}
                        )

                    dl_response.raise_for_status()

                    files_to_insert = []
                    with zipfile.ZipFile(io.BytesIO(dl_response.content)) as zf:
                        for filename in zf.namelist():
                            file_content = zf.read(filename).decode("utf-8").strip()

                            file_path = settings.STORAGE_DIR / filename
                            file_path.write_text(file_content, encoding="utf-8")

                            files_to_insert.append({
                                "name": filename,
                                "content": file_content,
                                "downloaded_at": datetime.now(timezone.utc)
                            })

                    if files_to_insert:
                        stmt = insert(DownloadFile).values(files_to_insert)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['name'])
                        await db.execute(stmt)

                    self.downloaded_files_count += len(files_to_insert)

                    await self._update_db_progress(db, is_active=True, status_msg="Скачивание выполняется...")

                    await asyncio.sleep(REQUEST_DELAY)

                    mark_resp = await client.post(
                        "/api/files/downloaded",
                        json={"file_names": batch}
                    )

                    if mark_resp.status_code in (429, 403):
                        retry_after = int(mark_resp.headers.get("Retry-After", 5))

                        if retry_after > MAX_RETRY_WAIT:
                            msg = f"Сервер заблокировал подтверждение на {retry_after} сек."
                            logger.error(msg)
                            self.status = "error"
                            self.error_message = msg
                            await self._update_db_progress(db, is_active=False, status_msg=msg)
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
                await self.update_db_progress(db, is_active=False, status_msg=f"Ошибка: {str(e)}")
                raise e


file_download_service = DownloadService()