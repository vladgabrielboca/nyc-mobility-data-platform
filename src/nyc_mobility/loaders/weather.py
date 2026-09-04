import os
from json import load as json_load

import pandas as pd

from nyc_mobility.common.db import get_connection
from nyc_mobility.validation.rules import WEATHER_RULES, split_valid_rejected

postgres_columns = [
    "time",
    "temperature_2m",
    "precipitation",
    "windspeed_10m",
    "source_year",
    "source_month",
]


def transform_weather_data(data, year: int, month: int):
    # Add source_year and source_month columns
    data["source_year"] = year
    data["source_month"] = month

    # Align columns with the order in the COPY statement
    data = data[postgres_columns]

    return data.to_csv(index=False, header=False, na_rep="")


def load_weather_data_idempotent(year: int, month: int) -> None:
    path = f"data/raw/weather/year={year}/month={month:02d}/weather.json"

    print("[LOG] Opening JSON file...")
    with open(path) as file:
        print("[LOG] Reading JSON file...")
        data = json_load(file)
        data = data["hourly"]

    print("[LOG] Transforming data...")
    data = pd.DataFrame(data)
    data["time"] = pd.to_datetime(data["time"], errors="coerce")

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

            counts = {}
            rejected_rows = []

            with cur.copy(copy_sql) as copy:  # type: ignore
                valid, rejected, batch_counts = split_valid_rejected(
                    data, year, month, WEATHER_RULES
                )
                for rule_name, n in batch_counts.items():
                    counts[rule_name] = counts.get(rule_name, 0) + n
                rejected_rows.append(rejected)

                csv_data = transform_weather_data(valid, year, month)
                copy.write(csv_data)

            rejected_df = (
                pd.concat(rejected_rows, ignore_index=True)
                if rejected_rows
                else pd.DataFrame()
            )

            if not rejected_df.empty:
                print(f"[LOG] Total bad rows: {len(rejected_df)}")

                dest_path = f"data/quarantine/weather/year={year}/month={month:02d}/rejected.csv"

                print("[LOG] Saving rejected rows to quarantine...")
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                rejected_df.to_csv(dest_path, index=False)
                print("[LOG] Rejected rows saved to quarantine.")
            else:
                print("[LOG] No rejected rows found for this period.")

            print("[LOG] Cleaning data_quality_results table...")
            cur.execute(
                """
                DELETE FROM
                ops.data_quality_results
                WHERE source = 'weather' AND year = %s AND month = %s
                """,
                (year, month),
            )
            print("[LOG] Cleaning complete.")

            print("[LOG] Inserting counts into data_quality_results table...")

            for rule_name, rejected_count in counts.items():
                cur.execute(
                    """
                    INSERT INTO
                    ops.data_quality_results
                    (source, year, month, rule_name, rejected_count, checked_at)
                    VALUES ('weather', %s, %s, %s, %s, NOW())
                    """,
                    (
                        year,
                        month,
                        rule_name,
                        rejected_count,
                    ),
                )

        print(f"[LOG] Transaction completed successfully for {year}-{month:02d}!")
