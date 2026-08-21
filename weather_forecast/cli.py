"""Composition root: wires config + service + display together.

This is the only module that knows about all the others; config.py,
models.py, client.py, service.py, and display.py each stay independently
testable and don't know this module exists.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import List

from pydantic import ValidationError

from .config import Settings
from .display import make_console, render_table
from .service import collect_forecasts

CITIES: List[str] = ["Chisinau", "Madrid", "Kyiv", "Amsterdam"]

# Configure logging to output both to console (stderr) and to a file.
# Only configure once (when no handlers are present) to avoid duplicate logs
# if this module is imported multiple times during tests or interactive use.
root_logger = logging.getLogger()
if not root_logger.handlers:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("weather_forecast.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

logger = logging.getLogger("weather_forecast")


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

    console = make_console()
    console.print(render_table(forecasts))

    missing = [city for city in CITIES if city not in {f.city for f in forecasts}]
    if missing:
        logger.warning("Forecast unavailable for: %s", ", ".join(missing))

    return 0
