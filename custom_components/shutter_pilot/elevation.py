"""Elevation-based sun protection - Lower shutters when sun elevation is below threshold."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_GROUP_DOWN,
    CONF_POSITION_SUN_PROTECT,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_USE_ELEVATION,
    CONF_ELEVATION_THRESHOLD,
    CONF_AUTO_LIVING,
    CONF_AUTO_SLEEP,
    CONF_AUTO_CHILDREN,
    DEFAULT_ELEVATION_THRESHOLD,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action

_LOGGER = logging.getLogger(__name__)


def _is_auto_enabled(hass: HomeAssistant, opts: dict, group: str) -> bool:
    """True if automation is enabled for this group."""
    key = {GROUP_LIVING: CONF_AUTO_LIVING, GROUP_SLEEP: CONF_AUTO_SLEEP, GROUP_CHILDREN: CONF_AUTO_CHILDREN}.get(group)
    if not key:
        return True
    entity_id = str(opts.get(key) or "").strip()
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

    use_elevation = entry.options.get(CONF_USE_ELEVATION, False)
    if use_elevation is None:
        use_elevation = False
    if not use_elevation:
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in elevation listener: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    opts = entry.options
    raw_threshold = entry.options.get(CONF_ELEVATION_THRESHOLD, DEFAULT_ELEVATION_THRESHOLD)
    try:
        threshold = float(raw_threshold)
    except (TypeError, ValueError):
        _LOGGER.warning(
            "Invalid elevation_threshold %r, falling back to default %s",
            raw_threshold,
            DEFAULT_ELEVATION_THRESHOLD,
        )
        threshold = float(DEFAULT_ELEVATION_THRESHOLD)

    # sun.sun has elevation in attributes (HA 2024+)
    sun_entity = "sun.sun"

    # Debounce: fire only once per day when sun crosses below threshold
    elevation_fired = data.setdefault("_elevation_fired", {})

    from datetime import date

    @callback
    def _on_sun_change(entity_id: str, old_state: Any, new_state: Any) -> None:
        if new_state is None:
            return
        try:
            elev = float(new_state.attributes.get("elevation", 0))
        except (TypeError, ValueError, AttributeError):
            return

        today = date.today()
        if elev < threshold:
            if elevation_fired.get("date") == today:
                return
            elevation_fired["date"] = today
            handled_groups: set[str] = set()
            covers_driven_down = data.setdefault("covers_driven_down", set())
            covers_driven_up = data.setdefault("covers_driven_up", set())
            for shutter in shutters:
                grp = shutter.get(CONF_GROUP_DOWN, GROUP_LIVING)
                if not _is_auto_enabled(hass, opts, grp):
                    continue
                cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
                if not cover_entity:
                    continue
                if cover_entity in covers_driven_down:
                    continue
                pos = shutter.get(CONF_POSITION_SUN_PROTECT, 50)
                drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
                if drive_after and is_window_open_or_tilted(hass, shutter):
                    data.setdefault("drive_after_close_pending", {})[cover_entity] = {
                        "position": pos,
                        "reason": "Elevation down",
                        "shutter": shutter,
                    }
                    _LOGGER.debug("Elevation: %s Fenster offen – drive_after_close", cover_entity)
                    continue
                pos = get_effective_close_position(hass, shutter, pos)
                hass.async_create_task(
                    _set_cover_position(hass, cover_entity, pos, "Elevation down")
                )
                covers_driven_down.add(cover_entity)
                covers_driven_up.discard(cover_entity)
                if grp not in handled_groups:
                    handled_groups.add(grp)
                    hass.async_create_task(
                        run_group_light_action(hass, entry, grp, "down")
                    )
        else:
            # Sun above threshold – reset for next day
            if elevation_fired.get("date") == today:
                elevation_fired.pop("date", None)

    unsub = async_track_state_change(hass, sun_entity, _on_sun_change)
    if unsub:
        data["_elevation_unsubs"].append(unsub)
    _LOGGER.debug("Elevation listener: sun < %s° -> sun protect", threshold)


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
