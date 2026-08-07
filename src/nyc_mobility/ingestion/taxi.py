import os
import requests
import pyarrow.parquet as pq
import src.nyc_mobility.common.manifest as manifest
from src.nyc_mobility.common.utils import get_retry_session
from src.nyc_mobility.common.utils import compute_checksum

"""

    To build the correct URL, take this as an example:
    
    https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-01.parquet

    The above example retrieves the data for january 2026, so as a string it would be:

    https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet

"""

def build_taxi_url(year: int, month: int) -> str:
    return f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"


def count_rows(file_path: str) -> int:
    metadata = pq.read_metadata(file_path)
    return metadata.num_rows


def download_taxi_file(year: int, month: int, dest_path: str) -> None:
    """Download the taxi data from the NYC Taxi and Limousine Commission."""

    url = build_taxi_url(year, month)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Create a session using helper function from utils.py
    session = get_retry_session()

    try:
        print("[LOG] Requesting taxi data...")
        response = session.get(url, timeout=(5, 30))

        # throw an error if HTTP status is not: 200 OK
        response.raise_for_status()

        print("[LOG] Saving data to: {dest_path} ...")
        with open(dest_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        print(f"File for {year}-{month} has been succesfully downloaded!")
    except requests.exceptions.RequestException as e:
        print(f"Error while downloading the file: {e}")
        raise


def ingest_taxi_month(cursor, year: int, month: int) -> None:
    """Ingest the taxi data for a given year and month."""

    if manifest.has_successful_ingestion(cursor, "taxi", year, month):
        print(f"[LOG] Taxi data for {year}-{month} already ingested, skipping...")
        return

    manifest_id = manifest.start_ingestion_attempt(cursor, "taxi", year, month)

    try:
        dest_path = f"data/raw/taxi/year={year}/month={month:02d}/trips.parquet"
        download_taxi_file(year, month, dest_path)

        checksum = compute_checksum(dest_path)
        row_count = count_rows(dest_path)

        manifest.mark_ingestion_success(cursor, manifest_id, checksum, row_count)
        print(f"[LOG] Taxi data for {year}-{month} ingested successfully!")

    except Exception as e:
        manifest.mark_ingestion_failure(cursor, manifest_id, str(e))
        print(f"[LOG] Taxi data for {year}-{month} failed to ingest: {e}")
        raise