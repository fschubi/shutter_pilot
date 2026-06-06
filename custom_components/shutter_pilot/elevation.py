"""Elevation-based sun protection - per area (min-max range)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_DOWN_ID,
    CONF_AREA_UP_ID,
    CONF_POSITION_SUN_PROTECT,
    CONF_POSITION_OPEN,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
)
from .helpers import (
    elevation_in_sun_protect_range,
    get_elevation_bounds,
    is_auto_enabled,
    set_cover_position,
    set_sun_protect_active,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted

_LOGGER = logging.getLogger(__name__)

SUN_ENTITY = "sun.sun"


def _current_elevation(hass: HomeAssistant) -> float | None:
    sun_state = hass.states.get(SUN_ENTITY)
    if not sun_state:
        return None
    try:
        return float(sun_state.attributes.get("elevation", 0))
    except (TypeError, ValueError, AttributeError):
        return None


async def setup_elevation_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up periodic sun elevation evaluation for sun protection."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_elevation_unsubs", []):
        unsub()
    data["_elevation_unsubs"] = []

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []

    protect_areas: list[dict] = []
    for a in areas:
        if not isinstance(a, dict):
            continue
        if not bool(a.get(CONF_AREA_SUN_PROTECT_ENABLED, False)):
            continue
        protect_areas.append(a)
    if not protect_areas:
        return

    async def _drive_sun_protect(area: dict, elev: float) -> int:
        """Drive shutters to sun protection position. Returns count moved."""
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            return 0
        moved = 0
        try:
            delay = max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            delay = DEFAULT_AREA_DRIVE_DELAY
        idx = 0
        for shutter in [
            s for s in shutters if str(s.get(CONF_AREA_DOWN_ID) or "").strip() == area_id
        ]:
            cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover_entity:
                continue
            pos = shutter.get(CONF_POSITION_SUN_PROTECT, 50)
            drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
            if drive_after and is_window_open_or_tilted(hass, shutter):
                data.setdefault("drive_after_close_pending", {})[cover_entity] = {
                    "position": pos,
                    "reason": "Sun protect",
                    "shutter": shutter,
                }
                continue
            pos = get_effective_close_position(hass, shutter, pos)
            e_min, e_max = get_elevation_bounds(area)
            _LOGGER.info(
                "[elevation] area=%s: elev=%.1f in [%.1f–%.1f] → %s -> %d%%",
                area_id, elev, e_min, e_max, cover_entity, int(pos),
            )
            if idx > 0 and delay > 0:
                await asyncio.sleep(delay * idx)
            await set_cover_position(
                hass, entry, cover_entity, pos, f"Sun protect (area={area_id})"
            )
            idx += 1
            moved += 1
        return moved

    async def _release_sun_protect(area: dict, elev: float) -> int:
        """Drive shutters to open when elevation rises above protection range."""
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            return 0
        moved = 0
        try:
            delay = max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            delay = DEFAULT_AREA_DRIVE_DELAY
        idx = 0
        for shutter in [
            s for s in shutters if str(s.get(CONF_AREA_UP_ID) or "").strip() == area_id
        ]:
            cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover_entity:
                continue
            pos = shutter.get(CONF_POSITION_OPEN, 100)
            e_min, e_max = get_elevation_bounds(area)
            _LOGGER.info(
                "[elevation] area=%s: elev=%.1f > %.1f – release → %s -> %d%%",
                area_id, elev, e_max, cover_entity, int(pos),
            )
            if idx > 0 and delay > 0:
                await asyncio.sleep(delay * idx)
            await set_cover_position(
                hass, entry, cover_entity, pos, f"Sun protect release (area={area_id})"
            )
            idx += 1
            moved += 1
        return moved

    async def _evaluate_elevation() -> None:
        elev = _current_elevation(hass)
        if elev is None:
            return

        for area in protect_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            if not is_auto_enabled(hass, entry, area):
                continue

            e_min, e_max = get_elevation_bounds(area)
            was_active = bool(data.get("sun_protect_active", {}).get(area_id))

            if elevation_in_sun_protect_range(elev, area):
                set_sun_protect_active(data, area_id, True)
                if not was_active:
                    await _drive_sun_protect(area, elev)
            elif elev > e_max and was_active:
                set_sun_protect_active(data, area_id, False)
                await _release_sun_protect(area, elev)
            elif elev < e_min and was_active:
                set_sun_protect_active(data, area_id, False)
                _LOGGER.debug(
                    "[elevation] area=%s: elev=%.1f < min %.1f – sun protect inactive",
                    area_id, elev, e_min,
                )

    @callback
    def _elevation_tick(_now: datetime) -> None:
        hass.async_create_task(_evaluate_elevation())

    unsub = async_track_time_change(hass, _elevation_tick, hour="*", minute="*", second=0)
    if unsub:
        data["_elevation_unsubs"].append(unsub)

    hass.async_create_task(_evaluate_elevation())
    _LOGGER.info("Elevation listener: %d sun-protect areas (minute tick)", len(protect_areas))
