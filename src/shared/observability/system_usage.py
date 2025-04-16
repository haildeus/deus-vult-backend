import psutil
import os

from src.shared.observability.metrics import MetricsStorage
from src.shared.worker import BaseWorker


class SystemUsageMonitoring(BaseWorker):
    INTERVAL = 15

    metrics = MetricsStorage("system.usage")

    def __init__(self):
        super().__init__()
        self.process = psutil.Process(os.getpid())

    async def run_once(self):
        cpu_percent = self.process.cpu_percent()
        memory_used = self.process.memory_info().rss

        self.metrics.set("cpu", cpu_percent)
        self.metrics.set("memory", memory_used)
