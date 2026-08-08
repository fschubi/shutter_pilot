"""Fetch today's weather forecast for use as a shading condition.

Since Home Assistant 2024.4 forecasts are no longer exposed as attributes of
the weather entity. They have to be requested through the `weather.get_forecasts`
service, which returns its data as a service response.

The values land in `hass.data[DOMAIN][entry_id]["weather"]` and are published
through two sensors, so users can pick them in the ordinary condition slots
instead of building a template sensor by hand.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import CONF_WEATHER_ENTITY, DOMAIN
from .helpers import register_minute_callback

_LOGGER = logging.getLogger(__name__)

# The forecast changes slowly; every 30 minutes is plenty and keeps the load
# on the weather integration low.
REFRESH_EVERY_MINUTES = 30


def get_weather_data(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Return the cached forecast for a config entry."""
    data = hass.data.get(DOMAIN, {}).get(entry_id)
    if not isinstance(data, dict):
        return {}
    cached = data.get("weather")
    return cached if isinstance(cached, dict) else {}


def _configured_entity(entry: ConfigEntry) -> str:
    return str(entry.options.get(CONF_WEATHER_ENTITY) or "").strip()


def _peak_today(data: dict[str, Any], temp_max: float | None) -> float | None:
    """Highest forecast high seen since midnight.

    A daily forecast is revised while the day runs, and most sources lower it
    once the peak has passed: at 21:00 the "high for today" can read 25 °C on a
    day that reached 28 °C at three in the afternoon. A condition like "close
    only halfway when it was above 26 °C" is evaluated exactly then – against a
    number that has quietly walked away from what happened. So the day's
    highest reading is kept alongside the live one, and it only ever rises
    until midnight.
    """
    today = dt_util.now().date().isoformat()
    if data.get("_weather_peak_day") != today:
        data["_weather_peak_day"] = today
        data["_weather_peak"] = None
    if temp_max is None:
        return data.get("_weather_peak")
    previous = data.get("_weather_peak")
    peak = temp_max if previous is None else max(float(previous), temp_max)
    data["_weather_peak"] = peak
    return peak


async def async_fetch_forecast(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Fetch today's forecast and cache it.

    Any failure keeps the previous values. A broken or slow weather integration
    must never block shading, so nothing here raises.
    """
    entity_id = _configured_entity(entry)
    if not entity_id:
        return

    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        return

    def _warn_once(key: str, msg: str, *args) -> None:
        warned = data.setdefault("_weather_warned", set())
        if key not in warned:
            warned.add(key)
            _LOGGER.warning(msg, *args)

    if hass.states.get(entity_id) is None:
        _warn_once("missing", "Weather entity %s not found", entity_id)
        return

    try:
        response = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"entity_id": entity_id, "type": "daily"},
            blocking=True,
            return_response=True,
        )
    except Exception as err:  # noqa: BLE001 - never let weather break shading
        _warn_once("call", "Could not fetch forecast from %s: %s", entity_id, err)
        return

    forecast = None
    if isinstance(response, dict):
        entry_data = response.get(entity_id)
        if isinstance(entry_data, dict):
            items = entry_data.get("forecast")
            if isinstance(items, list) and items:
                forecast = items[0]

    if not isinstance(forecast, dict):
        _warn_once("empty", "Weather entity %s returned no daily forecast", entity_id)
        return

    def _num(key: str) -> float | None:
        try:
            value = forecast.get(key)
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    temp_max = _num("temperature")
    data["weather"] = {
        "source": entity_id,
        "temp_max": temp_max,
        "temp_min": _num("templow"),
        "temp_max_peak": _peak_today(data, temp_max),
        "condition": str(forecast.get("condition") or "") or None,
        "precipitation_probability": _num("precipitation_probability"),
        "updated": dt_util.now().isoformat(),
    }
    # A successful fetch clears the warnings so a later outage is reported again.
    data["_weather_warned"] = set()
    _LOGGER.debug("Forecast for %s: %s", entity_id, data["weather"])


async def setup_weather(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register the periodic forecast fetch on the shared minute ticker."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    if not _configured_entity(entry):
        register_minute_callback(data, "weather", None)
        data.pop("weather", None)
        return

    counter = {"n": 0}

    def _tick(_now) -> None:
        # Own counter instead of a second timer – Shutter Pilot deliberately
        # runs everything periodic off one shared minute ticker.
        if counter["n"] % REFRESH_EVERY_MINUTES == 0:
            hass.async_create_task(async_fetch_forecast(hass, entry))
        counter["n"] += 1

    register_minute_callback(data, "weather", _tick)
    hass.async_create_task(async_fetch_forecast(hass, entry))
    _LOGGER.info("Weather forecast enabled for %s", _configured_entity(entry))
