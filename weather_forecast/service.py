"""Orchestration: fetch all cities concurrently and collect the results.

Kept separate from client.py (single-city HTTP + parsing) and from cli.py
(argument/logging/console wiring) so each module has one job and can be
tested or reused independently.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

import httpx

from .client import WeatherApiError, extract_next_day, fetch_forecast
from .config import Settings
from .models import CityForecast

logger = logging.getLogger(__name__)


async def _fetch_one(client: httpx.AsyncClient, settings: Settings, city: str) -> Optional[CityForecast]:
    try:
        raw = await fetch_forecast(client, settings, city)
        return extract_next_day(raw, city, wind_dir_hour=settings.wind_dir_hour)
    except WeatherApiError as exc:
        # Already logged with context inside client.py; catching here keeps
        # asyncio.gather resilient so one bad city doesn't take down the rest.
        logger.error("Skipping %s: %s", city, exc)
        return None


async def collect_forecasts(settings: Settings, cities: List[str]) -> List[CityForecast]:
    """Fetch the next-day forecast for every city concurrently.

    Cities that fail (network error, unknown location, malformed response)
    are logged and simply omitted from the result rather than aborting the
    whole run.
    """

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(_fetch_one(client, settings, city) for city in cities))
    return [forecast for forecast in results if forecast is not None]
