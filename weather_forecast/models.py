"""Pydantic models describing the parts of the WeatherAPI.com response we use.

Using typed models instead of raw dicts gives us the same kind of safety
Retrofit + Gson/Moshi would give on the JVM side: if WeatherAPI changes a
field name or type, we get a clear ValidationError instead of a silent
KeyError/TypeError somewhere deep in the code.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class ApiErrorDetail(BaseModel):
    """The `error` object WeatherAPI.com returns on failed requests."""

    model_config = ConfigDict(extra="ignore")

    code: int
    message: str


class ApiErrorResponse(BaseModel):
    """Shape of an error response, e.g. an unknown city or bad API key."""

    model_config = ConfigDict(extra="ignore")

    error: ApiErrorDetail


class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    country: str
    tz_id: str


class Hour(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: str
    wind_dir: str


class Day(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mintemp_c: float
    maxtemp_c: float
    avghumidity: float
    maxwind_kph: float


class ForecastDay(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: str
    day: Day
    hour: List[Hour]


class Forecast(BaseModel):
    model_config = ConfigDict(extra="ignore")

    forecastday: List[ForecastDay]


class ForecastResponse(BaseModel):
    """Top-level shape of a successful forecast.json response (fields we need)."""

    model_config = ConfigDict(extra="ignore")

    location: Location
    forecast: Forecast


class CityForecast(BaseModel):
    """Our own domain model: one row of the output table."""

    city: str
    date: str
    min_temp_c: float
    max_temp_c: float
    humidity_pct: float
    wind_kph: float
    wind_dir: str
