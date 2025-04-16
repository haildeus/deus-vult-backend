import asyncio
import logging
import random

from src.shared import observability
from src.shared.exceptions import format_exception
from src.shared.time import Timer


class BaseWorker:
    """Base worker class. Allows to create workers that will be executed in a loop."""

    INTERVAL = 60
    RANDOM_DELAY = 0.0

    logger = logging.getLogger("deus-vult.base_worker")
    metrics: "observability.metrics.MetricsStorage" = None

    def __init__(self):
        self._shutting_down = False
        self._task = None

    async def run_once(self):
        """
        Should be implemented by subclasses.
        """
        raise NotImplementedError()

    async def loop(self):
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
                self.logger.error(
                    "%s failed run step in worker: %s",
                    self,
                    format_exception(e, with_traceback=True)
                )

    def start(self) -> None:
        self._task = asyncio.create_task(
            self.loop(),
            name=f"worker-loop-{self.__class__.__name__}"
        )

    def stop(self):
        self._shutting_down = True
        self._task.cancel()

    @property
    def running(self):
        return not self._shutting_down and self._task is not None
