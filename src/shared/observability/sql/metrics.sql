CREATE TABLE operation.metrics
(
    app_env LowCardinality(String),
    stage LowCardinality(String),
    date DateTime64,
    key LowCardinality(String),
    value Float64,
    label String DEFAULT ''
)
ENGINE = MergeTree()
ORDER BY (app_env, stage, key, date)
TTL toDateTime(date) + INTERVAL 60 DAY
