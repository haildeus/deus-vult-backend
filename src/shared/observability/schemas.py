import datetime
import typing as tp

from pydantic import BaseModel, Field


class BaseStructure(BaseModel):
    @classmethod
    def from_row(cls, row: dict[str, tp.Any]) -> tp.Self:
        dct = {}  # type: ignore
        for key, value in row.copy().items():
            if key.startswith("@"):
                row[key.removeprefix("@")] = row.pop(key)

            if "." in key:
                parent, child = key.split(".")
                dct.setdefault(parent, {})[child] = value
                row.pop(key)

        row.update(dct)
        # noinspection PyArgumentList
        return cls(**row)

    @classmethod
    def from_rows(cls, rows: list[dict[tp.Any, tp.Any]]) -> list[tp.Self]:
        return [cls.from_row(x) for x in rows]

    def serialize(self) -> bytes:
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, data: bytes) -> tp.Self:
        raise NotImplementedError()

    @property
    def caching_key(self) -> bytes:
        raise NotImplementedError()


class Metric(BaseStructure):
    app_env: str
    stage: str
    date: datetime.datetime
    key: str
    value: float
    label: str = ''


class Log(BaseStructure):
    # OTEL format
    timestamp: datetime.datetime = Field(..., serialization_alias="Timestamp")
    severity_text: str = Field(..., serialization_alias="SeverityText")
    severity_number: int = Field(..., serialization_alias="SeverityNumber")
    body: str = Field(..., serialization_alias="Body")
    trace_id: str = Field(..., serialization_alias="TraceId")
    span_id: str = Field(..., serialization_alias="SpanId")
    pod_name: str = Field(..., serialization_alias="PodName")

    app_env: str
    stage: str
    logger_name: str
    format_message: str
    file_name: str
    func_name: str
    lineno: int


class Trace(BaseStructure):
    timestamp: int = Field(..., serialization_alias="Timestamp")
    trace_id: str = Field(..., serialization_alias="TraceId")
    span_id: str = Field(..., serialization_alias="SpanId")
    parent_span_id: str = Field(..., serialization_alias="ParentSpanId")
    trace_state: str = Field(..., serialization_alias="TraceState")
    span_name: str = Field(..., serialization_alias="SpanName")
    span_kind: str = Field(..., serialization_alias="SpanKind")
    service_name: str = Field(..., serialization_alias="ServiceName")
    resource_attributes: dict[str, str] = Field(
        ...,
        serialization_alias="ResourceAttributes"
    )
    span_attributes: dict[str, str] = Field(..., serialization_alias="SpanAttributes")
    duration: int = Field(..., serialization_alias="Duration")
    status_code: str = Field(..., serialization_alias="StatusCode")
    status_message: str = Field(..., serialization_alias="StatusMessage")

    events_timestamps: list[int] = Field(..., serialization_alias="Events.Timestamp")
    events_names: list[str] = Field(..., serialization_alias="Events.Name")
    events_attributes: list[dict[str, str]] = Field(
        ...,
        serialization_alias="Events.Attributes"
    )

    links_trace_ids: list[str] = Field(..., serialization_alias="Links.TraceId")
    links_span_ids: list[str] = Field(..., serialization_alias="Links.SpanId")
    links_trace_states: list[str] = Field(..., serialization_alias="Links.TraceState")
    links_attributes: list[dict[str, str]] = Field(
        ...,
        serialization_alias="Links.Attributes"
    )

    app_env: str
    stage: str
