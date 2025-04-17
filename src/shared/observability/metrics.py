import asyncio
import collections
import contextlib
import logging
import threading
import typing as tp
from types import TracebackType

from src.shared.config import shared_config
from src.shared.observability import schemas
from src.shared.observability.ch_utils import Inserter
from src.shared.time import Timer, now


class _MetricObject:
    def __init__(self) -> None:
        self.value = 0.0
        self.count = 0
        self.label = ""

    def get_value(self) -> float:
        return self.value / (self.count or 1)


class MetricsStorage:
    """
    Allows to set or increment metrics.

    Example usage:

    metrics = MetricsStorage("test_metrics")
    metrics.increment("foo")
    """

    INTERVAL = 15

    _storage: collections.defaultdict[str, _MetricObject] = collections.defaultdict(
        _MetricObject
    )
    _lock = threading.Lock()
    _task: asyncio.Task[tp.Any] | None = None
    _inserter = Inserter("operation.metrics")

    logger = logging.getLogger("deus-vult.metrics")

    def __init__(self, metric_prefix: str = "") -> None:
        self.metric_prefix = metric_prefix

    def get_full_key(self, key: str = "", label: str = "") -> str:
        if not self.metric_prefix:
            return key
        return f"{self.metric_prefix}.{key}{label}"

    def increment(self, key: str = "", delta: float = 1.0, label: str = "") -> None:
        with self._lock:
            metric = self._storage[self.get_full_key(key, label=label)]
            metric.value += delta
            metric.label = label

    def avg(
        self, key: str = "", value: float = 1.0, count: int = 1, label: str = ""
    ) -> None:
        with self._lock:
            metric = self._storage[self.get_full_key(key, label=label)]
            metric.value += value
            metric.count += count
            metric.label = label

    def set(self, key: str = "", value: float = 1.0) -> None:
        with self._lock:
            metric = self._storage[self.get_full_key(key)]
            metric.value = value

    @classmethod
    async def flush(cls) -> None:
        data: list[schemas.Metric] = []

        _now = now()
        with cls._lock:
            for key, metric in cls._storage.items():
                if metric.label:
                    key = key.removesuffix(metric.label)

                data.append(
                    schemas.Metric(
                        app_env=shared_config.app_env,
                        stage=shared_config.stage,
                        date=_now,
                        key=key,
                        value=metric.get_value(),
                        label=metric.label,
                    )
                )
            cls._storage.clear()

        try:
            data.append(
                schemas.Metric(
                    app_env=shared_config.app_env,
                    stage=shared_config.stage,
                    date=_now,
                    key="system.running_tasks",
                    value=len(asyncio.all_tasks(asyncio.get_running_loop())),
                )
            )
        except Exception:
            cls.logger.fatal("failed to prepare metrics data", exc_info=True)

        await cls._inserter.insert_async(*data)

    @classmethod
    async def loop(cls) -> None:
        delta = 0.0
        while True:
            await asyncio.sleep(max(cls.INTERVAL - delta, 0))
            with Timer() as t:
                try:
                    await cls.flush()
                except Exception:
                    cls.logger.exception("failed to flush metrics")

            delta = t.total

    @classmethod
    def start(cls) -> None:
        cls._task = asyncio.create_task(cls.loop(), name="metrics-loop")

    async def __aenter__(self) -> None:
        # Must be inside ClickHouse context
        MetricsStorage.start()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if MetricsStorage._task is not None:
            MetricsStorage._task.cancel()

        with contextlib.suppress(Exception):
            await MetricsStorage.flush()

        with contextlib.suppress(asyncio.CancelledError):
            if MetricsStorage._task is not None:
                await MetricsStorage._task
