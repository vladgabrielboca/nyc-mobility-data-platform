# NYC Mobility Analytics Data Platform

A batch data platform built around a simple question: how does weather shape the way New Yorkers move?

Every month, the platform pulls the complete yellow taxi trip records published by the NYC Taxi and Limousine Commission, fetches hourly weather history for the city from Open-Meteo, checks both against explicit data contracts, loads what passes into PostgreSQL, and sets aside what does not. Every run leaves an audit trail, and every month can be re-run without creating duplicates. One command handles any range of months.

The project is built to practice the behaviors expected of a production data platform: explicit contracts, idempotent loads, quarantine of bad data, audit tables, and failure handling. It is under active development, with dbt transformations, Airflow orchestration, and a Power BI dashboard on the roadmap.

## The pipeline

```
NYC TLC parquet ─┐
                 ├─> Python ingestion ─> Raw storage (data/raw) ─> PostgreSQL (raw)
Open-Meteo API ──┘         │                                              │
                           │                                              v
                    schema validation                              dbt transformations
                    (data contracts)                             staging -> core -> marts
                           │                                              │
                           v                                              v
                  row-level quality rules                         Power BI dashboard
                  (quarantine + audit)
```

A monthly run, in order:

1. **Ingest.** Download the month's taxi parquet and weather JSON, with retries, timeouts, and a SHA-256 checksum. Before anything is recorded, each file is checked against a schema contract: expected columns and expected type families. If a file arrives malformed, the month fails with an error message that names the column and the mismatch.
2. **Load.** Rows stream from parquet into `raw.yellow_taxi_trips` in batches through `COPY`. The load replaces the month instead of appending to it, so re-running a month always converges to the same result.
3. **Filter.** While loading, named quality rules (positive distance, pickup before dropoff, non-negative fare, sane passenger counts) split each batch into rows that continue into the database and rows that are written to a quarantine area on disk.
4. **Record.** Every step writes to tables in the `ops` schema: what was ingested, what it checksummed to, which rules rejected how many rows, and whether each pipeline run succeeded or failed.

## Design decisions

**Load first, transform in SQL.** Raw data lands in Postgres as the source sent it, and business logic is applied later in SQL. The one exception happens during loading: rows that fail a quality rule are stopped there, so invalid data never enters the warehouse and can never be joined by accident.

**Idempotent months.** The manifest in `ops.ingestion_manifest` records every ingestion attempt, and a partial unique index in Postgres allows only one successful ingestion per source and month. Loads replace their month before writing. Re-running a month, or the whole backfill, always produces the same result.

**Logical types in the schema contract.** The validator checks type families instead of exact physical types. TLC publishes `VendorID` as `int64` in January and `int32` in February, and both are accepted because nothing downstream can tell them apart. A missing column, or a string where a number belongs, still fails the month.

**Rejected rows are kept for inspection.** Around four percent of trip rows violate a quality rule. They are stored under `data/quarantine/` with the same partitioning as the raw layer, and the rejection count for each rule is written to `ops.data_quality_results`. The evidence for any rejection is still available months later.

**Failures are recorded before the runner continues.** When a month fails, the manifest row describing that failure is committed before the runner moves on, so the ops tables still describe what happened during a failed run.

**One database connection per month.** The runner processes each month on its own connection, with its own commit. A failure in February affects February alone, and March starts from a clean state. Airflow will later schedule each month as a separate task, which maps directly onto this design.

## By the numbers

For January through March 2023: 9,384,487 trips ingested, 359,241 rows quarantined by four taxi rules, and 2,160 hourly weather records loaded.

## Warehouse layout

```
raw        landing zone: taxi trips, hourly weather, exactly as the source sent them
staging    renaming, casting, cleaning          (dbt, in progress)
core       dimensional model: facts, dimensions (dbt, planned)
marts      aggregates for the dashboard         (dbt, planned)
ops        the platform's own memory: ingestion manifest, pipeline runs, quality results
```

## Stack

Python 3.11, psycopg, PyArrow and pandas, PostgreSQL 17 in Docker Compose, pytest, Ruff, GitHub Actions. dbt Core and Airflow are next.

## Getting started

You need Docker and Python 3.11 or newer.

```bash
git clone https://github.com/vladgabrielboca/nyc-mobility-data-platform.git
cd nyc-mobility-data-platform

# credentials for the local database (safe defaults for development)
cp .env.example .env

# start Postgres 17; schemas and tables are created on first boot
docker compose up -d

# install dependencies (preferably in a virtual environment)
pip install -r requirements-dev.txt
```

Run the test suite (the database container must be up; two integration tests are skipped by default):

```bash
pytest
```

Backfill a range of months:

```bash
python src/nyc_mobility/orchestration/run.py --start 2023-01 --end 2023-03
```

To reset the database from scratch, including its structure:

```bash
docker compose down -v && docker compose up -d
```

All raw files on disk can be rebuilt from the sources: delete them and re-run the pipeline.

## Project structure

```
src/nyc_mobility/
    common/         database access, manifest and run bookkeeping, HTTP session, checksums
    ingestion/      downloads and schema validation for taxi and weather
    loaders/        row-group streaming loads with the quality filter and quarantine
    validation/     data contracts and named quality rules
    orchestration/  the monthly pipeline and the backfill runner
infra/sql/          schemas and tables, applied on first database boot
ci/                 test fixture generation for CI
tests/              unit tests for validation, ingestion, and loaders
data/raw/           downloaded source files, partitioned by year and month (gitignored)
data/quarantine/    rejected rows, same partitioning (gitignored)
```

## Roadmap

- [x] DE-001: project foundation, Docker Compose, CI
- [x] DE-002: ingestion layer with retries, checksums, and the manifest
- [x] DE-003: raw loaders with streaming COPY and idempotent months
- [x] DE-004: schema contracts, row-level rules, quarantine, quality results
- [x] DE-005: backfill runner with failure isolation
- [x] DE-006: dbt models, staging to core to marts
- [ ] Airflow orchestration of the monthly flow
- [ ] Power BI dashboard

## Data sources

- [NYC Taxi and Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), yellow taxi trip records
- [Open-Meteo](https://open-meteo.com/), historical weather API
