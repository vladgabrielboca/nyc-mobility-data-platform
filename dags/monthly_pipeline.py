import os
from datetime import datetime

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task

from nyc_mobility.common.db import get_connection
from nyc_mobility.ingestion.taxi import ingest_taxi_month
from nyc_mobility.ingestion.weather import ingest_weather_month
from nyc_mobility.loaders.taxi import load_taxi_data_idempotent
from nyc_mobility.loaders.weather import load_weather_data_idempotent

PROJECT_ROOT = os.path.expanduser("~/Projects/nyc-mobility-data-platform")

DATA_WINDOW_START = datetime(2023, 1, 1)


def year_month(data_interval_start: datetime | None) -> tuple[int, int]:
    """Derive the target month, refusing runs outside the platform's data window."""
    if data_interval_start is None or data_interval_start < DATA_WINDOW_START:
        raise ValueError(
            f"Logical date {data_interval_start} is before the data window "
            f"start {DATA_WINDOW_START:%Y-%m}. Airflow's manual trigger defaults "
            f"to the last complete interval - pick the month explicitly."
        )
    return data_interval_start.year, data_interval_start.month


@dag(
    dag_id="monthly_pipeline",
    schedule="@monthly",
    start_date=datetime(2023, 1, 1),
    catchup=False,
)
def monthly_pipeline():
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"{PROJECT_ROOT}/.venv/bin/dbt deps && {PROJECT_ROOT}/.venv/bin/dbt build",
        cwd=f"{PROJECT_ROOT}/dbt",
    )

    @task
    def ingest_taxi(data_interval_start: datetime | None = None):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start)
        with get_connection() as conn:
            with conn.cursor() as cur:
                ingest_taxi_month(cur, year, month)

    @task
    def load_taxi(data_interval_start: datetime | None = None):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start)
        load_taxi_data_idempotent(year, month)

    @task
    def ingest_weather(data_interval_start: datetime | None = None):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start)
        with get_connection() as conn:
            with conn.cursor() as cur:
                ingest_weather_month(cur, year, month)

    @task
    def load_weather(data_interval_start: datetime | None = None):
        os.chdir(PROJECT_ROOT)
        year, month = year_month(data_interval_start)
        load_weather_data_idempotent(year, month)

    ingest_taxi() >> load_taxi()
    ingest_weather() >> load_weather()
    [load_taxi(), load_weather()] >> dbt_build


monthly_pipeline()
