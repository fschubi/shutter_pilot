"""Tests for the forecast fetch.

Forum feedback: users want to shade only when the day actually gets warm.
Since HA 2024.4 the forecast is only available through a service response,
never as an attribute.
"""

from __future__ import annotations

import pytest
from homeassistant.core import SupportsResponse
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import CONF_WEATHER_ENTITY, DOMAIN
from custom_components.shutter_pilot.weather_data import (
    async_fetch_forecast,
    get_weather_data,
)

FORECAST = {
    "weather.home": {
        "forecast": [
            {
                "datetime": "2026-08-02T00:00:00+00:00",
                "condition": "sunny",
                "temperature": 28.5,
                "templow": 16.0,
                "precipitation_probability": 5,
            },
            {"datetime": "2026-08-03T00:00:00+00:00", "condition": "rainy"},
        ]
    }
}


@pytest.fixture
async def weather_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, options={CONF_WEATHER_ENTITY: "weather.home"}
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    hass.states.async_set("weather.home", "sunny")
    return entry


async def _fetch(hass, entry, response, *, raises=False):
    """Register a stand-in weather.get_forecasts and run one fetch.

    A real service is registered rather than patching hass.services, so the
    response plumbing (supports_response / return_response) is exercised.
    Returns the list of received service calls.
    """
    received: list = []

    async def _handler(call):
        received.append(call)
        if raises:
            raise RuntimeError("boom")
        return response

    hass.services.async_register(
        "weather",
        "get_forecasts",
        _handler,
        supports_response=SupportsResponse.ONLY,
    )
    try:
        await async_fetch_forecast(hass, entry)
    finally:
        hass.services.async_remove("weather", "get_forecasts")
    return received


class TestSuccessfulFetch:
    async def test_values_are_cached(self, hass, weather_entry):
        await _fetch(hass, weather_entry, FORECAST)
        data = get_weather_data(hass, weather_entry.entry_id)
        assert data["temp_max"] == 28.5
        assert data["temp_min"] == 16.0
        assert data["condition"] == "sunny"
        assert data["precipitation_probability"] == 5.0
        assert data["source"] == "weather.home"
        assert data["updated"]

    async def test_asks_for_the_daily_forecast(self, hass, weather_entry):
        received = await _fetch(hass, weather_entry, FORECAST)
        assert len(received) == 1
        assert received[0].data["type"] == "daily"
        assert received[0].data["entity_id"] == "weather.home"

    async def test_only_first_day_is_used(self, hass, weather_entry):
        await _fetch(hass, weather_entry, FORECAST)
        assert get_weather_data(hass, weather_entry.entry_id)["condition"] == "sunny"


class TestFailuresKeepLastValue:
    """A broken weather integration must never disturb shading."""

    async def test_empty_response(self, hass, weather_entry):
        await _fetch(hass, weather_entry, FORECAST)
        await _fetch(hass, weather_entry, {})
        assert get_weather_data(hass, weather_entry.entry_id)["temp_max"] == 28.5

    async def test_forecast_list_empty(self, hass, weather_entry):
        await _fetch(hass, weather_entry, FORECAST)
        await _fetch(hass, weather_entry, {"weather.home": {"forecast": []}})
        assert get_weather_data(hass, weather_entry.entry_id)["temp_max"] == 28.5

    async def test_service_raises(self, hass, weather_entry):
        await _fetch(hass, weather_entry, FORECAST)
        await _fetch(hass, weather_entry, FORECAST, raises=True)
        assert get_weather_data(hass, weather_entry.entry_id)["temp_max"] == 28.5

    async def test_missing_service_is_survived(self, hass, weather_entry):
        """Weather integration not loaded at all."""
        await async_fetch_forecast(hass, weather_entry)
        assert get_weather_data(hass, weather_entry.entry_id) == {}

    async def test_missing_entity_is_not_called(self, hass, weather_entry):
        hass.states.async_remove("weather.home")
        received = await _fetch(hass, weather_entry, FORECAST)
        assert received == []
        assert get_weather_data(hass, weather_entry.entry_id) == {}

    async def test_missing_values_become_none(self, hass, weather_entry):
        await _fetch(
            hass, weather_entry, {"weather.home": {"forecast": [{"condition": "fog"}]}}
        )
        data = get_weather_data(hass, weather_entry.entry_id)
        assert data["condition"] == "fog"
        assert data["temp_max"] is None

    async def test_warning_only_once(self, hass, weather_entry, caplog):
        for _ in range(3):
            await _fetch(hass, weather_entry, {})
        assert caplog.text.count("returned no daily forecast") == 1


class TestNotConfigured:
    async def test_without_entity_nothing_happens(self, hass):
        entry = MockConfigEntry(domain=DOMAIN, options={})
        entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
        received = await _fetch(hass, entry, FORECAST)
        assert received == []
        assert get_weather_data(hass, entry.entry_id) == {}
