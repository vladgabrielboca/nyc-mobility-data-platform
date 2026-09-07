import os
from datetime import datetime

from airflow.sdk import dag, task

from src.nyc_mobility.common.db import get_connection
from src.nyc_mobility.ingestion.taxi import ingest_taxi_month
from src.nyc_mobility.loaders.taxi import load_taxi_data_idempotent

PROJECT_ROOT = "/home/vlad/Projects/nyc-mobility-data-platform"

@dag(
    dag_id="monthly_pipeline",
    schedule="@monthly",
    start_date=datetime(2023, 1, 1),
    catchup=False
)
def monthly_pipeline():

    @task
    def ingest_taxi(data_interval_start: datetime | None = None):
        assert data_interval_start is not None
        os.chdir(PROJECT_ROOT)
        year, month = data_interval_start.year, data_interval_start.month
        with get_connection() as conn:
            with conn.cursor() as cur:
                ingest_taxi_month(cur, year, month)

    @task
    def load_taxi(data_interval_start: datetime | None = None):
        assert data_interval_start is not None
        os.chdir(PROJECT_ROOT)
        year, month = data_interval_start.year, data_interval_start.month
        load_taxi_data_idempotent(year, month)

    ingest_taxi() >> load_taxi()
