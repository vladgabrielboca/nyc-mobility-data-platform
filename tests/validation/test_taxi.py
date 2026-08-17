from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from nyc_mobility.validation.schema import validate_taxi_schema

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


def write_taxi_parquet(table, dir_, filename):
    pq.write_table(table, dir_ / filename)


def test_happy_path(tmp_path):
    table = pa.Table.from_pydict(TAXI_DATA, schema=TAXI_SCHEMA)
    write_taxi_parquet(table, tmp_path, "good.parquet")

    validate_taxi_schema(tmp_path / "good.parquet")


def test_missing_column(tmp_path):
    table = pa.Table.from_pydict(TAXI_DATA, schema=TAXI_SCHEMA).drop(["VendorID"])
    write_taxi_parquet(table, tmp_path, "missing.parquet")

    with pytest.raises(ValueError, match="VendorID"):
        validate_taxi_schema(tmp_path / "missing.parquet")


def test_wrong_type(tmp_path):
    wrong_type_schema = pa.schema(
        [
            field.with_type(pa.int64()) if field.name == "fare_amount" else field
            for field in TAXI_SCHEMA
        ]
    )
    table = pa.Table.from_pydict(TAXI_DATA, schema=wrong_type_schema)
    write_taxi_parquet(table, tmp_path, "wrong_type.parquet")

    with pytest.raises(ValueError, match="fare_amount"):
        validate_taxi_schema(tmp_path / "wrong_type.parquet")
