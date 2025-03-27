from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import MetaData, SQLModel

from src.shared.config import BaseStorageConfig
from src.shared.logging import logger


class Database:
    def __init__(self, db_config: BaseStorageConfig):
        self.__config_check(db_config)

        self.db_path = db_config.db_path
        self.db_url = f"sqlite+aiosqlite:///{self.db_path}"

        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    def __config_check(self, config: BaseStorageConfig):
        try:
            assert config
            assert config.db_path
            assert config.storage_path
        except AssertionError as e:
            logger.error(f"Error initializing database: {e}")
            raise

    async def initialize(self):
        logger.info("Initializing database")
        db_dir = self.db_path.parent
        logger.debug(f"Database directory: {db_dir}")
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

    async def get_all_tables(self):
        async with self.engine.begin():
            return SQLModel.metadata.tables.keys()

    @asynccontextmanager
    async def session(self):
        async with self.async_session() as session:
            logger.debug("Created session")
            try:
                yield session
                logger.debug("Committing session")
                await session.commit()
            except Exception:
                logger.debug("Rolling back session")
                await session.rollback()
                raise

    async def close(self):
        await self.engine.dispose()


metadata = MetaData()
