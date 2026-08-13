import json
from pathlib import Path

import pandas as pd


def make_taxi_fixture(year=2023, month=1):
    out = Path(f"data/raw/taxi/year={year}/month={month:02d}/trips.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
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

    df.to_parquet(out, index=False)


def make_weather_fixture(year=2023, month=1):
    out = Path(f"data/raw/weather/year={year}/month={month:02d}/weather.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "hourly": {
                    "time": ["2023-01-01 00:00:00", "2023-01-01 01:00:00"],
                    "temperature_2m": [10.5, 11.2],
                    "precipitation": [0.0, 0.0],
                    "windspeed_10m": [5.0, 6.0],
                }
            }
        )
    )


if __name__ == "__main__":
    make_taxi_fixture()
    make_weather_fixture()
