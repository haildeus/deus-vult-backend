import contextlib

from src.shared.observability.ch_utils import Inserter, clickhouse_default
from src.shared.observability.metrics import MetricsStorage
from src.shared.observability.system_usage import SystemUsageMonitoring
from src.shared.observability.logging_utils import configure_logging as _configure_logging
from src.shared.observability.traces import configure_tracing


def configure_logging():
    configure_tracing(Inserter)
    _configure_logging()


@contextlib.asynccontextmanager
async def with_observability():
    system_usage_monitoring = SystemUsageMonitoring()
    system_usage_monitoring.start()

    async with clickhouse_default():
        async with MetricsStorage():
            yield
