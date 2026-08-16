from datetime import datetime

import pyarrow as pa
import pytest

from nyc_mobility.common.db import get_connection
from nyc_mobility.loaders.taxi import (
    TAXI_COLUMN_MAPPING,
    load_taxi_data_idempotent,
    transform_taxi_batch,
)

TAXI_DATA = {
    "VendorID": [1, 2],
    "tpep_pickup_datetime": [datetime(2023, 1, 1), datetime(2023, 1, 2)],
    "tpep_dropoff_datetime": [datetime(2023, 1, 1, 1), datetime(2023, 1, 2, 1)],
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

TAXI_SCHEMA = pa.schema(
    [
        ("VendorID", pa.int64()),
        ("tpep_pickup_datetime", pa.timestamp("us")),
        ("tpep_dropoff_datetime", pa.timestamp("us")),
        ("passenger_count", pa.float64()),
        ("trip_distance", pa.float64()),
        ("RatecodeID", pa.float64()),
        ("store_and_fwd_flag", pa.string()),
        ("PULocationID", pa.int64()),
        ("DOLocationID", pa.int64()),
        ("payment_type", pa.int64()),
        ("fare_amount", pa.float64()),
        ("extra", pa.float64()),
        ("mta_tax", pa.float64()),
        ("tip_amount", pa.float64()),
        ("tolls_amount", pa.float64()),
        ("improvement_surcharge", pa.float64()),
        ("total_amount", pa.float64()),
        ("congestion_surcharge", pa.float64()),
        ("airport_fee", pa.float64()),
    ]
)


def test_transform_taxi_data():
    table = pa.Table.from_pydict(TAXI_DATA, schema=TAXI_SCHEMA)
    # transform_taxi_batch expects canonical (renamed) columns, like the loader passes
    df = table.to_pandas().rename(columns=TAXI_COLUMN_MAPPING)

    result = transform_taxi_batch(df, 2023, 1)

    assert "2023,1" in result  # metadata


def count_rows(source_year: int, source_month: int) -> int:
    """Helper: count rows from a specific row from raw.yellow_taxi_trips."""
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
