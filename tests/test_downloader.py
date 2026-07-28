import io
import zipfile
import pytest
import httpx
from src.services.downloader import file_download_service

@pytest.mark.asyncio
async def test_download_pipeline_success(db_session):
    # 1. Готовим фейковый ZIP-архив
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("test1.txt", "12345" * 100)
    zip_bytes = zip_buffer.getvalue()

    # 2. Описываем обработчик для httpx.MockTransport
    def handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path

        if url_path == "/api/files/names":
            # Сначала отдаем файлы, а при повторном вызове — пустой список (конец пайплайна)
            if getattr(handler, "called", False):
                return httpx.Response(200, json={"file_names": []})
            handler.called = True
            return httpx.Response(200, json={"file_names": ["test1.txt"]})

        elif url_path == "/api/files/download":
            return httpx.Response(200, content=zip_bytes)

        elif url_path == "/api/files/downloaded":
            return httpx.Response(200, json={"status": "ok"})

        return httpx.Response(404)

    # 3. Запускаем сервис с MockTransport
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await file_download_service.run_download_pipeline(db=db_session, client=client)

    assert file_download_service.status == "completed"
    assert file_download_service.downloaded_files_count == 1

@pytest.mark.asyncio
async def test_download_pipeline_retry_after(db_session, monkeypatch):
    async def dummy_sleep(secs):
        pass

    monkeypatch.setattr("asyncio.sleep", dummy_sleep)
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if request.url.path == "/api/files/names":
            attempts += 1
            if attempts == 1:
                return httpx.Response(429, headers={"Retry-After": "1"})
            return httpx.Response(200, json={"file_names": []})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await file_download_service.run_download_pipeline(db=db_session, client=client)

    assert attempts == 2
    assert file_download_service.status == "completed"