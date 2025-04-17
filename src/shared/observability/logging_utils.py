import logging
import socket
from datetime import UTC, datetime

import colorlog
from opentelemetry.trace import INVALID_SPAN, get_current_span

from src.shared.config import shared_config
from src.shared.observability import schemas
from src.shared.observability.ch_utils import Inserter

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


class ClickHouseHandler(logging.Handler):
    inserter = Inserter("operation.logs", no_logging=True)

    def __init__(self) -> None:
        super().__init__()
        self.fqdn = socket.getfqdn()

    def process_record(self, record: logging.LogRecord) -> schemas.Log:
        span = get_current_span()

        span_id = ""
        trace_id = ""
        if span is not INVALID_SPAN:
            context = span.get_span_context()
            span_id = hex(context.span_id)
            trace_id = hex(context.trace_id)

        return schemas.Log(
            timestamp=datetime.fromtimestamp(record.created, UTC),
            severity_text=record.levelname,
            severity_number=record.levelno,
            body=self.format(record),
            trace_id=trace_id or "",
            span_id=span_id or "",
            pod_name=self.fqdn,
            app_env=shared_config.app_env,
            stage=shared_config.stage,
            logger_name=record.name,
            format_message=record.msg,
            file_name=record.filename,
            func_name=record.funcName,
            lineno=record.lineno or 0,
        )

    def emit(self, record: logging.LogRecord) -> None:
        self.inserter.insert(self.process_record(record))


def configure_logging() -> None:
    console_handler = colorlog.StreamHandler()

    log_format = "%(log_color)s%(levelname)-8s%(reset)s | %(asctime)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"  # noqa: E501
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = colorlog.ColoredFormatter(
        fmt=log_format,
        datefmt=date_format,
        reset=True,
        log_colors=LOG_COLORS,
        secondary_log_colors={},  # You can color specific parts of the message too
        style="%",  # Use %-style formatting
    )
    console_handler.setFormatter(formatter)

    handlers = [
        console_handler,
        ClickHouseHandler(),
    ]

    logging.getLogger("pyrogram").setLevel(logging.INFO)
    logging.getLogger("clickhouse_connect").setLevel(logging.INFO)

    logging.basicConfig(
        level=shared_config.log_level,
        format="%(levelname)-8s | %(asctime)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",  # noqa: E501
        datefmt=date_format,
        handlers=handlers,
    )
