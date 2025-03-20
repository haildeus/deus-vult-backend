import asyncio
import contextlib
import sqlite3
from pathlib import Path

from .. import logger
from ..storage.storage_config import storage_config


class Database:
    def __init__(self):
        self.db_path = storage_config.db_path
        self.schemas_path = storage_config.schemas_path
        self.queries_path = storage_config.queries_path

        # Connection will be established during initialization
        self.conn = None
        self.cursor = None

    async def initialize(self) -> None:
        """
        Initialize the database: ensure the db file exists and establish connection.
        """
        self._check_database_file()  # Ensure database file exists
        self._check_settings()  # Ensure all settings are correct

        # Establish connection
        def _connect():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn, conn.cursor()

        self.conn, self.cursor = await asyncio.to_thread(_connect)

        await self._setup_database()
        return self

    def _check_database_file(self):
        # Ensure the directory exists
        db_dir = self.db_path.parent
        if db_dir and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

        # Ensure database file exists if not create
        if not self.db_path.exists():
            self.db_path.touch()

    def _check_settings(self):
        try:
            assert self.db_path.exists()
            assert self.db_path.is_file()
            assert self.db_path.suffix == ".db"
        except AssertionError as e:
            raise ValueError("Invalid database path") from e

        try:
            assert self.schemas_path.exists()
            assert self.schemas_path.is_dir()
        except AssertionError as e:
            raise ValueError("Invalid schemas path") from e

        try:
            assert self.queries_path.exists()
            assert self.queries_path.is_dir()
        except AssertionError as e:
            raise ValueError("Invalid queries path") from e

    async def _setup_database(self) -> None:
        """
        Set up the database by creating schemas if they don't exist.

        Args:
            schemas: Dictionary with CREATE TABLE statements as values
        """
        schemas = self.get_schemas_files()
        schemas_dict = {schema.stem: schema for schema in schemas}

        for schema_name, schema_file in schemas_dict.items():
            logger.info(f"Checking {schema_name} schema")
            schema_content = self.open(schema_file)["content"]

            def _execute_schema(schema_content: str):
                self.cursor.execute(schema_content)
                self.conn.commit()

            await asyncio.to_thread(_execute_schema, schema_content)

    def open(self, query_name: str) -> dict[str, str]:
        """
        Open a file and return its content.
        """
        file_path = self.queries_path / f"{query_name}.sql"
        try:
            assert file_path.exists()
            assert file_path.is_file()
            assert file_path.suffix == ".sql"
        except AssertionError as e:
            raise ValueError(
                f"File {file_path} is not a valid schema or query file"
            ) from e

        with open(file_path) as file:
            return {"name": file_path.name, "content": file.read()}

    async def query(
        self, query: str, params: tuple | None = None, fetch: bool = True
    ) -> list[sqlite3.Row] | None:
        """
        Execute a query and optionally fetch results.

        Args:
            query: SQL query string
            params: Parameters for the query
            fetch: Whether to fetch and return results

        Returns:
            List of rows if fetch is True, None otherwise
        """

        # Execute query in a separate thread to avoid blocking the event loop
        def _execute_query():
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if fetch:
                return self.cursor.fetchall()
            else:
                self.conn.commit()
                return None

        # Run database operation in a thread pool
        result = await asyncio.to_thread(_execute_query)
        return result

    @contextlib.asynccontextmanager
    async def async_query(self, query: str, params: tuple | None = None):
        """
        Async context manager for executing queries.

        Args:
            query: SQL query string
            params: Parameters for the query

        Yields:
            Cursor object for the query
        """

        # Execute query in a separate thread
        def _execute_query():
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor

        cursor = await asyncio.to_thread(_execute_query)
        try:
            yield cursor
        finally:
            await asyncio.to_thread(self.conn.commit)

    async def close(self) -> None:
        """
        Close the database connection asynchronously.
        """
        if self.conn:
            await asyncio.to_thread(lambda: (self.cursor.close(), self.conn.close()))

    def get_schemas_files(self) -> list[Path]:
        """
        Get a list of all schema files.
        """
        return list(self.schemas_path.glob("*.sql"))


db = Database()
