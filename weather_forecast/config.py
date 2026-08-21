"""Typed, validated configuration via pydantic-settings.

Replaces the manual `os.getenv(..., "YOUR_API_KEY")` + "did you forget to set
it" check from the original script: if WEATHER_API_KEY is missing or of the
wrong type, instantiating Settings() raises a pydantic ValidationError with a
clear message, instead of silently defaulting to a placeholder string.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    weather_api_key: str = Field(..., min_length=1, description="WeatherAPI.com API key")
    weather_api_base_url: str = "https://api.weatherapi.com/v1/forecast.json"
    request_timeout: float = 10.0
    forecast_days: int = 2
    """days=2 -> API returns today (index 0) + tomorrow (index 1)."""
    wind_dir_hour: int = 12
    """Hour (0-23) used as the representative wind direction for the day,
    since WeatherAPI does not provide a single day-level wind direction."""
