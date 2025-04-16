CREATE TABLE operation.logs
(
    Timestamp DateTime64 CODEC(Delta(8), ZSTD(1)),
    SeverityText LowCardinality(String),
	SeverityNumber Int32,
    Body String CODEC(ZSTD(1)),
    TraceId String CODEC(ZSTD(1)),
	SpanId String CODEC(ZSTD(1)),
    PodName String CODEC(ZSTD(1)),

    app_env LowCardinality(String),
    stage LowCardinality(String),
    logger_name LowCardinality(String),
    format_message String CODEC(ZSTD(1)),
    file_name LowCardinality(String),
    func_name String CODEC(ZSTD(1)),
    lineno UInt32,

    LogAttributes String ALIAS SeverityText,

    INDEX idx_trace_id TraceId TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_pod_name PodName TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_body Body TYPE tokenbf_v1(32768, 3, 0) GRANULARITY 1
)
ENGINE = MergeTree()
ORDER BY (app_env, stage, Timestamp)
TTL toDateTime(Timestamp) + INTERVAL 60 DAY
