import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from nyc_mobility.validation.schema import validate_weather_schema


def make_broken_json(dir_, filename):
    out = Path(dir_, filename)

    out.write_text(
        json.dumps(
            {
                "hourly": {
                    "time": ["2023-01-01 00:00:00", "2023-01-01 01:00:00"],
                    "temperature_2m": [10.5, 11.2],
                    "precipitation": [0.0, 0.0],
                    "windspeed_10m": [5.0, 6.0],
                }
            }
        )
    )


def test_validate_weather_schema(tmp_path):
    make_broken_json(tmp_path, "weather.json")

    with pytest.raises(ValidationError):
        validate_weather_schema(tmp_path / "weather.json")
