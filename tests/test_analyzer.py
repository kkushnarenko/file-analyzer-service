import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, result

from src.models import Base, DownloadFile
from src.services.analyzer import FileAnalyzerService

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession):
    files = [
        DownloadFile(
            name="file1.txt",
            content="1234555",
            downloaded_at=datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
        ),
        DownloadFile(
            name="file2.txt",
            content="00099",
            downloaded_at=datetime(2026, 7, 28, 11, 0, tzinfo=timezone.utc),
        ),
        DownloadFile(
            name="file3.txt",
            content="abc 123",
            downloaded_at=datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc),
        ),
    ]
    db_session.add_all(files)
    await db_session.commit()
    return db_session

@pytest.mark.asyncio
async def test_get_files_paginated(seeded_db : AsyncSession):
    analyzer = FileAnalyzerService(seeded_db)

    result = await analyzer.get_files_paginated(page=1, page_size=2)

    assert result["total_items"] == 3
    assert result["total_pages"] == 2
    assert result["page"] == 1
    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "file3.txt"
    assert result["items"][1]["name"] == "file2.txt"


@pytest.mark.asyncio
async def test_calculate_stats_select_all(seeded_db: AsyncSession):
    analyzer = FileAnalyzerService(seeded_db)

    result = await analyzer.calculate_stats(select_all=True)

    assert result["selected_count"] == 3
    total_stats = result["total_stats"]

    assert total_stats["0"] == 3  # Из file2
    assert total_stats["1"] == 2  # 1 из file1, 1 из file3
    assert total_stats["5"] == 3  # Из file1
    assert total_stats["9"] == 2  # Из file2


@pytest.mark.asyncio
async def test_calculate_stats_empty_file_ids(seeded_db: AsyncSession):
    analyzer = FileAnalyzerService(seeded_db)

    result = await analyzer.calculate_stats(file_ids=[], select_all=False)

    assert "error" in result
    assert result["total_stats"] == {}
    assert result["files_stats"] == []