"""Diagnostics support for Shutter Pilot."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_SHUTTERS,
    DOMAIN,
)
from .helpers import get_sun_angles
from .position_store import get_position_store
from .schedule_times import get_next_action

# Home coordinates are the only privacy-relevant values we ever store.
TO_REDACT = {"latitude", "longitude"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    if not isinstance(data, dict):
        data = {}

    areas = entry.options.get(CONF_AREAS, [])
    areas = areas if isinstance(areas, list) else []
    shutters = entry.options.get(CONF_SHUTTERS, [])
    shutters = shutters if isinstance(shutters, list) else []

    elevation, azimuth = get_sun_angles(hass)

    next_actions: dict[str, Any] = {}
    for area in areas:
        if not isinstance(area, dict):
            continue
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            continue
        when, direction = get_next_action(hass, area)
        next_actions[area_id] = {
            "mode": str(area.get(CONF_AREA_MODE) or ""),
            "when": when.isoformat() if when else None,
            "direction": direction,
        }

    cover_states: dict[str, Any] = {}
    for shutter in shutters:
        if not isinstance(shutter, dict):
            continue
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "")
        if not cover:
            continue
        state = hass.states.get(cover)
        cover_states[cover] = {
            "available": state is not None and state.state not in ("unavailable", "unknown"),
            "state": state.state if state else None,
            "current_position": (state.attributes or {}).get("current_position") if state else None,
            "current_tilt_position": (state.attributes or {}).get("current_tilt_position") if state else None,
            "supported_features": (state.attributes or {}).get("supported_features") if state else None,
        }

    store = get_position_store(hass, entry.entry_id)
    persisted = await store.async_load()

    return {
        "entry": {
            "version": entry.version,
            "data": async_redact_data(dict(entry.data or {}), TO_REDACT),
        },
        "options": {
            "areas": areas,
            "shutters": shutters,
        },
        "runtime": {
            "master_enabled": data.get("master_enabled"),
            "auto_modes": data.get("auto_modes", {}),
            "sun_protect_active": data.get("sun_protect_active", {}),
            "sun_protect_covers": sorted(data.get("sun_protect_covers", set())),
            "sun_cond_state": data.get("sun_cond_state", {}),
            "weather": data.get("weather", {}),
            "covers_driven_up": sorted(data.get("covers_driven_up", set())),
            "covers_driven_down": sorted(data.get("covers_driven_down", set())),
            "drive_after_close_pending": sorted(
                data.get("drive_after_close_pending", {}).keys()
            ),
            "pending_up": {k: str(v) for k, v in data.get("_pending_up", {}).items()},
            "minute_callbacks": sorted(data.get("_minute_callbacks", {}).keys()),
            "minute_ticker_active": bool(data.get("_minute_ticker_unsub")),
        },
        "sun": {"elevation": elevation, "azimuth": azimuth},
        "next_actions": next_actions,
        "covers": cover_states,
        "persisted_positions": persisted,
    }
