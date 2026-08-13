import pandas as pd

from json import load as json_load

from nyc_mobility.common.db import get_connection

postgres_columns = [
    "time",
    "temperature_2m",
    "precipitation",
    "windspeed_10m",
    "source_year",
    "source_month",
]


def transform_weather_data(data, year: int, month: int):
    df = pd.DataFrame(data)

    # Add source_year and source_month columns
    df["source_year"] = year
    df["source_month"] = month

    # Align columns with the order in the COPY statement
    df = df[postgres_columns]

    return df.to_csv(index=False, header=False, na_rep="")


def load_weather_data_idempotent(year: int, month: int) -> None:
    path = f"data/raw/weather/year={year}/month={month:02d}/weather.json"

    print("[LOG] Opening JSON file...")
    with open(path, "r") as file:
        print("[LOG] Reading JSON file...")
        data = json_load(file)
        data = data["hourly"]

    print("[LOG] Transforming data...")
    data = transform_weather_data(data, year, month)

    with get_connection() as conn:
        with conn.cursor() as cur:
            print(
                f"[LOG - Weather] Cleaning old data for year = {year} and month = {month:02d}"
            )
            cur.execute(
                """
                DELETE FROM raw.weather_hourly
                WHERE source_year = %s
                AND source_month = %s
                """,
                (year, month),
            )

            columns_str = ", ".join(postgres_columns)
            print("[LOG] Initiating stream COPY in Postgres...")
            copy_sql = f"COPY raw.weather_hourly ({columns_str}) FROM STDIN WITH (FORMAT CSV, header false, DELIMITER ',')"

            with cur.copy(copy_sql) as copy:  # type: ignore
                copy.write(data)

        print(f"[LOG] Transaction completed successfully for {year}-{month:02d}!")
