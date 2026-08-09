"""Tests for nyc_mobility.ingestion.taxi download logic."""

from unittest.mock import MagicMock, patch

import pytest

from nyc_mobility.ingestion.taxi import download_taxi_file

# ---------------------------------------------------------------------------
# Unit tests (mocked I/O)
# ---------------------------------------------------------------------------


@patch("nyc_mobility.ingestion.taxi.get_retry_session")
@patch("nyc_mobility.ingestion.taxi.build_taxi_url")
def test_download_taxi_file(mock_build_url, mock_get_retry_session, tmp_path):
    year, month = 2023, 1
    dest = tmp_path / "taxi.parquet"

    mock_build_url.return_value = "https://example.com"

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_get_retry_session.return_value = mock_session
    mock_session.get.return_value = mock_response
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"fake content"]

    download_taxi_file(year, month, str(dest))

    mock_get_retry_session.assert_called_once()
    mock_session.get.assert_called_once_with(
        mock_build_url.return_value, timeout=(5, 30)
    )
    mock_response.iter_content.assert_called_once()
    assert dest.read_bytes() == b"fake content"


# ---------------------------------------------------------------------------
# Integration tests (live network) — skip by default, run with:
#   pytest -m integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skip(reason="hits live TLC endpoint - run manually")
def test_download_taxi_file_live(tmp_path):
    dest = tmp_path / "test_download.parquet"
    download_taxi_file(2026, 1, str(dest))

    assert dest.exists()
    assert dest.stat().st_size > 0
