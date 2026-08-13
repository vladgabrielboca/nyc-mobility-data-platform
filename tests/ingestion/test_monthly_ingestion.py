# tests/ingestion/test_monthly_ingestion.py

from unittest.mock import MagicMock, patch

import pytest

from nyc_mobility.orchestration.monthly import run_monthly_ingestion


@patch("nyc_mobility.orchestration.monthly.load_taxi_data_idempotent")
@patch("nyc_mobility.orchestration.monthly.load_weather_data_idempotent")
@patch("nyc_mobility.orchestration.monthly.ingest_taxi_month")
@patch("nyc_mobility.orchestration.monthly.ingest_weather_month")
@patch("nyc_mobility.orchestration.monthly.pipeline")
def test_monthly_ingestion_success(mock_pipeline, mock_weather, mock_taxi, mock_load_weather, mock_load_taxi):
    mock_cursor = MagicMock()
    year, month = 2023, 1

    mock_pipeline.start_pipeline_run.return_value = 42

    run_monthly_ingestion(mock_cursor, year, month)

    mock_pipeline.start_pipeline_run.assert_called_once_with(
        mock_cursor, "monthly_ingestion", year, month
    )

    mock_taxi.assert_called_once_with(mock_cursor, year, month)
    mock_weather.assert_called_once_with(mock_cursor, year, month)

    mock_pipeline.mark_pipeline_run_success.assert_called_once_with(mock_cursor, 42)
    mock_pipeline.mark_pipeline_run_failure.assert_not_called()


@patch("nyc_mobility.orchestration.monthly.ingest_taxi_month")
@patch("nyc_mobility.orchestration.monthly.ingest_weather_month")
@patch("nyc_mobility.orchestration.monthly.pipeline")
def test_monthly_ingestion_failure(mock_pipeline, mock_weather, mock_taxi):
    mock_cursor = MagicMock()
    year, month = 2023, 1

    mock_pipeline.start_pipeline_run.return_value = 99

    mock_taxi.side_effect = Exception("The taxi API is down!")

    with pytest.raises(Exception, match="The taxi API is down!"):
        run_monthly_ingestion(mock_cursor, year, month)

    mock_pipeline.mark_pipeline_run_failure.assert_called_once_with(mock_cursor, 99)

    mock_pipeline.mark_pipeline_run_success.assert_not_called()
