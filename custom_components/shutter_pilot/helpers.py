"""Shared helper functions for Shutter Pilot."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_AREA_ID,
    CONF_AREA_AUTO_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_UP_ID,
    CONF_AREA_DOWN_ID,
)

_LOGGER = logging.getLogger(__name__)


def is_auto_enabled(hass: HomeAssistant, entry: ConfigEntry, area: dict) -> bool:
    """True if automation is enabled for this area. No entity = enabled."""
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


def filter_shutters_by_area(shutters: list, area_id: str, use_up: bool) -> list:
    """Filter shutters by area_up_id or area_down_id."""
    key = CONF_AREA_UP_ID if use_up else CONF_AREA_DOWN_ID
    return [s for s in shutters if str(s.get(key) or "").strip() == area_id]


async def set_cover_position(
    hass: HomeAssistant, entity_id: str, position: float, reason: str
) -> None:
    """Set cover position via service call."""
    try:
        await hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )
        _LOGGER.info("%s: %s -> %d%%", reason, entity_id, int(position))
    except Exception as e:
        _LOGGER.warning("Failed to set %s: %s", entity_id, e)
