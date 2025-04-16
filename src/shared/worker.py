import asyncio
import logging
import random
import typing as tp

from src.shared.time import Timer

if tp.TYPE_CHECKING:
    from src.shared.observability.metrics import MetricsStorage


class BaseWorker:
    """Base worker class. Allows to create workers that will be executed in a loop."""

    INTERVAL = 60
    RANDOM_DELAY = 0.0

    logger = logging.getLogger("deus-vult.base_worker")
    metrics: tp.Optional["MetricsStorage"] = None

    def __init__(self) -> None:
        self._shutting_down: bool = False
        self._task: asyncio.Task[tp.Any] | None = None

    async def run_once(self) -> None:
        """
        Should be implemented by subclasses.
        """
        raise NotImplementedError()

    async def loop(self) -> None:
        while not self._shutting_down:
            try:
                with Timer() as t:
                    await self.run_once()

                if self.metrics:
                    self.metrics.avg("worker.run_time", t.total)

                delay = random.uniform(0, self.RANDOM_DELAY)
                sleep_time = self.INTERVAL - t.total + delay

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                elif self.metrics:
                    self.metrics.increment("worker.later")

            except Exception as e:
                self.logger.exception(
                    "%s failed run step in worker: %s",
                    self,
                    e
                )

    def start(self) -> None:
        self._task = asyncio.create_task(
            self.loop(), name=f"worker-loop-{self.__class__.__name__}"
        )

    def stop(self) -> None:
        self._shutting_down = True
        if self._task is not None:
            self._task.cancel()

    @property
    def running(self) -> bool:
        return not self._shutting_down and self._task is not None
