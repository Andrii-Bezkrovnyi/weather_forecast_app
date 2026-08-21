"""Unit tests for weather_forecast.client using httpx.MockTransport (no real API calls).

Run with:  python -m pytest -v      (from the project root)
"""

from __future__ import annotations

import httpx
import pytest

from weather_forecast.client import WeatherApiError, extract_next_day, fetch_forecast
from weather_forecast.config import Settings
from weather_forecast.models import ForecastResponse

from datetime import date, timedelta


def make_settings() -> Settings:
    return Settings(weather_api_key="dummy-key")


def success_payload(city: str = "Kyiv") -> dict:
    today = date.today()
    tomorrow = today + timedelta(days=1)

    today_str = today.isoformat()
    tomorrow_str = tomorrow.isoformat()

    return {
        "location": {"name": city, "country": "Ukraine", "tz_id": "Europe/Kyiv"},
        "forecast": {
            "forecastday": [
                {  # today - index 0, should be ignored
                    "date": today_str,
                    "day": {
                        "mintemp_c": 10.0,
                        "maxtemp_c": 20.0,
                        "avghumidity": 50.0,
                        "maxwind_kph": 15.0,
                    },
                    "hour": [{"time": f"{today_str} {hour:02d}:00", "wind_dir": "N"} for hour in range(24)],
                },
                {  # tomorrow - index 1, this is what we want
                    "date": tomorrow_str,
                    "day": {
                        "mintemp_c": 22.5,
                        "maxtemp_c": 36.2,
                        "avghumidity": 31.0,
                        "maxwind_kph": 22.0,
                    },
                    "hour": [
                        {"time": f"{tomorrow_str} {h:02d}:00", "wind_dir": "S" if h == 12 else "SW"}
                        for h in range(24)
                    ],
                },
            ]
        },
    }


@pytest.mark.asyncio
async def test_fetch_and_extract_success():
    tomorrow_expected = (date.today() + timedelta(days=1)).isoformat()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=success_payload("Kyiv"))

    transport = httpx.MockTransport(handler)
    settings = make_settings()

    async with httpx.AsyncClient(transport=transport) as client:
        raw = await fetch_forecast(client, settings, "Kyiv")

    result = extract_next_day(raw, "Kyiv", wind_dir_hour=12)

    assert result.city == "Kyiv"
    assert result.date == tomorrow_expected
    assert result.min_temp_c == 22.5
    assert result.max_temp_c == 36.2
    assert result.humidity_pct == 31.0
    assert result.wind_kph == 22.0
    assert result.wind_dir == "S"  # taken from hour[12], not the "SW" default


@pytest.mark.asyncio
async def test_api_error_field_raises_weather_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": {"code": 1006, "message": "No matching location found."}})

    transport = httpx.MockTransport(handler)
    settings = make_settings()

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(WeatherApiError, match="No matching location found"):
            await fetch_forecast(client, settings, "Atlantis")


@pytest.mark.asyncio
async def test_non_200_status_raises_weather_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    transport = httpx.MockTransport(handler)
    settings = make_settings()

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(WeatherApiError, match="HTTP 401"):
            await fetch_forecast(client, settings, "Kyiv")


@pytest.mark.asyncio
async def test_malformed_json_raises_weather_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json at all")

    transport = httpx.MockTransport(handler)
    settings = make_settings()

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(WeatherApiError, match="Invalid JSON"):
            await fetch_forecast(client, settings, "Kyiv")


@pytest.mark.asyncio
async def test_unexpected_shape_raises_weather_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"location": {"name": "Kyiv"}})

    transport = httpx.MockTransport(handler)
    settings = make_settings()

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(WeatherApiError, match="Unexpected response structure"):
            await fetch_forecast(client, settings, "Kyiv")


def test_extract_next_day_missing_index_raises():
    payload = success_payload("Kyiv")
    payload["forecast"]["forecastday"] = payload["forecast"]["forecastday"][:1]  # only "today"
    forecast = ForecastResponse.model_validate(payload)

    with pytest.raises(WeatherApiError, match="No next-day forecast"):
        extract_next_day(forecast, "Kyiv")
