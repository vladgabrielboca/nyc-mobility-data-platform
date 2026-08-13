from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from nyc_mobility.loaders.weather import transform_weather_data
from nyc_mobility.loaders.weather import load_weather_data_idempotent
from nyc_mobility.common.db import get_connection

def test_transform_weather_data():
    mock_df_data = {
        "time": ["2023-01-01 00:00:00", "2023-01-01 01:00:00"],
        "temperature_2m": [10.5, 11.2],
        "precipitation": [0.0, 0.0],
        "windspeed_10m": [5.0, 6.0]
    }

    year, month = 2023, 1
    result = transform_weather_data(mock_df_data, year, month)
    expected_csv = "2023-01-01 00:00:00,10.5,0.0,5.0,2023,1\n2023-01-01 01:00:00,11.2,0.0,6.0,2023,1\n"
    assert result == expected_csv, f"Expected CSV:\n{expected_csv}\nActual CSV:\n{result}"


def count_rows(source_year: int, source_month: int) -> int:
    """Helper: numără rândurile pentru o lună anume din raw.yellow_taxi_trips."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM raw.weather_hourly
                WHERE source_year = %s AND source_month = %s
                """,
                (source_year, source_month),
            )
            row = cur.fetchone()
            return row[0] if row is not None else 0


@pytest.fixture
def clean_weather():
    yield
    # after testing, delete the data we inserted
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM raw.weather_hourly WHERE source_year = %s AND source_month = %s",
                (2023, 1)
            )


@pytest.mark.integration
def test_weather_load_is_idempotent(clean_weather):
    year, month = 2023, 1

    # First load
    load_weather_data_idempotent(year, month)
    count_after_first = count_rows(year, month)

    assert count_after_first > 0

    # Second load
    load_weather_data_idempotent(year, month)
    count_after_second = count_rows(year, month)

    assert count_after_second == count_after_first
