# NYC Mobility Analytics Data Platform

A batch data platform built around one question: how does weather shape the way New Yorkers move?

The platform pulls the monthly yellow taxi records of the NYC Taxi and Limousine Commission. It also fetches hourly weather history for the city from Open-Meteo. It validates both against explicit data contracts, loads what passes into PostgreSQL, and quarantines what fails. dbt then builds the dimensional model on top. Every month can run again without duplicates, and one command processes any range of months.

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

1. **Ingest.** Download the taxi parquet and the weather JSON for the month. Retries, timeouts, and a SHA-256 checksum protect the download.
2. **Validate.** Each file must match a schema contract: expected columns and expected type families. A malformed file fails the month and names the offending column.
3. **Load.** Rows stream into `raw.yellow_taxi_trips` in batches through `COPY`. The load replaces the month, so a re-run always converges to the same result.
4. **Filter.** Named quality rules split each batch. Valid rows enter the database, and invalid rows go to a quarantine area on disk.
5. **Record.** Every step writes to tables in the `ops` schema: files, checksums, rejections per rule, and the status of each pipeline run.
6. **Transform.** dbt builds staging views, then the core star schema: `fact_trips`, `fact_weather`, and three dimensions.

## Design decisions

- **Load raw, transform in SQL.** Raw data lands in Postgres as the source sent it, and business logic lives in SQL. The one exception is the load itself: rows that fail a quality rule stop there.
- **Idempotent months.** A partial unique index in the manifest allows only one successful ingestion per source and month. Loads replace their month before they write.
- **Logical types in contracts.** TLC publishes `VendorID` as `int64` in January and `int32` in February, and both pass because they are the same type family. A missing column, or a string where a number belongs, still fails.
- **Rejected rows stay on disk.** Around four percent of trip rows violate a rule. They sit under `data/quarantine/` with the same partitioning as raw, so the evidence for a rejection is still there months later.
- **One connection per month.** A failure in February affects February alone, and March starts clean. Airflow will later map one month to one task.
- **Natural date keys.** Both facts carry plain dates that join `dim_date` directly. A shared key is what lets the demand-versus-weather mart join them.

## By the numbers

January to March 2023: the source files hold 9,384,487 trip rows. Five taxi rules quarantined 359,448 of them, and 9,025,039 trips landed in `fact_trips`. `fact_weather` holds 2,160 hourly records, one per hour of the period.

## Warehouse layout

```
raw        landing zone: taxi trips and hourly weather, as the source sent them
staging    renaming, casting, derived columns        (dbt views)
core       star schema: two facts, three dimensions  (dbt tables)
marts      aggregates for the dashboard              (dbt, planned)
ops        the platform's own memory: manifest, pipeline runs, quality results
```

## Stack

Python 3.11, psycopg, PyArrow and pandas, PostgreSQL 17 in Docker Compose, dbt Core, pytest, Ruff, and GitHub Actions. Airflow and Power BI are next.

## Getting started

You need Docker and Python 3.11 or newer.

1. Clone the repository and enter it:

```bash
git clone https://github.com/vladgabrielboca/nyc-mobility-data-platform.git
cd nyc-mobility-data-platform
```

2. Create the credentials file for the local database:

```bash
cp .env.example .env
```

3. Start PostgreSQL. Schemas and tables are created on first boot:

```bash
docker compose up -d
```

4. Install the dependencies, preferably in a virtual environment:

```bash
pip install -r requirements-dev.txt
```

Run the test suite. The database container must be up before you run it, and two integration tests are skipped by default:

```bash
pytest
```

Backfill a range of months:

```bash
python src/nyc_mobility/orchestration/run.py --start 2023-01 --end 2023-03
```

Build the dbt models. The profile reads the `POSTGRES_*` variables from your environment, so export the values from `.env` first:

```bash
cd dbt
dbt build
```

To reset the database completely, including its structure:

```bash
docker compose down -v && docker compose up -d
```

All raw files on disk can be rebuilt from the sources. Delete them and run the pipeline again.

## Project structure

```
src/nyc_mobility/
    common/         database access, manifest and run bookkeeping, HTTP session, checksums
    ingestion/      downloads and schema validation for taxi and weather
    loaders/        row-group streaming loads with the quality filter and quarantine
    validation/     data contracts and named quality rules
    orchestration/  the monthly pipeline and the backfill runner
dbt/
    models/staging/ one view per source: renaming, casting, derivations
    models/core/    fact_trips, fact_weather, dim_date, dim_zone, dim_payment_type
    seeds/          taxi zone lookup
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
- [x] DE-006: dbt foundation, staging models, sources, data tests
- [x] DE-007: core star schema with `fact_trips`, `fact_weather`, and dimensions
- [ ] DE-008: data marts for the dashboard
- [ ] Airflow orchestration of the monthly flow
- [ ] Power BI dashboard

## Data sources

- [NYC Taxi and Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), yellow taxi trip records
- [Open-Meteo](https://open-meteo.com/), historical weather API
