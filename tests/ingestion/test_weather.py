# tests/ingestion/test_weather.py


def test_download_weather_data(tmp_path):
    print("[LOG] Starting download...")

    from nyc_mobility.ingestion.weather import build_params, download_weather_data

    dest = tmp_path / "test_weather.json"

    params = build_params(2023, 1)
    download_weather_data(params, str(dest))

    assert dest.exists()
    assert dest.stat().st_size > 0
