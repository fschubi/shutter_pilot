"""Binary sensor entities exposing the sun protection state per area."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .awning_guard import guard_status
from .const import (
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
)
from .helpers import (
    get_azimuth_bounds,
    get_elevation_bounds,
    get_sun_angles,
    is_sun_protect_active,
    only_awnings,
    sun_protect_conditions_met,
)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one sun protection sensor per area that uses shading."""
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        return

    entities: list[BinarySensorEntity] = []
    for area in areas:
        if not isinstance(area, dict):
            continue
        if not bool(area.get(CONF_AREA_SUN_PROTECT_ENABLED, False)):
            continue
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            continue
        entities.append(ShutterPilotSunProtectionSensor(entry, area_id))

    # One per awning rather than one for the house: the lockout runs per awning,
    # and two awnings on different sides of the house are released at different
    # moments. Same shape as the per-area shading sensor above.
    shutters = entry.options.get(CONF_SHUTTERS, [])
    if isinstance(shutters, list):
        for shutter in only_awnings(shutters):
            cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
            if cover:
                entities.append(ShutterPilotAwningGuardSensor(entry, cover))

    if entities:
        async_add_entities(entities)


class ShutterPilotSunProtectionSensor(BinarySensorEntity):
    """On while shading is actively holding the shutters in position."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:sun-wireless-outline"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, area_id: str) -> None:
        self._entry = entry
        self._area_id = area_id
        self._attr_unique_id = f"{entry.entry_id}_sun_protection_{area_id}"
        self._attr_name = f"Shutter Pilot {self._area_name()} Sonnenschutz"
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

    def _runtime(self) -> dict[str, Any]:
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        return data if isinstance(data, dict) else {}

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
    def is_on(self) -> bool:
        return is_sun_protect_active(self._runtime(), self._area_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        area = self._area()
        elev, azim = get_sun_angles(self.hass)
        e_min, e_max = get_elevation_bounds(area)
        a_min, a_max = get_azimuth_bounds(area)
        return {
            "area_id": self._area_id,
            "area_name": self._area_name(),
            "conditions_met": sun_protect_conditions_met(elev, azim, area),
            "current_elevation": elev,
            "elevation_min": e_min,
            "elevation_max": e_max,
            "current_azimuth": azim,
            "azimuth_enabled": bool(area.get("azimuth_enabled", False)),
            "azimuth_min": a_min,
            "azimuth_max": a_max,
        }


class ShutterPilotAwningGuardSensor(BinarySensorEntity):
    """On while this awning must not extend.

    Reads the guard's last verdict rather than evaluating one: evaluating
    writes hysteresis and lockout timers, and an entity that is polled once a
    minute by the frontend would then be moving the state it reports.
    """

    _attr_has_entity_name = False
    _attr_icon = "mdi:weather-windy"
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry: ConfigEntry, cover_entity_id: str) -> None:
        self._entry = entry
        self._cover = cover_entity_id
        self._attr_unique_id = f"{entry.entry_id}_awning_guard_{cover_entity_id}"
        self._attr_name = f"Shutter Pilot {self._awning_name()} Sperre"
        self._unsub = None

    def _awning(self) -> dict[str, Any]:
        shutters = self._entry.options.get(CONF_SHUTTERS, [])
        if isinstance(shutters, list):
            for s in shutters:
                if (
                    isinstance(s, dict)
                    and str(s.get(CONF_COVER_ENTITY_ID) or "").strip() == self._cover
                ):
                    return s
        return {}

    def _awning_name(self) -> str:
        return str(self._awning().get(CONF_NAME) or self._cover)

    def _runtime(self) -> dict[str, Any]:
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        return data if isinstance(data, dict) else {}

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
    def is_on(self) -> bool:
        return bool(guard_status(self._runtime(), self._cover).get("barred"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = guard_status(self._runtime(), self._cover)
        release_at = status.get("release_at")
        remaining = None
        if release_at is not None:
            # Stored as a monotonic timestamp, which says nothing on its own –
            # what a user wants to read is "another four minutes".
            remaining = max(0, int(round(release_at - time.monotonic())))
        return {
            "cover_entity_id": self._cover,
            "awning_name": self._awning_name(),
            "reasons": list(status.get("reasons") or []),
            "retracted": bool(status.get("retracted")),
            "release_in_seconds": remaining,
        }
