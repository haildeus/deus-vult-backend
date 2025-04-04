from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.shared.config import PostgresConfig
from src.shared.logging import logger


class Database:
    def __init__(self, db_config: PostgresConfig):
        self.__config_check(db_config)

        self.user = db_config.user
        self.password = db_config.password
        self.host = db_config.host
        self.port = db_config.port
        self.db_name = db_config.db_name

        self.url = db_config.db_url
        self.safe_url = self.url.replace(self.password, "********")

        logger.debug(f"Connecting to {self.safe_url}")

        self.engine = create_async_engine(
            self.url,
            echo=False,  # Change to True to see queries
            pool_pre_ping=True,
            pool_recycle=3600,
            # connect_args={"ssl": "require"}, # TODO: Add ssl
        )

        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.debug("Database connection initialized")

    def __config_check(self, config: PostgresConfig):
        try:
            assert config
            assert config.user
            assert config.password
            assert config.host
            assert config.port
            assert config.port == 5432
            assert config.db_url
        except AssertionError as e:
            logger.error(f"Error initializing database: {e}")
            raise

    async def create_all(self):
        """
        Initializes the database connection and optionally creates tables.
        """
        logger.debug(f"Initializing database connection to {self.safe_url}")

        async with self.engine.begin() as conn:
            # TODO: Add Alembic migrations
            logger.warning(
                "Running SQLModel.metadata.create_all. Use Alembic for production."
            )
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.debug("Database connection initialized, tables checked/created.")
        return self

    async def drop_all(self):
        """
        Drops all tables defined in SQLModel.metadata.
        WARNING: This is destructive and irreversible. Use with extreme caution.
        """
        async with self.engine.begin() as conn:
            logger.warning(
                f"Dropping all tables in database {self.safe_url} defined in metadata!"
            )
            await conn.run_sync(SQLModel.metadata.drop_all)
        logger.info("Finished dropping tables.")

    async def get_all_tables(self):
        """
        Returns a list of all tables defined in SQLModel.metadata.
        """
        return SQLModel.metadata.tables.keys()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Provides a transactional database session."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                logger.error(f"Session rollback due to error: {e}", exc_info=True)
                await session.rollback()
                raise

    async def close(self):
        """Closes the database connection pool."""
        logger.info(f"Closing database connection pool for {self.safe_url}")
        await self.engine.dispose()
