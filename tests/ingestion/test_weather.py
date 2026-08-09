"""Tests for nyc_mobility.ingestion.weather download logic."""

import json
from unittest.mock import MagicMock, patch

import pytest

from nyc_mobility.ingestion.weather import download_weather_data

# ---------------------------------------------------------------------------
# Unit tests (mocked I/O)
# ---------------------------------------------------------------------------


@patch("nyc_mobility.ingestion.weather.get_retry_session")
def test_download_weather_data(mock_get_retry_session, tmp_path):
    dest_path = tmp_path / "test_weather.json"
    mock_session = MagicMock()
    mock_response = MagicMock()
    params = MagicMock()

    mock_get_retry_session.return_value = mock_session
    mock_session.get.return_value = mock_response

    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"NY": 23}

    download_weather_data(params, str(dest_path))

    mock_get_retry_session.assert_called_once()
    mock_session.get.assert_called_once_with(
        "https://archive-api.open-meteo.com/v1/archive", params=params, timeout=(5, 30)
    )

    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()

    assert dest_path.exists()

    with open(dest_path, encoding="UTF-8") as f:
        saved_data = json.load(f)

    assert saved_data == {"NY": 23}


# ---------------------------------------------------------------------------
# Integration tests (live network) — skip by default, run with:
#   pytest -m integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skip(reason="hits live TLC endpoint - run manually")
def test_download_weather_data_live(tmp_path):
    print("[LOG] Starting download...")

    from nyc_mobility.ingestion.weather import build_params, download_weather_data

    dest = tmp_path / "test_weather.json"

    params = build_params(2023, 1)
    download_weather_data(params, str(dest))

    assert dest.exists()
    assert dest.stat().st_size > 0
