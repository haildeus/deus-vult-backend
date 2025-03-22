from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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

        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize(self):
        logger.info("Initializing database")
        db_dir = storage_config.db_path.parent
        print(db_dir)
        if db_dir and not db_dir.exists():
            logger.info("Database directory not found. Creating.")
            db_dir.mkdir(parents=True, exist_ok=True)

        async with self.engine.begin() as conn:
            logger.info("Database tables not found. Creating.")
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("Database initialized")
        return self

    async def drop_all(self):
        """Drops all tables in the database"""
        async with self.engine.begin() as conn:
            logger.info("Dropping all tables")
            await conn.run_sync(SQLModel.metadata.drop_all)

    async def clean_entries(self):
        """Cleans all entries in the database"""
        async with self.engine.begin() as conn:
            await conn.run_sync(lambda _: SQLModel.metadata.clear())

    @asynccontextmanager
    async def session(self):
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self):
        await self.engine.dispose()


db = Database()
