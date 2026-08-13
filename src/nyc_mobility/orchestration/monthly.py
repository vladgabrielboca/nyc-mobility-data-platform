import nyc_mobility.common.pipeline as pipeline
from nyc_mobility.ingestion.taxi import ingest_taxi_month
from nyc_mobility.ingestion.weather import ingest_weather_month
from nyc_mobility.loaders.taxi import load_taxi_data_idempotent
from nyc_mobility.loaders.weather import load_weather_data_idempotent


def run_monthly_ingestion(cursor, year: int, month: int) -> None:
    """Run the full ingestion: taxi + weather, wrapped in a pipeline run."""

    run_id = pipeline.start_pipeline_run(cursor, "monthly_ingestion", year, month)

    try:
        # Ingest data
        ingest_taxi_month(cursor, year, month)
        ingest_weather_month(cursor, year, month)

        # Load data
        load_taxi_data_idempotent(year, month)
        load_weather_data_idempotent(year, month)

        pipeline.mark_pipeline_run_success(cursor, run_id)
        print(f"[LOG] Monthly ingestion for {year}-{month} completed successfully!")

    except Exception as e:
        pipeline.mark_pipeline_run_failure(cursor, run_id)
        print(f"[LOG] Monthly ingestion for {year}-{month} failed to complete: {e}")
        raise
