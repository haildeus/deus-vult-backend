from datetime import datetime, timezone

ZERO_UTC = datetime(1970, 1, 1, tzinfo=timezone.utc)
MAX_UTC = datetime.fromtimestamp(4294967295, tz=timezone.utc)


def now() -> datetime:
    return datetime.now(tz=timezone.utc)


def utcnow() -> datetime:
    return datetime.utcnow()


def to_utc(d: datetime) -> datetime:
    return d.astimezone(timezone.utc)


class Timer:
    def __init__(self):
        self.start: datetime | None = None
        self.end: datetime | None = None

    @property
    def current(self) -> float:
        return (now() - self.start).total_seconds()

    @property
    def total(self) -> float:
        if self.end is None:
            raise ValueError("Timer is not finished")

        return (self.end - self.start).total_seconds()

    def __enter__(self):
        self.start = now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = now()
