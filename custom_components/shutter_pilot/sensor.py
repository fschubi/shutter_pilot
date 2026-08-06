"""Sensor entities exposing the next scheduled movement per area."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from datetime import timedelta

from homeassistant.const import UnitOfTemperature

from .const import (
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_WEATHER_ENTITY,
)
from .schedule_times import get_next_action
from .weather_data import get_weather_data

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one "next action" sensor per area."""
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        return

    entities: list[SensorEntity] = []
    for area in areas:
        if not isinstance(area, dict):
            continue
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            continue
        entities.append(ShutterPilotNextActionSensor(entry, area_id))

    # Only when a weather entity is configured – otherwise these would sit
    # around as permanently unknown entities.
    if str(entry.options.get(CONF_WEATHER_ENTITY) or "").strip():
        entities.append(ShutterPilotForecastTempSensor(entry))
        entities.append(ShutterPilotForecastTempMinSensor(entry))
        entities.append(ShutterPilotForecastConditionSensor(entry))

    if entities:
        async_add_entities(entities)


class _ForecastSensorBase(SensorEntity):
    """Shared plumbing for the forecast sensors."""

    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._unsub = None

    def _weather(self) -> dict[str, Any]:
        return get_weather_data(self.hass, self._entry.entry_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_track_time_interval(self.hass, self._on_tick, SCAN_INTERVAL)
        self.async_on_remove(self._cancel)

    @callback
    def _cancel(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _on_tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        w = self._weather()
        return {
            "source": w.get("source"),
            "updated": w.get("updated"),
            "temp_min": w.get("temp_min"),
            "precipitation_probability": w.get("precipitation_probability"),
        }


class ShutterPilotForecastTempSensor(_ForecastSensorBase):
    """Today's forecast high, ready to use as a shading condition."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-high"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_forecast_temp_max"
        self._attr_name = "Shutter Pilot Vorhersage Höchsttemperatur"

    @property
    def native_value(self) -> float | None:
        return self._weather().get("temp_max")


class ShutterPilotForecastTempMinSensor(_ForecastSensorBase):
    """Today's forecast low – the natural input for frost protection."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-low"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_forecast_temp_min"
        self._attr_name = "Shutter Pilot Vorhersage Tiefsttemperatur"

    @property
    def native_value(self) -> float | None:
        return self._weather().get("temp_min")


class ShutterPilotForecastConditionSensor(_ForecastSensorBase):
    """Today's forecast weather condition, e.g. sunny or rainy."""

    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_forecast_condition"
        self._attr_name = "Shutter Pilot Vorhersage Wetterlage"

    @property
    def native_value(self) -> str | None:
        return self._weather().get("condition")


class ShutterPilotNextActionSensor(SensorEntity):
    """Timestamp of the next scheduled up/down movement for one area."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, area_id: str) -> None:
        self._entry = entry
        self._area_id = area_id
        self._attr_unique_id = f"{entry.entry_id}_next_action_{area_id}"
        self._attr_name = f"Shutter Pilot {self._area_name()} nächste Fahrt"
        self._value: datetime | None = None
        self._direction: str | None = None
        self._unsub = None

    def _area(self) -> dict[str, Any]:
        areas = self._entry.options.get(CONF_AREAS, [])
        if isinstance(areas, list):
            for a in areas:
                if isinstance(a, dict) and str(a.get(CONF_AREA_ID) or "") == self._area_id:
                    return a
        return {}

    def _area_name(self) -> str:
        return str(self._area().get(CONF_AREA_NAME) or self._area_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._refresh()
        self._unsub = async_track_time_interval(self.hass, self._on_tick, SCAN_INTERVAL)
        self.async_on_remove(self._cancel)

    @callback
    def _cancel(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _on_tick(self, _now: datetime) -> None:
        self._refresh()
        self.async_write_ha_state()

    @callback
    def _refresh(self) -> None:
        area = self._area()
        if not area:
            self._value, self._direction = None, None
            return
        self._value, self._direction = get_next_action(self.hass, area, dt_util.now())

    @property
    def native_value(self) -> datetime | None:
        return self._value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        area = self._area()
        return {
            "area_id": self._area_id,
            "area_name": self._area_name(),
            "mode": str(area.get(CONF_AREA_MODE) or ""),
            "direction": self._direction,
        }
