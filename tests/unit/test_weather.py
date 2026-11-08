from unittest.mock import Mock

import pytest
import requests

from src.services.weather import WeatherService
from src.utils.errors import ApiError


def response(payload):
    obj = Mock()
    obj.json.return_value = payload
    return obj


def test_success():
    session = Mock()
    session.get.side_effect = [
        response(
            {"results": [{"name": "Taipei", "latitude": 25, "longitude": 121, "country": "Taiwan"}]}
        ),
        response(
            {
                "current": {
                    "time": "2026-11-08T12:00",
                    "temperature_2m": 25,
                    "weather_code": 0,
                    "wind_speed_10m": 10,
                },
                "current_units": {"temperature_2m": "°C"},
            }
        ),
    ]
    result = WeatherService(session).query("Taipei")
    assert result["current"]["temperature_2m"] == 25
    assert session.get.call_count == 2
    assert session.get.call_args.kwargs["timeout"] == (2, 3)


@pytest.mark.parametrize(
    "exception,code",
    [
        (requests.Timeout(), 504),
        (requests.ConnectionError(), 502),
        (requests.HTTPError(), 502),
        (ValueError(), 502),
    ],
)
def test_provider_errors(exception, code):
    session = Mock()
    session.get.side_effect = exception
    with pytest.raises(ApiError) as err:
        WeatherService(session).query("Taipei")
    assert err.value.status == code


def test_http_error_response():
    session = Mock()
    session.get.return_value.raise_for_status.side_effect = requests.HTTPError("upstream secret")
    with pytest.raises(ApiError) as err:
        WeatherService(session).query("Taipei")
    assert err.value.status == 502 and "secret" not in err.value.message


@pytest.mark.parametrize("value", ["", "x", "a" * 81, "<script>", None, "Taipei1"])
def test_bad_city(value):
    with pytest.raises(ApiError) as err:
        WeatherService(Mock()).query(value)
    assert err.value.status == 400


def test_city_not_found():
    session = Mock()
    session.get.return_value = response({"results": []})
    with pytest.raises(ApiError) as err:
        WeatherService(session).query("Nowhere")
    assert err.value.status == 404


def test_invalid_upstream_schema():
    session = Mock()
    session.get.return_value = response({"results": [None]})
    with pytest.raises(ApiError) as err:
        WeatherService(session).query("Taipei")
    assert err.value.status == 502
