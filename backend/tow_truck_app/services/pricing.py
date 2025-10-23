"""
Utilities for calculating tow truck pricing with weather adjustments.
"""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Tuple

import requests
from django.conf import settings

from ..models import VehicleType

logger = logging.getLogger(__name__)


WEATHER_MULTIPLIERS: Dict[str, Decimal] = {
    "clear": Decimal("1.00"),
    "partly-cloudy": Decimal("1.00"),
    "cloudy": Decimal("1.05"),
    "overcast": Decimal("1.07"),
    "rain": Decimal("1.15"),
    "drizzle": Decimal("1.10"),
    "light-rain": Decimal("1.12"),
    "showers": Decimal("1.18"),
    "snow": Decimal("1.20"),
    "light-snow": Decimal("1.15"),
    "wet-snow": Decimal("1.25"),
    "storm": Decimal("1.30"),
    "thunderstorm": Decimal("1.35"),
}


def fetch_weather(lat: float, lon: float) -> dict[str, Any] | None:
    """
    Retrieve weather data for the provided coordinates.

    The function prefers Yandex Weather API when a key is provided, otherwise
    falls back to the free Open-Meteo API.
    """

    api_key = getattr(settings, "YANDEX_WEATHER_API_KEY", None)
    base_url = getattr(settings, "YANDEX_WEATHER_API_URL", "https://api.weather.yandex.ru/v2/informers")

    if api_key:
        headers = {"X-Yandex-API-Key": api_key}
        params = {"lat": lat, "lon": lon}

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=6)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:  # pragma: no cover - network failure
            logger.warning("Failed to fetch weather data from Yandex API: %s", exc)

    # Fallback to Open-Meteo (no API key required)
    try:
        open_meteo_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,pressure_msl",
            "timezone": "auto",
        }
        response = requests.get(open_meteo_url, params=params, timeout=6)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:  # pragma: no cover - network failure
        logger.warning("Failed to fetch weather data from Open-Meteo: %s", exc)
        return None


def get_weather_multiplier(weather: dict[str, Any] | None) -> Decimal:
    """Derive a multiplier based on the Yandex weather payload."""

    if not weather:
        return Decimal("1.00")

    condition = weather.get("fact", {}).get("condition")
    if condition in WEATHER_MULTIPLIERS:
        return WEATHER_MULTIPLIERS[condition]

    # Handle precipitation type when condition is not enough.
    prec_type = weather.get("fact", {}).get("prec_type")
    if prec_type == 1:  # rain
        return Decimal("1.12")
    if prec_type == 2:  # snow
        return Decimal("1.20")
    if prec_type == 3:  # mixed
        return Decimal("1.18")

    return Decimal("1.00")


def calculate_price(
    vehicle_type: VehicleType,
    distance_km: Decimal,
    lat: float,
    lon: float,
) -> Tuple[Decimal, dict[str, Any]]:
    """
    Calculate the final price and return a tuple with the price and metadata.

    Metadata includes the weather multiplier that was applied and raw weather data (if any).
    """

    base_price = vehicle_type.base_price or Decimal("0")
    distance_component = (vehicle_type.per_km_rate or Decimal("0")) * distance_km

    weather_payload = fetch_weather(lat, lon)
    multiplier = get_weather_multiplier(weather_payload)

    subtotal = base_price + distance_component
    total = (subtotal * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return total, {
        "base_price": str(base_price),
        "distance_component": str(distance_component.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "multiplier": str(multiplier),
        "distance_km": str(distance_km),
        "weather": weather_payload or {},
    }


OPEN_METEO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle (light)",
    57: "Freezing drizzle (dense)",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Rain showers (slight)",
    81: "Rain showers (moderate)",
    82: "Rain showers (violent)",
    85: "Snow showers (slight)",
    86: "Snow showers (heavy)",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def simplify_weather(weather_payload: dict[str, Any] | None) -> dict[str, Any]:
    """
    Extract a compact weather description from the raw payload.
    """
    if not weather_payload:
        return {}

    if "fact" in weather_payload:
        fact = weather_payload.get("fact") or {}
        return {
            "provider": "yandex",
            "condition": fact.get("condition"),
            "temperature": fact.get("temp"),
            "feels_like": fact.get("feels_like"),
            "wind_speed": fact.get("wind_speed"),
            "pressure_mm": fact.get("pressure_mm"),
            "raw": weather_payload,
        }

    current = weather_payload.get("current")
    if current:
        code = current.get("weather_code")
        return {
            "provider": "open-meteo",
            "condition": OPEN_METEO_CODES.get(code, str(code) if code is not None else None),
            "temperature": current.get("temperature"),
            "feels_like": current.get("apparent_temperature"),
            "wind_speed": current.get("wind_speed_10m"),
            "pressure_mm": current.get("pressure_msl"),
            "raw": weather_payload,
        }

    return {"raw": weather_payload}
