import calendar
import json
import os

import requests

import nyc_mobility.common.manifest as manifest
from nyc_mobility.common.utils import compute_checksum, get_retry_session


def find_start_end_month(year: int, month: int) -> tuple[str, str]:
    """Find the start and end month of the given year"""
    _, last_day = calendar.monthrange(year, month)

    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    return start_date, end_date


def build_params(year: int, month: int) -> dict:
    """Build the params for the weather API."""

    start_date, end_date = find_start_end_month(year, month)

    params = {
        "latitude": 40.71,
        "longitude": -74.01,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation,windspeed_10m",
        "timezone": "America/New_York",
    }

    return params


def count_rows(file_path: str) -> int:
    with open(file_path, encoding="UTF-8") as file:
        data = json.load(file)

    return len(data["hourly"]["time"])


def download_weather_data(params: dict, dest_path: str) -> None:
    """Download the weather data from the Open-Meteo API."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Create a session using helper function from utils.py
    session = get_retry_session()

    try:
        print("[LOG] Requesting weather data...")
        response = session.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params=params,
            timeout=(5, 30),
        )

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        print("[LOG] Converting response to JSON...")
        data = response.json()

        print(f"[LOG] Saving data to: {dest_path} ...")
        with open(dest_path, "w", encoding="UTF-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print("File has been succesfully downloaded!")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading weather data: {e}")
        raise


def ingest_weather_month(cursor, year: int, month: int) -> None:
    """Ingest the weather data for a given year and month."""

    if manifest.has_successful_ingestion(cursor, "weather", year, month):
        print(f"[LOG] Weather data for {year}-{month} already ingested, skipping...")
        return

    manifest_id = manifest.start_ingestion_attempt(cursor, "weather", year, month)

    try:
        dest_path = f"data/raw/weather/year={year}/month={month:02d}/weather.json"
        params = build_params(year, month)
        download_weather_data(params, dest_path)

        checksum = compute_checksum(dest_path)
        row_count = count_rows(dest_path)
        manifest.mark_ingestion_success(cursor, manifest_id, checksum, row_count)

    except Exception as e:
        manifest.mark_ingestion_failure(cursor, manifest_id, str(e))
        print(f"Error ingesting weather data: {e}")
        raise
