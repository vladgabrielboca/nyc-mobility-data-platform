import calendar
import hashlib
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def get_retry_session(
    total_retries: int = 3, backoff_factor: int = 1
) -> requests.Session:
    retry_strategy = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )

    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def compute_checksum(file_path: str) -> str:
    with open(file_path, "rb") as file:
        digest_object = hashlib.file_digest(file, "sha256")

    checksum = digest_object.hexdigest()
    return checksum


def find_start_end_month(year: int, month: int) -> tuple[str, Any]:
    """Find the start and end month of the given year"""
    _, last_day = calendar.monthrange(year, month)

    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    return start_date, end_date
