import asyncio
import contextlib
import json
import logging
import threading
import typing
import typing as tp
import uuid
from functools import partial

import clickhouse_connect
import pytz  # type: ignore
import urllib3
from clickhouse_connect.driver import httputil
from clickhouse_connect.driver.asyncclient import AsyncClient

from src.shared.config import clickhouse_config
from src.shared.exceptions import NotFoundError
from src.shared.observability import schemas
from src.shared.observability.traces import async_traced_function, tracer
from src.shared.singleton import Singleton
from src.shared.time import Timer
from src.shared.worker import BaseWorker

if typing.TYPE_CHECKING:
    from src.shared.observability.metrics import MetricsStorage


retries = urllib3.Retry(total=10, backoff_factor=0.1, backoff_max=30)
http_pool: urllib3.PoolManager | None = None
http_client: AsyncClient | None = None
get_http_client: tp.Callable[[], tp.Awaitable[AsyncClient]] | None = None

GLOBAL_SETTINGS: dict[str, tp.Any] = {
    "s3_max_get_rps": 0,
    "s3_max_get_burst": 0,
    "s3_max_put_rps": 0,
}


class Inserter(BaseWorker, metaclass=Singleton["Inserter"]):  # type: ignore
    INTERVAL = 15

    metrics: tp.Optional["MetricsStorage"] = None  # round imports

    def __init__(
        self,
        table_name: str,
        max_size: int = 150_000,
        no_logging: bool = False,
        update_interval: int | None = None,
    ) -> None:
        super().__init__()
        self.queue = asyncio.Queue[schemas.BaseStructure](max_size)
        self.priority_queue = asyncio.Queue[schemas.BaseStructure]()
        self.table_name = table_name

        self.logger = logging.getLogger(f"deus-vult.ch.inserter.{table_name}")
        self.no_logging = no_logging

        self.lock = asyncio.Lock()

        if update_interval is not None:
            self.INTERVAL = update_interval

    @property
    def instance_key(self) -> str:
        return self.table_name

    def insert(self, record: schemas.BaseStructure) -> None:
        self.queue.put_nowait(record)

    async def insert_wait(self, record: schemas.BaseStructure) -> None:
        await self.queue.put(record)

    async def insert_sync(self, *records: schemas.BaseStructure) -> None:
        if http_client is None or self.metrics is None:
            raise RuntimeError("out of `with_clickhouse()` scope")

        try:
            await http_client.insert(
                self.table_name,
                [list(record.model_dump().values()) for record in records],
                column_names=list(records[0].model_dump(by_alias=True).keys()),
                settings={
                    "async_insert": 1,
                    "wait_for_async_insert": 1,
                    "async_insert_busy_timeout_max_ms": 200,
                    "async_insert_use_adaptive_busy_timeout": 0,
                },
            )

            self.metrics.increment(self.table_name, 1)
        except Exception as e:
            self.logger.exception("failed to sync insert")
            raise e

    async def insert_async(self, *records: schemas.BaseStructure) -> None:
        if http_client is None or self.metrics is None:
            raise RuntimeError("out of `with_clickhouse()` scope")

        await http_client.insert(
            self.table_name,
            [list(record.model_dump().values()) for record in records],
            column_names=list(records[0].model_dump(by_alias=True).keys()),
            settings={"async_insert": 1, "wait_for_async_insert": 0},
        )

    async def flush(self) -> None:
        assert self.metrics is not None

        with Timer() as t:
            async with self.lock:
                batch: list[schemas.BaseStructure] = []

                priority_size = self.priority_queue.qsize()
                for _ in range(priority_size):
                    batch.append(self.priority_queue.get_nowait())

                size = self.queue.qsize()
                for _ in range(size):
                    batch.append(self.queue.get_nowait())

            if not batch:
                return

            with tracer.start_as_current_span(
                "flush", attributes={"table_name": self.table_name}
            ):
                try:
                    await self.insert_async(*batch)

                    if not self.no_logging:
                        self.logger.info("flushed %s records", len(batch))
                    self.metrics.increment(self.table_name, len(batch))
                except Exception:
                    self.logger.exception("failed to flush")

                    for obj in batch:
                        self.priority_queue.put_nowait(obj)

        self.metrics.avg("flush_time", t.total, label=f".{self.table_name}")

    async def run_once(self) -> None:
        try:
            await self.flush()
        except Exception:
            if self.no_logging:
                return

            self.logger.exception("failed to flush insert")

    @classmethod
    def run(cls) -> None:
        for instance in cls.get_all_instances():
            instance.start()

    @classmethod
    async def shutdown(cls) -> None:
        for instance in cls.get_all_instances():
            instance.stop()

        with contextlib.suppress(Exception):
            await asyncio.gather(
                *(instance.flush() for instance in cls.get_all_instances())
            )

    def __str__(self) -> str:
        return f"Inserter<{self.table_name}>(size={self.queue.qsize()})"

    __repr__ = __str__


