from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.models import Base

DATABASE_URL = "sqlite+aiosqlite:///./src.db"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


