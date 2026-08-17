CREATE TABLE IF NOT EXISTS ops.ingestion_manifest (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,    -- 'taxi' or 'weather'
    year INT NOT NULL,
    month INT NOT NULL,
    file_checksum TEXT,
    row_count INT,
    status TEXT NOT NULL,  -- 'pending' | 'success' | 'failed'
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_successful_ingestion
ON ops.ingestion_manifest (source, year, month)
WHERE status = 'success';

CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_type TEXT NOT NULL,
    year INT,
    month INT,
    status TEXT NOT NULL,  -- 'pending' | 'success' | 'failed'
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ops.data_quality_results (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    rule_name TEXT NOT NULL,
    rejected_count INT NOT NULL,
    checked_at TIMESTAMPTZ DEFAULT now()
);
