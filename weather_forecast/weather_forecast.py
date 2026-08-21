"""WeatherAPI.com code challenge: next-day forecast for several cities.

Fetches the next day's forecast for a fixed list of cities concurrently
(httpx + asyncio), validates every response with pydantic models, logs
errors via the `logging` module instead of `print`, and renders the result
as a Rich table with cities as rows and (for this single day) an explicit
Date column.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import List, Optional

import httpx
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from config import Settings
from models import CityForecast
from weather_client import WeatherApiError, extract_next_day, fetch_forecast

CITIES: List[str] = ["Chisinau", "Madrid", "Kyiv", "Amsterdam"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("weather_forecast")


async def _fetch_one(client: httpx.AsyncClient, settings: Settings, city: str) -> Optional[CityForecast]:
    try:
        raw = await fetch_forecast(client, settings, city)
        return extract_next_day(raw, city, wind_dir_hour=settings.wind_dir_hour)
    except WeatherApiError as exc:
        # Already logged with context inside weather_client; this keeps the
        # gather() call resilient so one bad city doesn't take down the rest.
        logger.error("Skipping %s: %s", city, exc)
        return None


async def collect_forecasts(settings: Settings, cities: List[str]) -> List[CityForecast]:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(_fetch_one(client, settings, city) for city in cities))
    return [forecast for forecast in results if forecast is not None]


def render_table(forecasts: List[CityForecast]) -> Table:
    table = Table(title="Next-day weather forecast", show_lines=True, header_style="bold")
    table.add_column("City", style="bold cyan")
    table.add_column("Date", justify="center")
    table.add_column("Min Temp (°C)", justify="right")
    table.add_column("Max Temp (°C)", justify="right")
    table.add_column("Humidity (%)", justify="right")
    table.add_column("Wind Speed (kph)", justify="right")
    table.add_column("Wind Direction", justify="center")

    for f in forecasts:
        table.add_row(
            f.city,
            f.date,
            f"{f.min_temp_c:.1f}",
            f"{f.max_temp_c:.1f}",
            f"{f.humidity_pct:.0f}",
            f"{f.wind_kph:.1f}",
            f.wind_dir,
        )
    return table


def main() -> int:
    try:
        settings = Settings()
    except ValidationError as exc:
        logger.error("Invalid configuration: %s", exc)
        print(
            "Error: WEATHER_API_KEY is missing or invalid. "
            "Copy .env.example to .env and set your key.",
            file=sys.stderr,
        )
        return 1

    forecasts = asyncio.run(collect_forecasts(settings, CITIES))

    if not forecasts:
        logger.error("No forecast data could be retrieved for any city.")
        return 1

    # When stdout isn't a real terminal (piped, redirected to a file, run in
    # CI), Rich can't detect a terminal width and falls back to 80 columns,
    # which truncates this table. Force a wider fixed width in that case;
    # in an interactive terminal, Rich still uses the real detected size.
    console = Console() if sys.stdout.isatty() else Console(width=120)
    console.print(render_table(forecasts))

    missing = [city for city in CITIES if city not in {f.city for f in forecasts}]
    if missing:
        logger.warning("Forecast unavailable for: %s", ", ".join(missing))

    return 0


if __name__ == "__main__":
    sys.exit(main())
