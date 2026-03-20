"""Elevation-based sun protection - per area."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_ELEVATION_THRESHOLD,
    DEFAULT_AREA_ELEVATION_THRESHOLD,
    CONF_AREA_AUTO_ENTITY_ID,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_DOWN_ID,
    CONF_POSITION_SUN_PROTECT,
    CONF_DRIVE_AFTER_CLOSE,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action

_LOGGER = logging.getLogger(__name__)


def _is_auto_enabled(hass: HomeAssistant, entry: ConfigEntry, area: dict) -> bool:
    area_id = str(area.get(CONF_AREA_ID) or "")
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    auto_modes = data.get("auto_modes", {}) if isinstance(data, dict) else {}
    if isinstance(auto_modes, dict) and area_id in auto_modes:
        return bool(auto_modes.get(area_id))

    entity_id = str(area.get(CONF_AREA_AUTO_ENTITY_ID) or "").strip()
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if not state:
        return True
    return str(state.state).lower() in ("on", "true", "1")


async def setup_elevation_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up sun elevation listener for sun protection."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_elevation_unsubs", []):
        unsub()
    data["_elevation_unsubs"] = []

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in elevation listener: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []
    # Only areas with sun protection enabled are considered
    protect_areas: list[dict] = []
    for a in areas:
        if not isinstance(a, dict):
            continue
        if not bool(a.get(CONF_AREA_SUN_PROTECT_ENABLED, False)):
            continue
        protect_areas.append(a)
    if not protect_areas:
        return

    # sun.sun has elevation in attributes (HA 2024+)
    sun_entity = "sun.sun"

    # Debounce: fire only once per day when sun crosses below threshold
    elevation_fired = data.setdefault("_elevation_fired", {})

    from datetime import date

    @callback
    def _on_sun_change(event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        try:
            elev = float(new_state.attributes.get("elevation", 0))
        except (TypeError, ValueError, AttributeError):
            return

        today = date.today()
        handled_areas: set[str] = set()
        covers_driven_down = data.setdefault("covers_driven_down", set())
        covers_driven_up = data.setdefault("covers_driven_up", set())

        for area in protect_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            if not _is_auto_enabled(hass, entry, area):
                continue

            raw_threshold = area.get(
                CONF_AREA_ELEVATION_THRESHOLD, DEFAULT_AREA_ELEVATION_THRESHOLD
            )
            try:
                threshold = float(raw_threshold)
            except (TypeError, ValueError):
                threshold = float(DEFAULT_AREA_ELEVATION_THRESHOLD)

            if elev < threshold:
                if elevation_fired.get(area_id) == today:
                    continue
                elevation_fired[area_id] = today

                for shutter in [
                    s
                    for s in shutters
                    if str(s.get(CONF_AREA_DOWN_ID) or "").strip() == area_id
                ]:
                    cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
                    if not cover_entity:
                        continue
                    if cover_entity in covers_driven_down:
                        continue
                    pos = shutter.get(CONF_POSITION_SUN_PROTECT, 50)
                    drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
                    if drive_after and is_window_open_or_tilted(hass, shutter):
                        data.setdefault("drive_after_close_pending", {})[
                            cover_entity
                        ] = {
                            "position": pos,
                            "reason": "Elevation down",
                            "shutter": shutter,
                        }
                        continue
                    pos = get_effective_close_position(hass, shutter, pos)
                    hass.async_create_task(
                        _set_cover_position(
                            hass, cover_entity, pos, "Elevation down"
                        )
                    )
                    covers_driven_down.add(cover_entity)
                    covers_driven_up.discard(cover_entity)
                    if area_id not in handled_areas:
                        handled_areas.add(area_id)
                        hass.async_create_task(
                            run_group_light_action(hass, entry, area_id, "down")
                        )
            else:
                # Sun above threshold – reset for next trigger
                if elevation_fired.get(area_id) == today:
                    elevation_fired.pop(area_id, None)

    unsub = async_track_state_change_event(hass, sun_entity, _on_sun_change)
    if unsub:
        data["_elevation_unsubs"].append(unsub)

    # Prevent spurious firing after restart when the sun is already below
    # the threshold (e.g. at night).  Pre-mark those areas as "already fired
    # today" so the listener only fires on actual downward crossings.
    current_sun = hass.states.get(sun_entity)
    if current_sun:
        try:
            current_elev = float(current_sun.attributes.get("elevation", 0))
        except (TypeError, ValueError, AttributeError):
            current_elev = 0
        today = date.today()
        for area in protect_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            try:
                threshold = float(area.get(CONF_AREA_ELEVATION_THRESHOLD, DEFAULT_AREA_ELEVATION_THRESHOLD))
            except (TypeError, ValueError):
                threshold = float(DEFAULT_AREA_ELEVATION_THRESHOLD)
            if current_elev < threshold:
                elevation_fired[area_id] = today
                _LOGGER.debug(
                    "Elevation: area %s pre-marked as fired (elev=%.1f < thresh=%.1f at startup)",
                    area_id, current_elev, threshold,
                )

    _LOGGER.debug("Elevation listener: per-area sun protection enabled")


async def _set_cover_position(
    hass: HomeAssistant, entity_id: str, position: float, reason: str
) -> None:
    try:
        await hass.services.async_call(
            "cover", "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )
        _LOGGER.debug("%s: %s -> %d%%", reason, entity_id, int(position))
    except Exception as e:
        _LOGGER.warning("Failed %s %s: %s", reason, entity_id, e)
