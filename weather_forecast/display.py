"""Presentation layer: render CityForecast rows as a rich table."""

from __future__ import annotations

import sys
from typing import List

from rich.console import Console
from rich.table import Table

from .models import CityForecast


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


def make_console() -> Console:
    """A Console that stays wide even when stdout isn't a real terminal.

    Rich falls back to an 80-column width when it can't detect a terminal
    (piped output, redirected to a file, CI) which truncates this table.
    """

    return Console() if sys.stdout.isatty() else Console(width=120)
