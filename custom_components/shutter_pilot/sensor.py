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
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_SHUTTERS,
    CONF_WEATHER_ENTITY,
    DOMAIN,
    ROLE_CLOSED,
    ROLE_OPEN,
)
from .helpers import (
    is_window,
    POSITION_TOLERANCE_PCT,
    get_position_for_role,
    get_tracked_position,
    is_awning,
    is_cover_sun_protected,
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

    entities.append(ShutterPilotStatusSensor(entry))

    # Only when a weather entity is configured – otherwise these would sit
    # around as permanently unknown entities.
    if str(entry.options.get(CONF_WEATHER_ENTITY) or "").strip():
        entities.append(ShutterPilotForecastTempSensor(entry))
        entities.append(ShutterPilotForecastTempPeakSensor(entry))
        entities.append(ShutterPilotForecastTempMinSensor(entry))
        entities.append(ShutterPilotForecastConditionSensor(entry))

    if entities:
        async_add_entities(entities)


class _ForecastSensorBase(SensorEntity):
    """Shared plumbing for the forecast sensors.

    The names come from the translation files. Home Assistant only looks them
    up when has_entity_name is set *and* no _attr_name is present – setting a
    name short-circuits the lookup, which is why these sensors used to be
    German for everyone.
    """

    _attr_has_entity_name = True
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
        self._attr_translation_key = "forecast_temp_max"

    @property
    def native_value(self) -> float | None:
        return self._weather().get("temp_max")


class ShutterPilotForecastTempPeakSensor(_ForecastSensorBase):
    """The day's highest forecast high, for decisions taken in the evening.

    The plain forecast sensor follows the source and drops again once the peak
    has passed. Anything that asks "was it hot today?" at closing time needs
    this one instead.
    """

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-chevron-up"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_forecast_temp_max_peak"
        self._attr_translation_key = "forecast_temp_max_peak"

    @property
    def native_value(self) -> float | None:
        return self._weather().get("temp_max_peak")


class ShutterPilotForecastTempMinSensor(_ForecastSensorBase):
    """Today's forecast low – the natural input for frost protection."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-low"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_forecast_temp_min"
        self._attr_translation_key = "forecast_temp_min"

    @property
    def native_value(self) -> float | None:
        return self._weather().get("temp_min")


class ShutterPilotForecastConditionSensor(_ForecastSensorBase):
    """Today's forecast weather condition, e.g. sunny or rainy."""

    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_forecast_condition"
        self._attr_translation_key = "forecast_condition"

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


class ShutterPilotStatusSensor(SensorEntity):
    """One entity that answers "how does the house stand right now?".

    Asked for as a card on a plain Home Assistant dashboard: a primary status
    (open / closed) and a secondary line naming what is being shaded. The
    primary one is the state, everything else is an attribute – a state is a
    single word by contract, and a sentence in it cannot be filtered on.

    Awnings are counted apart rather than folded in. A retracted awning is at
    rest, and calling that "closed" alongside a closed shutter would make the
    tally read as if the house were shut when the terrace is simply tidy.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:window-shutter"
    _attr_translation_key = "status"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._unsub = None

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

    def _shutters(self) -> list[dict]:
        shutters = self._entry.options.get(CONF_SHUTTERS, [])
        return [s for s in shutters if isinstance(s, dict)] if isinstance(
            shutters, list
        ) else []

    def _area_names(self) -> dict[str, str]:
        areas = self._entry.options.get(CONF_AREAS, [])
        if not isinstance(areas, list):
            return {}
        out: dict[str, str] = {}
        for a in areas:
            if isinstance(a, dict):
                area_id = str(a.get(CONF_AREA_ID) or "").strip()
                if area_id:
                    out[area_id] = str(a.get(CONF_AREA_NAME) or area_id)
        return out

    def _collect(self) -> dict[str, Any]:
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        if not isinstance(data, dict):
            data = {}
        names = self._area_names()
        counts = {"open": 0, "closed": 0, "partial": 0, "unknown": 0}
        awn_out = awn_in = awn_unknown = 0
        win_open = win_closed = win_unknown = 0
        shaded_covers: list[str] = []
        shaded_areas: list[str] = []

        for shutter in self._shutters():
            cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
            if not cover:
                continue
            if is_cover_sun_protected(data, cover):
                shaded_covers.append(cover)
                area_name = names.get(
                    str(shutter.get(CONF_AREA_DOWN_ID) or "").strip()
                )
                if area_name and area_name not in shaded_areas:
                    shaded_areas.append(area_name)
            pos = get_tracked_position(self.hass, shutter, cover)
            awning = is_awning(shutter)
            window = is_window(shutter)
            if pos is None:
                if awning:
                    awn_unknown += 1
                elif window:
                    win_unknown += 1
                else:
                    counts["unknown"] += 1
                continue
            # ROLE_OPEN is the rest position for both kinds – on an awning
            # that is "retracted". Which number it holds is configuration, and
            # that is exactly why the roles are asked instead of 0 and 100.
            rest = get_position_for_role(shutter, ROLE_OPEN)
            if awning:
                if abs(pos - rest) <= POSITION_TOLERANCE_PCT:
                    awn_in += 1
                else:
                    awn_out += 1
                continue
            closed = get_position_for_role(shutter, ROLE_CLOSED)
            if window:
                # Counted apart from the shutters for the same reason awnings
                # are: a tilted roof window does not make the house "open".
                if abs(pos - closed) <= POSITION_TOLERANCE_PCT:
                    win_closed += 1
                else:
                    win_open += 1
                continue
            if abs(pos - rest) <= POSITION_TOLERANCE_PCT:
                counts["open"] += 1
            elif abs(pos - closed) <= POSITION_TOLERANCE_PCT:
                counts["closed"] += 1
            else:
                counts["partial"] += 1

        return {
            "counts": counts,
            "awnings_extended": awn_out,
            "awnings_retracted": awn_in,
            "awnings_unknown": awn_unknown,
            "windows_open": win_open,
            "windows_closed": win_closed,
            "windows_unknown": win_unknown,
            "shaded_covers": shaded_covers,
            "shaded_areas": shaded_areas,
        }

    @property
    def native_value(self) -> str | None:
        info = self._collect()
        c = info["counts"]
        total = c["open"] + c["closed"] + c["partial"]
        if not total:
            return None
        if c["open"] == total:
            return "open"
        if c["closed"] == total:
            return "closed"
        return "partial"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = self._collect()
        c = info["counts"]
        return {
            "open": c["open"],
            "closed": c["closed"],
            "partial": c["partial"],
            "unknown": c["unknown"],
            "awnings_extended": info["awnings_extended"],
            "awnings_retracted": info["awnings_retracted"],
            "shading_active": bool(info["shaded_covers"]),
            "shading_areas": info["shaded_areas"],
            "shading_covers": info["shaded_covers"],
        }
