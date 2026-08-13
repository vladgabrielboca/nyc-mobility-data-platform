import pyarrow as pa
import pytest

from nyc_mobility.common.db import get_connection
from nyc_mobility.loaders.taxi import load_taxi_data_idempotent, transform_taxi_batch


def test_transform_taxi_data():
    batch = pa.table(
        {
            "VendorID": [1, 2],
            "tpep_pickup_datetime": ["2023-01-01 00:00:00", "2023-01-02 00:00:00"],
            "tpep_dropoff_datetime": ["2023-01-01 01:00:00", "2023-01-02 01:00:00"],
            "passenger_count": [1.0, 2.0],
            "trip_distance": [1.5, 2.5],
            "RatecodeID": [1.0, 1.0],
            "store_and_fwd_flag": ["N", "N"],
            "PULocationID": [100, 200],
            "DOLocationID": [150, 250],
            "payment_type": [1, 1],
            "fare_amount": [10.0, 20.0],
            "extra": [0.5, 0.5],
            "mta_tax": [0.5, 0.5],
            "tip_amount": [2.0, 3.0],
            "tolls_amount": [0.0, 0.0],
            "improvement_surcharge": [1.0, 1.0],
            "total_amount": [14.0, 25.0],
            "congestion_surcharge": [2.5, 2.5],
            "airport_fee": [0.0, 0.0],
        }
    )

    result = transform_taxi_batch(batch, 2023, 1)

    assert "2023,1" in result  # metadata


def count_rows(source_year: int, source_month: int) -> int:
    """Helper: numără rândurile pentru o lună anume din raw.yellow_taxi_trips."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM raw.yellow_taxi_trips
                WHERE source_year = %s AND source_month = %s
                """,
                (source_year, source_month),
            )
            row = cur.fetchone()
            return row[0] if row is not None else 0


@pytest.fixture
def clean_taxi():
    yield
    # after testing, delete the data we inserted
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM raw.yellow_taxi_trips WHERE source_year = %s AND source_month = %s",
                (2023, 1),
            )


@pytest.mark.integration
def test_taxi_load_is_idempotent(clean_taxi):
    year, month = 2023, 1

    # First load
    load_taxi_data_idempotent(year, month)
    count_after_first = count_rows(year, month)

    assert count_after_first > 0

    # Second load
    load_taxi_data_idempotent(year, month)
    count_after_second = count_rows(year, month)

    assert count_after_second == count_after_first
