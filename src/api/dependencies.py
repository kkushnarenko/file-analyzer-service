from typing import AsyncGenerator

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal as session:
        yield session


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    headers = {}
    if settings.CANDIDATE_ID:
        headers["X-CANDIDATE-ID"] = settings.CANDIDATE_ID

    async with httpx.AsyncClient(
        base_url=settings.BASE_URL, headers=headers,
        timeout=httpx.Timeout(30.0),
    ) as client:
        yield client

