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
    CONF_AREA_DOWN_ID,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_UP_ID,
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
)

_LOGGER = logging.getLogger(__name__)


def is_auto_enabled(hass: HomeAssistant, entry: ConfigEntry, area: dict) -> bool:
    """True if automation is enabled for this area.

    Fail-safe: if runtime data is missing (e.g. during reload), return False
    to prevent stale listeners from triggering unwanted movements.
    """
    area_id = str(area.get(CONF_AREA_ID) or "")
    domain_data = hass.data.get(DOMAIN)
    if not isinstance(domain_data, dict) or entry.entry_id not in domain_data:
        _LOGGER.debug("is_auto_enabled: no runtime data for %s – returning False (fail-safe)", area_id)
        return False
    data = domain_data.get(entry.entry_id, {})
    if not isinstance(data, dict):
        return False

    auto_modes = data.get("auto_modes", {})
    if isinstance(auto_modes, dict) and area_id in auto_modes:
        return bool(auto_modes.get(area_id))

    entity_id = str(area.get(CONF_AREA_AUTO_ENTITY_ID) or "").strip()
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if not state:
        _LOGGER.debug("is_auto_enabled: switch entity %s not found – returning False (fail-safe)", entity_id)
        return False
    return str(state.state).lower() in ("on", "true", "1")


def filter_shutters_by_area(shutters: list, area_id: str, use_up: bool) -> list:
    """Filter shutters by area_up_id or area_down_id."""
    key = CONF_AREA_UP_ID if use_up else CONF_AREA_DOWN_ID
    return [s for s in shutters if str(s.get(key) or "").strip() == area_id]


def get_cover_current_position(hass: HomeAssistant, entity_id: str) -> float | None:
    """Return cover current_position (0..100) if available."""
    try:
        st = hass.states.get(entity_id)
        attrs = (st.attributes or {}) if st else {}
        cur = attrs.get("current_position")
        if cur is None:
            return None
        return float(cur)
    except (TypeError, ValueError):
        return None


def sun_protect_area_ids_from_options(areas: list[Any]) -> set[str]:
    """Area ids where elevation-based sun protection is enabled."""
    out: set[str] = set()
    if not isinstance(areas, list):
        return out
    for a in areas:
        if not isinstance(a, dict):
            continue
        if not bool(a.get(CONF_AREA_SUN_PROTECT_ENABLED, False)):
            continue
        aid = str(a.get(CONF_AREA_ID) or "").strip()
        if aid:
            out.add(aid)
    return out


def should_skip_full_open_preserving_sun_protect(
    hass: HomeAssistant,
    shutter: dict[str, Any],
    sun_protect_area_ids: set[str],
) -> bool:
    """True if automated full-open should not run (cover already at sun-protect height).

    Used after HA restart when in-memory automation state is lost but the physical
    cover is still at the elevation-driven sun protection position.
    """
    down_id = str(shutter.get(CONF_AREA_DOWN_ID) or "").strip()
    if not down_id or down_id not in sun_protect_area_ids:
        return False
    cover = shutter.get(CONF_COVER_ENTITY_ID)
    if not cover:
        return False
    cur = get_cover_current_position(hass, cover)
    if cur is None:
        return False
    try:
        pos_open = float(shutter.get(CONF_POSITION_OPEN, 100))
        pos_sp = float(shutter.get(CONF_POSITION_SUN_PROTECT, 50))
    except (TypeError, ValueError):
        return False
    if cur >= pos_open - 5.0:
        return False
    if abs(cur - pos_sp) > 10.0:
        return False
    return True


def clear_stale_window_cycle_after_automated_up(
    data: dict[str, Any], cover_entity_id: str
) -> None:
    """Drop window open/tilt restore state after automation opened the cover (day phase).

    Without this, closing the window later would restore trigger_heights from before
    tilt (often closed) or run a stale drive_after_close_pending down movement.
    """
    if not cover_entity_id:
        return
    ta = data.get("trigger_actions")
    if isinstance(ta, dict):
        ta.pop(cover_entity_id, None)
    th = data.get("trigger_heights")
    if isinstance(th, dict):
        th.pop(cover_entity_id, None)
    pending = data.get("drive_after_close_pending")
    if isinstance(pending, dict):
        pending.pop(cover_entity_id, None)


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
