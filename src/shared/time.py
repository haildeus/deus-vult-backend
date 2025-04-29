from datetime import UTC, datetime
from types import TracebackType

ZERO_UTC = datetime(1970, 1, 1, tzinfo=UTC)
MAX_UTC = datetime.fromtimestamp(4294967295, tz=UTC)


def now() -> datetime:
    return datetime.now(tz=UTC)


def utcnow() -> datetime:
    # noinspection PyDeprecation
    return datetime.utcnow()


def to_utc(d: datetime) -> datetime:
    return d.astimezone(UTC)


class Timer:
    def __init__(self) -> None:
        self.start: datetime | None = None
        self.end: datetime | None = None

    @property
    def current(self) -> float:
        if self.start is None:
            raise RuntimeError("Timer has not started yet")

        return (now() - self.start).total_seconds()

    @property
    def total(self) -> float:
        if self.start is None:
            raise RuntimeError("Timer has not started yet")

        if self.end is None:
            raise ValueError("Timer is not finished")

        return (self.end - self.start).total_seconds()

    def __enter__(self) -> "Timer":
        self.start = now()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.end = now()
