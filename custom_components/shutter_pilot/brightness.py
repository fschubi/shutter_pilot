"""Brightness sensor logic - React to lux levels for shutters."""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_GROUP_UP,
    CONF_GROUP_DOWN,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_BRIGHTNESS_TRIGGER,
    CONF_BRIGHTNESS_ENTITY_ID,
    CONF_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_BRIGHTNESS_UP_THRESHOLD,
    CONF_BRIGHTNESS_DOWN_TIME,
    CONF_BRIGHTNESS_UP_TIME,
    CONF_BRIGHTNESS_IGNORE_TIME,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_AUTO_LIVING,
    CONF_AUTO_SLEEP,
    CONF_AUTO_CHILDREN,
    BRIGHTNESS_OFF,
    BRIGHTNESS_UP,
    BRIGHTNESS_DOWN,
    BRIGHTNESS_BOTH,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action

_LOGGER = logging.getLogger(__name__)


def _parse_time(tstr: str | None) -> time:
    """Parse HH:MM string to time, robust gegen ungültige Werte."""
    try:
        parts = str(tstr or "16:00").strip().split(":")
        if len(parts) >= 2:
            return time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError, TypeError):
        pass
    return time(16, 0)  # default 16:00


def _current_time_in_range(
    now: datetime,
    up_time: time,
    down_time: time,
) -> tuple[bool, bool]:
    """Return (is_up_window, is_down_window).
    is_up_window: true if we're in the "up" time window (morning to afternoon)
    is_down_window: true if we're in the "down" time window (afternoon onwards)
    """
    now_t = now.time()
    if up_time <= down_time:
        is_up = up_time <= now_t < down_time
        is_down = now_t >= down_time or now_t < up_time
    else:
        is_up = now_t >= up_time or now_t < down_time
        is_down = down_time <= now_t < up_time
    return is_up, is_down


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


async def setup_brightness_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up brightness sensor listener."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_brightness_unsubs", []):
        unsub()
    data["_brightness_unsubs"] = []

    raw_brightness_entity = entry.options.get(CONF_BRIGHTNESS_ENTITY_ID, "")
    brightness_entity = str(raw_brightness_entity or "").strip()
    if not brightness_entity:
        _LOGGER.debug("No brightness entity configured, skipping")
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in brightness listener: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    opts = entry.options

    raw_down = entry.options.get(CONF_BRIGHTNESS_DOWN_THRESHOLD, 400)
    raw_up = entry.options.get(CONF_BRIGHTNESS_UP_THRESHOLD, 500)
    try:
        down_threshold = int(raw_down)
    except (TypeError, ValueError):
        _LOGGER.warning(
            "Invalid brightness down threshold %r, falling back to 400", raw_down
        )
        down_threshold = 400
    try:
        up_threshold = int(raw_up)
    except (TypeError, ValueError):
        _LOGGER.warning(
            "Invalid brightness up threshold %r, falling back to 500", raw_up
        )
        up_threshold = 500

    down_time_str = entry.options.get(CONF_BRIGHTNESS_DOWN_TIME, "16:00") or "16:00"
    up_time_str = entry.options.get(CONF_BRIGHTNESS_UP_TIME, "05:00") or "05:00"
    down_time = _parse_time(down_time_str)
    up_time = _parse_time(up_time_str)
    ignore_time = bool(entry.options.get(CONF_BRIGHTNESS_IGNORE_TIME, True))

    shutters_down = [s for s in shutters if s.get(CONF_BRIGHTNESS_TRIGGER) in (BRIGHTNESS_DOWN, BRIGHTNESS_BOTH)]
    shutters_up = [s for s in shutters if s.get(CONF_BRIGHTNESS_TRIGGER) in (BRIGHTNESS_UP, BRIGHTNESS_BOTH)]

    @callback
    def _on_brightness_change(entity_id: str, old_state: Any, new_state: Any) -> None:
        if new_state is None or new_state.state in (None, "unknown", "unavailable"):
            return

        try:
            lux = float(new_state.state)
        except (TypeError, ValueError):
            return

        now = datetime.now()
        if ignore_time:
            is_up_window, is_down_window = True, True
        else:
            is_up_window, is_down_window = _current_time_in_range(now, up_time, down_time)

        handled_groups_down: set[str] = set()
        handled_groups_up: set[str] = set()

        # Down logic: time >= down_time AND lux <= down_threshold
        if is_down_window and lux <= down_threshold and shutters_down:
            data["brightness_down"] = True
            for shutter in shutters_down:
                grp = shutter.get(CONF_GROUP_DOWN, GROUP_LIVING)
                if not _is_auto_enabled(hass, opts, grp):
                    continue
                cover_entity = shutter[CONF_COVER_ENTITY_ID]
                pos = shutter.get(CONF_POSITION_CLOSED, 0)
                drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
                if drive_after and is_window_open_or_tilted(hass, shutter):
                    data.setdefault("drive_after_close_pending", {})[cover_entity] = {
                        "position": pos,
                        "reason": "Brightness down",
                        "shutter": shutter,
                    }
                    _LOGGER.info("Brightness down: %s Fenster offen – drive_after_close", cover_entity)
                    continue
                pos = get_effective_close_position(hass, shutter, pos)
                hass.async_create_task(
                    _set_cover_position(hass, cover_entity, pos, "Brightness down")
                )
                if grp not in handled_groups_down:
                    handled_groups_down.add(grp)
                    hass.async_create_task(
                        run_group_light_action(hass, entry, grp, "down")
                    )

        # Up logic: between up_time and down_time AND lux > up_threshold
        elif is_up_window and lux > up_threshold and shutters_up:
            data["brightness_down"] = False
            for shutter in shutters_up:
                grp = shutter.get(CONF_GROUP_UP, GROUP_LIVING)
                if not _is_auto_enabled(hass, opts, grp):
                    continue
                cover_entity = shutter[CONF_COVER_ENTITY_ID]
                pos = shutter.get(CONF_POSITION_OPEN, 100)
                hass.async_create_task(
                    _set_cover_position(hass, cover_entity, pos, "Brightness up")
                )
                if grp not in handled_groups_up:
                    handled_groups_up.add(grp)
                    hass.async_create_task(
                        run_group_light_action(hass, entry, grp, "up")
                    )

    unsub = async_track_state_change(
        hass, brightness_entity, _on_brightness_change
    )
    if unsub:
        data["_brightness_unsubs"].append(unsub)
    _LOGGER.info(
        "Brightness listener: %s (down<=%d, up>%d)",
        brightness_entity, down_threshold, up_threshold,
    )


async def _set_cover_position(
    hass: HomeAssistant, entity_id: str, position: float, reason: str
) -> None:
    try:
        await hass.services.async_call(
            "cover", "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )
        _LOGGER.debug("%s: Set %s to %d%%", reason, entity_id, int(position))
    except Exception as e:
        _LOGGER.warning("Failed to set %s: %s", entity_id, e)
