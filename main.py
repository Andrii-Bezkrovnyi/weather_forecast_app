#!/usr/bin/env python3
"""Entry point for the WeatherAPI.com code challenge.

Usage:
    python main.py

Kept at the repository root so the challenge has one obvious command to
run. The actual implementation lives in the weather_forecast/ package.
"""

import sys

from weather_forecast.cli import main

if __name__ == "__main__":
    sys.exit(main())
