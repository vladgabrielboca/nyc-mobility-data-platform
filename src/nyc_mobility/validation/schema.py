import json

import pyarrow.parquet as pq
from jsonschema import ValidationError, validate


def validate_taxi_schema(file_path) -> None:
    """Validate whether or not the taxi parquet file has the expected schema."""

    # Define the expected schema
    expected_schema = {
        "VendorID": "int64",
        "tpep_pickup_datetime": "timestamp[us]",
        "tpep_dropoff_datetime": "timestamp[us]",
        "passenger_count": "double",
        "trip_distance": "double",
        "RatecodeID": "double",
        "store_and_fwd_flag": "string",
        "PULocationID": "int64",
        "DOLocationID": "int64",
        "payment_type": "int64",
        "fare_amount": "double",
        "extra": "double",
        "mta_tax": "double",
        "tip_amount": "double",
        "tolls_amount": "double",
        "improvement_surcharge": "double",
        "total_amount": "double",
        "congestion_surcharge": "double",
        "airport_fee": "double",
    }

    # Read the parquet file
    parquet_file = pq.ParquetFile(file_path)

    # Get the actual schema
    actual_schema = parquet_file.schema.to_arrow_schema()

    # Compare the actual schema with the expected schema
    for column, dtype in expected_schema.items():
        if column not in actual_schema.names:
            raise ValueError(f"Column '{column}' is missing in the parquet file.")

        actual_type_str = str(actual_schema.field(column).type)

        if actual_type_str != dtype:
            raise ValueError(
                f"Column '{column}' has an unexpected data type. Expected: {dtype}, Actual: {actual_type_str}"
            )

    print("Schema validation passed. The parquet file has the expected schema.")


def validate_weather_schema(file_path) -> None:
    """Validate whether the weather data has the expected schema or not."""

    # Define the expected JSON schema
    expected_schema = {
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
            "generationtime_ms": {"type": "number"},
            "utc_offset_seconds": {"type": "number"},
            "timezone": {"type": "string"},
            "timezone_abbreviation": {"type": "string"},
            "elevation": {"type": "number"},
            "hourly_units": {
                "type": "object",
                "properties": {
                    "time": {"type": "string"},
                    "temperature_2m": {"type": "string"},
                    "precipitation": {"type": "string"},
                    "windspeed_10m": {"type": "string"},
                },
            },
            "hourly": {
                "type": "object",
                "properties": {
                    "time": {"type": "array", "items": {"type": "string"}},
                    "temperature_2m": {"type": "array", "items": {"type": "number"}},
                    "precipitation": {"type": "array", "items": {"type": "number"}},
                    "windspeed_10m": {"type": "array", "items": {"type": "number"}},
                },
            },
        },
        "required": [
            "latitude",
            "longitude",
            "generationtime_ms",
            "utc_offset_seconds",
            "timezone",
            "timezone_abbreviation",
            "elevation",
            "hourly_units",
            "hourly",
        ],
    }

    # Load the JSON data from the file
    with open(file_path, encoding="UTF-8") as file:
        data = json.load(file)

    try:
        validate(instance=data, schema=expected_schema)
        print("JSON data is valid!")
    except ValidationError as e:
        print(f"JSON data is invalid: {e}")
        raise
