import pyarrow.parquet as pq

from nyc_mobility.common.db import get_connection

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
    """Pure: Arrow batch -> rows with stamped medatadata. No DB."""

    # Convert Arrow batch to Pandas DataFrame
    batch = batch.to_pandas()

    # Rename columns to match PostgreSQL table
    batch = batch.rename(columns=TAXI_COLUMN_MAPPING)

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

            with cur.copy(copy_sql) as copy:  # type: ignore
                for i in range(parquet_file.num_row_groups):
                    print(
                        f"[LOG] Processing row group {i + 1} of {parquet_file.num_row_groups}..."
                    )

                    batch = parquet_file.read_row_groups([i])
                    csv_batch = transform_taxi_batch(batch, year, month)
                    copy.write(csv_batch)

        print(f"[LOG] Transaction completed successfully for {year}-{month:02d}!")
