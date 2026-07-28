import logging
from typing import List, Dict, Any, Optional
from collections import Counter

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DownloadFile

logger = logging.getLogger(__name__)

class FileAnalyzerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_files_paginated(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        offset = (page - 1) * page_size

        total_count_query = await self.db.execute(select(func.count(DownloadFile.id)))
        total = total_count_query.scalar_one()

        stmt = (
            select(DownloadFile.id, DownloadFile.name, DownloadFile.downloaded_at)
            .order_by(desc(DownloadFile.downloaded_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        files = result.all()

        return {
            "items": [
                {
                    "id": f.id,
                    "file_name": f.name,  # Заменено с "name" на "file_name"
                    "downloaded_at": f.downloaded_at.isoformat() if f.downloaded_at else None
                }
                for f in files
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }

    async def calculate_stats(
            self,
            file_ids: Optional[List[int]] = None,
            select_all: bool = False
    ) -> Dict[str, Any]:

        stmt = select(DownloadFile)
        if not select_all:
            if not file_ids:
                return {"error": "Файлы не выбраны", "total_stats": {}, "files_stats": []}
            stmt = stmt.where(DownloadFile.id.in_(file_ids))

        result = await self.db.execute(stmt)
        files = result.scalars().all()

        total_counter = Counter({str(digit): 0 for digit in range(10)})
        files_stats = []

        for f in files:
            content = f.content or ""
            file_counter = Counter(content)

            digit_stats = {str(digit): file_counter.get(str(digit), 0) for digit in range(10)}

            total_counter.update(file_counter)

            files_stats.append({
                "id": f.id,
                "name": f.name,
                "digits": digit_stats
            })

        total_stats = {str(digit): total_counter.get(str(digit), 0) for digit in range(10)}

        return {
            "selected_count": len(files),
            "total_stats": total_stats,
            "files_stats": files_stats
        }
