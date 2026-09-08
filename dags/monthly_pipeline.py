import os
from datetime import datetime, timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task
from airflow.timetables.interval import CronDataIntervalTimetable

from nyc_mobility.common.db import get_connection
from nyc_mobility.ingestion.taxi import ingest_taxi_month
from nyc_mobility.ingestion.weather import ingest_weather_month
from nyc_mobility.loaders.taxi import load_taxi_data_idempotent
from nyc_mobility.loaders.weather import load_weather_data_idempotent

PROJECT_ROOT = os.path.expanduser("~/Projects/nyc-mobility-data-platform")
# pendulum timezone: the explicit timetable serializes with it; zoneinfo fails.
DATA_TIMEZONE = pendulum.timezone("America/New_York")
MIN_YEAR_MONTH = (2023, 1)


def year_month(
    data_interval_start: datetime | None, data_interval_end: datetime | None
) -> tuple[int, int]:
    """Return the month a run owns: the last full month before its interval end."""

    if data_interval_start is None or data_interval_end is None:
        raise ValueError("Run has no data interval - trigger with an explicit month.")
    end_ny = data_interval_end.astimezone(DATA_TIMEZONE)
    if data_interval_start == data_interval_end:
        month_start = datetime(end_ny.year, end_ny.month, 1, tzinfo=DATA_TIMEZONE)
        covered = month_start - timedelta(seconds=1)
    else:
        covered = end_ny - timedelta(seconds=1)
    owned_month = (covered.year, covered.month)
    if owned_month < MIN_YEAR_MONTH:
        raise ValueError(
            f"This run covers {owned_month[0]}-{owned_month[1]:02d}, before the "
            f"data window starts at 2023-01. Pick the month explicitly in the "
            f"trigger dialog, or use a backfill for a range of months."
        )
    return owned_month


@dag(
    dag_id="monthly_pipeline",
    # the run labeled M owns [M 1st -> M+1 1st)
    # and fires at the start of the next month, ingesting month M.
    schedule=CronDataIntervalTimetable("0 0 1 * *", DATA_TIMEZONE),
    start_date=datetime(2023, 1, 1, tzinfo=DATA_TIMEZONE),
    catchup=False,
    is_paused_upon_creation=True,
    # default_args={
    #     "retries": 2,
    #     "retry_delay": timedelta(minutes=5),
    # },
)
def monthly_pipeline():
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"{PROJECT_ROOT}/.venv/bin/dbt deps && {PROJECT_ROOT}/.venv/bin/dbt build",
        cwd=f"{PROJECT_ROOT}/dbt",
    )

    @task
    def ingest_taxi(
        data_interval_start: datetime | None = None,
        data_interval_end: datetime | None = None,
    ):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start, data_interval_end)
        with get_connection() as conn:
            with conn.cursor() as cur:
                ingest_taxi_month(cur, year, month)

    @task
    def load_taxi(
        data_interval_start: datetime | None = None,
        data_interval_end: datetime | None = None,
    ):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start, data_interval_end)
        load_taxi_data_idempotent(year, month)

    @task
    def ingest_weather(
        data_interval_start: datetime | None = None,
        data_interval_end: datetime | None = None,
    ):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start, data_interval_end)
        with get_connection() as conn:
            with conn.cursor() as cur:
                ingest_weather_month(cur, year, month)

    @task
    def load_weather(
        data_interval_start: datetime | None = None,
        data_interval_end: datetime | None = None,
    ):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start, data_interval_end)
        load_weather_data_idempotent(year, month)

    # Each call creates a task instance - call once, reuse the handle.
    t_ingest_taxi = ingest_taxi()
    t_ingest_weather = ingest_weather()
    t_load_taxi = load_taxi()
    t_load_weather = load_weather()

    t_ingest_taxi >> t_load_taxi
    t_ingest_weather >> t_load_weather
    [t_load_taxi, t_load_weather] >> dbt_build


monthly_pipeline()
