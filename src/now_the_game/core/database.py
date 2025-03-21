from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .. import logger
from .storage_config import storage_config


class Database:
    def __init__(self):
        db_path = storage_config.db_path
        db_url = f"sqlite+aiosqlite:///{db_path}"

        self.engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize(self):
        db_dir = storage_config.db_path.parent
        if db_dir and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

        async with self.engine.begin() as conn:
            logger.info("Creating database tables if they don't exist")
            await conn.run_sync(SQLModel.metadata.create_all)

        return self

    @asynccontextmanager
    async def session(self):
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        await self.engine.dispose()


db = Database()
