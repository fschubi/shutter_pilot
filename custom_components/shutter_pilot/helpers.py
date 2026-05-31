"""Shared helper functions for Shutter Pilot."""

from __future__ import annotations

import logging
import time
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
from .position_store import (
    SOURCE_AUTOMATION,
    SOURCE_MANUAL,
    ShutterPositionStore,
    get_position_store,
)

_LOGGER = logging.getLogger(__name__)

POSITION_TOLERANCE_PCT = 8.0
AUTOMATION_STATE_GRACE_SEC = 90.0


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


def positions_differ_significantly(
    a: float, b: float, tolerance: float = POSITION_TOLERANCE_PCT
) -> bool:
    """True if two positions differ by more than tolerance percent."""
    return abs(a - b) > tolerance


def _position_near(value: float, target: float, tolerance: float = POSITION_TOLERANCE_PCT) -> bool:
    return abs(value - target) <= tolerance


def mark_automation_pending(hass: HomeAssistant, entry: ConfigEntry, cover_entity_id: str) -> None:
    """Mark cover so the next state change is recorded as automation, not manual."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        return
    pending = data.setdefault("pending_automation_covers", set())
    pending.add(cover_entity_id)
    recent = data.setdefault("recent_automation_covers", {})
    recent[cover_entity_id] = time.monotonic()


def is_recent_automation(data: dict[str, Any], cover_entity_id: str) -> bool:
    """True if this cover was moved by automation within the grace window."""
    if cover_entity_id in data.get("pending_automation_covers", set()):
        return True
    recent = data.get("recent_automation_covers", {})
    if not isinstance(recent, dict):
        return False
    ts = recent.get(cover_entity_id)
    if ts is None:
        return False
    try:
        return (time.monotonic() - float(ts)) < AUTOMATION_STATE_GRACE_SEC
    except (TypeError, ValueError):
        return False


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
        cur = _persisted_position(hass, cover)
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


def _persisted_position(hass: HomeAssistant, cover_entity_id: str) -> float | None:
    """Read last persisted position from any config entry store."""
    domain_data = hass.data.get(DOMAIN, {})
    if not isinstance(domain_data, dict):
        return None
    for entry_id, data in domain_data.items():
        if not isinstance(data, dict):
            continue
        store = data.get("position_store")
        if isinstance(store, ShutterPositionStore):
            pos = store.get_position_sync(cover_entity_id)
            if pos is not None:
                return pos
    return None


def should_skip_automated_up(
    hass: HomeAssistant,
    entry: ConfigEntry,
    shutter: dict[str, Any],
    data: dict[str, Any],
    sun_protect_area_ids: set[str],
) -> bool:
    """True if an automated UP should not run for this shutter."""
    if should_skip_full_open_preserving_sun_protect(hass, shutter, sun_protect_area_ids):
        return True

    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
    if not cover:
        return False

    store = get_position_store(hass, entry.entry_id)
    source = store.get_source_sync(cover)
    if source != SOURCE_MANUAL:
        return False

    try:
        pos_open = float(shutter.get(CONF_POSITION_OPEN, 100))
    except (TypeError, ValueError):
        return False

    cur = get_cover_current_position(hass, cover)
    persisted = store.get_position_sync(cover)
    # Prefer persisted position: cover integrations may report wrong state after restart.
    check_pos = persisted if persisted is not None else cur
    if check_pos is None:
        return False

    if check_pos < pos_open - POSITION_TOLERANCE_PCT:
        _LOGGER.debug(
            "Skip automated UP for %s: manual position %.0f%% (HA reports %.0f%%)",
            cover,
            check_pos,
            cur if cur is not None else -1,
        )
        return True

    return False


def apply_covers_driven_from_persisted(
    hass: HomeAssistant,
    entry: ConfigEntry,
    shutters: list,
    store: ShutterPositionStore,
) -> None:
    """Restore covers_driven_up/down from persisted positions after restart."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        return

    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())
    last_positions: dict[str, float] = data.setdefault("last_positions", {})

    for shutter in shutters:
        if not isinstance(shutter, dict):
            continue
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
        if not cover:
            continue

        rec = store.get_record(cover)
        if not rec:
            continue

        try:
            pos = float(rec["position"])
        except (TypeError, ValueError, KeyError):
            continue

        last_positions[cover] = pos

        try:
            pos_open = float(shutter.get(CONF_POSITION_OPEN, 100))
            pos_closed = float(shutter.get(CONF_POSITION_CLOSED, 0))
            pos_sp = float(shutter.get(CONF_POSITION_SUN_PROTECT, 50))
        except (TypeError, ValueError):
            continue

        if _position_near(pos, pos_open):
            covers_driven_up.add(cover)
            covers_driven_down.discard(cover)
        elif _position_near(pos, pos_closed) or pos < pos_open - POSITION_TOLERANCE_PCT:
            covers_driven_down.add(cover)
            covers_driven_up.discard(cover)
        elif _position_near(pos, pos_sp):
            covers_driven_down.add(cover)
            covers_driven_up.discard(cover)

    _LOGGER.debug(
        "Restored driven state from store: up=%d down=%d",
        len(covers_driven_up),
        len(covers_driven_down),
    )


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
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_id: str,
    position: float,
    reason: str,
    *,
    source: str | None = None,
) -> None:
    """Set cover position via service call and persist."""
    mark_automation_pending(hass, entry, entity_id)
    try:
        await hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )
        _LOGGER.info("%s: %s -> %d%%", reason, entity_id, int(position))

        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if isinstance(data, dict):
            data.setdefault("last_positions", {})[entity_id] = float(position)

        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(
            entity_id,
            position,
            source or SOURCE_AUTOMATION,
        )
    except Exception as e:
        _LOGGER.warning("Failed to set %s: %s", entity_id, e)
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if isinstance(data, dict):
            data.setdefault("pending_automation_covers", set()).discard(entity_id)
            recent = data.setdefault("recent_automation_covers", {})
            recent.pop(entity_id, None)