class HTTPDictCursor:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client
        self.results: list[dict[str, tp.Any]] = []
        self.session_id: str = str(uuid.uuid4())
        self.lock = threading.Lock()

    async def _execute(
        self, query: str, args: dict[str, tp.Any] | None = None, _: tp.Any = None
    ) -> None:
        result = await self.client.query(
            query,
            args,
            query_tz=pytz.UTC,
            settings={"session_id": self.session_id},
        )

        if "total_rows_to_read" in result.column_names:
            # todo: this is kostil! thanks, clickhouse-connect
            return

        with self.lock:
            self.results.extend(result.named_results())

    async def execute(
        self, query: str, args: dict[str, tp.Any] | None = None, context: tp.Any = None
    ) -> None:
        await _traced_execute(self._execute, query, args, context)

    async def fetchone(self) -> dict[str, tp.Any] | None:
        with self.lock:
            if self.results:
                return self.results.pop(0)
            return None

    async def fetchall(self) -> list[dict[str, tp.Any]]:
        with self.lock:
            dump = self.results.copy()
            self.results.clear()
            return dump


async def _traced_execute(
    execute: tp.Callable[[str, dict[str, tp.Any] | None, tp.Any], tp.Awaitable[None]],
    query: str,
    args: dict[str, tp.Any] | None = None,
    context: tp.Any = None,
) -> None:
    trace_args = args or {}
    if query.upper().startswith("INSERT") or isinstance(args, list):
        trace_args = {}

    with tracer.start_as_current_span(
        "cursor.execute",
        attributes={
            "query": query,
            "args": json.dumps({key: str(value) for key, value in trace_args.items()}),
        },
    ):
        await execute(query, args, context)


@contextlib.asynccontextmanager
async def with_clickhouse(**kwargs: tp.Any) -> tp.AsyncGenerator[tp.Any, None]:
    global http_pool, http_client, get_http_client
    from src.shared.observability.metrics import MetricsStorage

    http_pool = httputil.get_pool_manager(
        maxsize=clickhouse_config.http_max_pool_size,
        num_pools=clickhouse_config.http_num_pools,
        retries=retries,
        verify=False,
    )

    # noinspection PyRedeclaration
    async def get_http_client() -> AsyncClient:
        settings = GLOBAL_SETTINGS.copy()

        return await clickhouse_connect.get_async_client(
            pool_mgr=http_pool,
            executor_threads=clickhouse_config.http_thread_executor_size,
            settings=settings,
            **kwargs,
        )

    http_client = await get_http_client()  # type: ignore
    Inserter.metrics = MetricsStorage("inserter.flush")
    Inserter.run()

    try:
        yield http_pool
    finally:
        await Inserter.shutdown()

    http_pool = None


clickhouse_default = partial(
    with_clickhouse,
    host=clickhouse_config.host,
    port=clickhouse_config.port,
    user=clickhouse_config.user,
    password=clickhouse_config.password,
    secure=clickhouse_config.secure,
)

T = tp.TypeVar("T", bound=schemas.BaseStructure)


def _should_close_after_use(query: str) -> bool:
    return "CREATE TEMPORARY TABLE" in query.upper()


async def _execute_multiquery(
    session: HTTPDictCursor, query: str, query_args: dict[str, tp.Any] | None = None
) -> str:
    queries = query.split("; -- split")
    for statement in queries[:-1]:
        await session.execute(statement, query_args)

    return queries[-1]


@async_traced_function
async def db_fetchone(
    model: type[T],
    query: str,
    query_args: dict[str, tp.Any] | None = None,
    name: str | None = None,
    *,
    raise_not_found: bool = True,
) -> T | None:
    if http_client is None:
        raise RuntimeError("out of `with_clickhouse()` scope")

    if query_args is None:
        query_args = {}

    session = HTTPDictCursor(http_client)

    query = await _execute_multiquery(session, query, query_args)
    await session.execute(query, query_args)
    result = await session.fetchone()

    if not result:
        if raise_not_found:
            raise NotFoundError(name or model.__name__)

        return None

    return model.from_row(result)


@async_traced_function
async def db_fetchall(
    model: type[T],
    query: str,
    query_args: dict[str, tp.Any] | None = None,
    name: str | None = None,
    *,
    raise_not_found: bool = True,
) -> list[T]:
    if http_client is None:
        raise RuntimeError("out of `with_clickhouse()` scope")

    if query_args is None:
        query_args = {}

    session = HTTPDictCursor(http_client)

    query = await _execute_multiquery(session, query, query_args)
    await session.execute(query, query_args)
    result = await session.fetchall()

    if not result:
        if raise_not_found:
            raise NotFoundError(name or model.__name__)

        return []

    return model.from_rows(result)
