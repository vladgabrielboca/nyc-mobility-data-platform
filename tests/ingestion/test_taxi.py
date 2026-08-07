# tests/ingestion/test_taxi.py


def test_download_taxi_file(tmp_path):
    print("[LOG] Starting download...")
    from nyc_mobility.ingestion.taxi import download_taxi_file

    dest = tmp_path / "test_download.parquet"
    download_taxi_file(2026, 1, str(dest))

    assert dest.exists()
    assert dest.stat().st_size > 0
