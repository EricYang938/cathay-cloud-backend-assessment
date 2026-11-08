import requests

from src.models.validation import city
from src.utils.errors import ApiError


class WeatherService:
    def __init__(self, session=None):
        self.session = session or requests.Session()

    def query(self, value):
        value = city(value)
        try:
            geo = self._get(
                "https://geocoding-api.open-meteo.com/v1/search",
                {"name": value, "count": 1, "language": "en", "format": "json"},
            )
            matches = geo.get("results")
            if not matches:
                raise ApiError(404, "CITY_NOT_FOUND", "City not found")
            place = matches[0]
            weather = self._get(
                "https://api.open-meteo.com/v1/forecast",
                {
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,weather_code,wind_speed_10m",
                    "timezone": "UTC",
                },
            )
            current, units = weather["current"], weather["current_units"]
            # Validate upstream schema before reporting success.
            for key in ("time", "temperature_2m", "weather_code", "wind_speed_10m"):
                if key not in current:
                    raise ValueError("Missing current field")
            return {
                "city": place["name"],
                "country": place.get("country", ""),
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": current,
                "units": units,
                "timezone": "UTC",
                "source": "Open-Meteo",
                "source_url": "https://open-meteo.com/",
            }
        except requests.Timeout:
            raise ApiError(504, "WEATHER_TIMEOUT", "Weather provider timed out") from None
        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            AttributeError,
        ):
            raise ApiError(502, "WEATHER_UNAVAILABLE", "Weather provider unavailable") from None

    def _get(self, url, params):
        response = self.session.get(url, params=params, timeout=(2, 3))
        response.raise_for_status()
        return response.json()
