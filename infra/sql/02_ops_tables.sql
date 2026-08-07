CREATE TABLE IF NOT EXISTS ops.ingestion_manifest (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,    -- 'taxi' sau 'weather'
    year INT NOT NULL,
    month INT NOT NULL,
    file_checksum TEXT NOT NULL,
    row_count INT,
    status TEXT NOT NULL,  -- 'pending' | 'success' | 'failed'
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    error_message TEXT,
    UNIQUE (source, year, month, file_checksum)
);

CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_type TEXT NOT NULL,
    year INT,
    month INT,
    status TEXT NOT NULL,  -- 'pending' | 'success' | 'failed'
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);