from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from config.settings import settings

async_engine = create_async_engine(
    settings.db_url_asynpg,
    echo=False, # Если нужен полный лог, то True
    future=True
)

AssyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AssyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()