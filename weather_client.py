"""Async HTTP client for WeatherAPI.com, built on httpx.

Compared to the original `requests`-based version this:
  * uses a single shared httpx.AsyncClient so all cities can be fetched
    concurrently with asyncio.gather instead of sequentially;
  * validates every response against pydantic models instead of indexing
    into raw dicts;
  * explicitly handles the three distinct failure modes the API can produce:
      1. network/transport errors (timeouts, DNS, connection refused);
      2. a 200 OK response that still contains an `"error": {...}` payload
         (WeatherAPI does this for some error kinds, e.g. invalid API key);
      3. a non-2xx HTTP status;
      4. a 200 OK "success" response whose JSON doesn't match the shape we
         expect (would previously surface as an unhandled KeyError/IndexError).
"""

from __future__ import annotations

import logging

import httpx
from pydantic import ValidationError

from config import Settings
from models import ApiErrorResponse, CityForecast, ForecastResponse

logger = logging.getLogger(__name__)


class WeatherApiError(Exception):
    """Raised for any failure retrieving or parsing a city's forecast.

    Callers can catch this single exception type instead of having to know
    about httpx, pydantic, or JSON decoding errors individually.
    """


async def fetch_forecast(client: httpx.AsyncClient, settings: Settings, city: str) -> ForecastResponse:
    """Fetch and validate the raw forecast payload for one city."""

    params = {
        "key": settings.weather_api_key,
        "q": city,
        "days": settings.forecast_days,
        "aqi": "no",
        "alerts": "no",
    }

    try:
        response = await client.get(
            settings.weather_api_base_url,
            params=params,
            timeout=settings.request_timeout,
        )
    except httpx.RequestError as exc:
        logger.error("Network error while requesting forecast for %s: %s", city, exc)
        raise WeatherApiError(f"Network error for {city}: {exc}") from exc

    try:
        payload = response.json()
    except ValueError:
        payload = None

    # WeatherAPI can return HTTP 200 with an "error" body for some failure
    # kinds (bad key, disabled endpoint, etc.), and non-2xx for others
    # (unknown location, rate limit). Check the error payload first since
    # it's more informative than a bare status code when both are present.
    if isinstance(payload, dict) and "error" in payload:
        try:
            err = ApiErrorResponse.model_validate(payload)
            message = f"[{err.error.code}] {err.error.message}"
        except ValidationError:
            message = str(payload.get("error"))
        logger.error("WeatherAPI returned an error for %s: %s", city, message)
        raise WeatherApiError(f"API error for {city}: {message}")

    if response.status_code != httpx.codes.OK:
        logger.error("Unexpected HTTP status %s for %s: %s", response.status_code, city, response.text[:200])
        raise WeatherApiError(f"HTTP {response.status_code} for {city}")

    if payload is None:
        logger.error("Response for %s was not valid JSON (status %s)", city, response.status_code)
        raise WeatherApiError(f"Invalid JSON response for {city}")

    try:
        return ForecastResponse.model_validate(payload)
    except ValidationError as exc:
        logger.error("Unexpected response structure for %s: %s", city, exc)
        raise WeatherApiError(f"Unexpected response structure for {city}") from exc


def extract_next_day(forecast: ForecastResponse, city: str, wind_dir_hour: int = 12) -> CityForecast:
    """Pull the next day's forecastday entry (index 1) out of a validated response."""

    try:
        next_day = forecast.forecast.forecastday[1]
    except IndexError as exc:
        logger.error("No next-day forecast entry returned for %s", city)
        raise WeatherApiError(f"No next-day forecast data returned for {city}") from exc

    if next_day.hour:
        try:
            wind_dir = next_day.hour[wind_dir_hour].wind_dir
        except IndexError:
            logger.warning(
                "Hour %s not available for %s, falling back to first available hour",
                wind_dir_hour,
                city,
            )
            wind_dir = next_day.hour[0].wind_dir
    else:
        logger.warning("No hourly data available for %s, wind direction unknown", city)
        wind_dir = "N/A"

    return CityForecast(
        city=city,
        date=next_day.date,
        min_temp_c=next_day.day.mintemp_c,
        max_temp_c=next_day.day.maxtemp_c,
        humidity_pct=next_day.day.avghumidity,
        wind_kph=next_day.day.maxwind_kph,
        wind_dir=wind_dir,
    )
