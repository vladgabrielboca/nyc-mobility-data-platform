import os

import pandas as pd
import pyarrow.parquet as pq

from nyc_mobility.common.db import get_connection
from nyc_mobility.validation.rules import split_valid_rejected

TAXI_COLUMN_MAPPING = {
    "VendorID": "vendor_id",
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "RatecodeID": "rate_code_id",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "PULocationID": "pickup_location_id",
    "DOLocationID": "dropoff_location_id",
    "payment_type": "payment_type",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "total_amount": "total_amount",
    "congestion_surcharge": "congestion_surcharge",
    "airport_fee": "airport_fee",
}

postgres_columns = [
    "vendor_id",
    "pickup_datetime",
    "dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "rate_code_id",
    "store_and_fwd_flag",
    "pickup_location_id",
    "dropoff_location_id",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount",
    "congestion_surcharge",
    "airport_fee",
    "source_year",
    "source_month",
]


def transform_taxi_batch(batch, year: int, month: int):
    """Pure: Pandas DataFrame -> CSV String. No DB."""
    # Add source_year and source_month columns
    batch["source_year"] = year
    batch["source_month"] = month

    # Align columns with the order in the COPY statement
    batch = batch[postgres_columns]
    return batch.to_csv(index=False, header=False, na_rep="")


def load_taxi_data_idempotent(year: int, month: int) -> None:
    path = f"data/raw/taxi/year={year}/month={month:02d}/trips.parquet"

    print(f"[LOG] Opening parquet file: {path}")
    parquet_file = pq.ParquetFile(path)

    # Define the columns in the order expected by the COPY statement
    columns_str = ", ".join(postgres_columns)

    with get_connection() as conn:
        with conn.cursor() as cur:
            print(
                f"[LOG - Taxi] Cleaning old data for year = {year} and month = {month:02d}..."
            )
            cur.execute(
                """
                DELETE FROM raw.yellow_taxi_trips
                WHERE source_year = %s
                AND source_month = %s
                """,
                (year, month),
            )

            # Load: Preparing for bulk copy operation
            print("[LOG] Initiating stream COPY in Postgres...")
            copy_sql = f"COPY raw.yellow_taxi_trips ({columns_str}) FROM STDIN WITH (FORMAT csv, HEADER false, DELIMITER ',')"

            counts = {}
            rejected_rows = []

            with cur.copy(copy_sql) as copy:  # type: ignore
                for i in range(parquet_file.num_row_groups):
                    print(
                        f"[LOG] Processing row group {i + 1} of {parquet_file.num_row_groups}..."
                    )
                    batch = parquet_file.read_row_groups([i]).to_pandas()

                    # Rename columns to match PostgreSQL table
                    batch = batch.rename(columns=TAXI_COLUMN_MAPPING)

                    valid, rejected, batch_counts = split_valid_rejected(batch)
                    for rule_name, n in batch_counts.items():
                        counts[rule_name] = counts.get(rule_name, 0) + n
                    rejected_rows.append(rejected)

                    csv_batch = transform_taxi_batch(valid, year, month)
                    copy.write(csv_batch)

            rejected_df = (
                pd.concat(rejected_rows, ignore_index=True)
                if rejected_rows
                else pd.DataFrame()
            )

            if not rejected_df.empty:
                print(f"[LOG] Total bad rows: {len(rejected_df)}")

                dest_path = f"data/quarantine/taxi/year={year}/month={month:02d}/rejected.parquet"

                print("[LOG] Saving rejected rows to quarantine...")
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                rejected_df.to_parquet(dest_path)
                print("[LOG] Rejected rows saved to quarantine.")
            else:
                print("[LOG] No rejected rows found for this period.")

            print("[LOG] Cleaning data_quality_results table...")
            cur.execute(
                """
                DELETE FROM
                ops.data_quality_results
                WHERE source = 'taxi' AND year = %s AND month = %s
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
                    VALUES ('taxi', %s, %s, %s, %s, NOW())
                    """,
                    (
                        year,
                        month,
                        rule_name,
                        rejected_count,
                    ),
                )

        print(f"[LOG] Transaction completed successfully for {year}-{month:02d}!")
