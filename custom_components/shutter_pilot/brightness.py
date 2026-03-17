"""Brightness sensor logic - per area (brightness mode)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WE_UP_TO,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_DOWN_TO,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
    CONF_AREA_AUTO_ENTITY_ID,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_UP_ID,
    CONF_AREA_DOWN_ID,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_DRIVE_AFTER_CLOSE,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action
from .scheduler import _parse_time  # reuse robust parser

_LOGGER = logging.getLogger(__name__)


def _is_weekend(d: datetime) -> bool:
    return d.weekday() in (5, 6)


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


def _area_window(area: dict, now: datetime, direction: str) -> bool:
    """direction: 'up' or 'down'."""
    is_we = _is_weekend(now)
    if direction == "up":
        f_key = CONF_AREA_WE_UP_FROM if is_we else CONF_AREA_W_UP_FROM
        t_key = CONF_AREA_WE_UP_TO if is_we else CONF_AREA_W_UP_TO
    else:
        f_key = CONF_AREA_WE_DOWN_FROM if is_we else CONF_AREA_W_DOWN_FROM
        t_key = CONF_AREA_WE_DOWN_TO if is_we else CONF_AREA_W_DOWN_TO
    start = _parse_time(area.get(f_key, "00:00"))
    end = _parse_time(area.get(t_key, "23:59"))
    t = now.time()
    if start <= end:
        return start <= t <= end
    # overnight window (e.g. 22:00 -> 06:00)
    return t >= start or t <= end


async def setup_brightness_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up brightness sensor listener."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    # Clean up previous listeners
    for unsub in data.get("_brightness_unsubs", []):
        unsub()
    data["_brightness_unsubs"] = []
    # Gemeinsame Sperren mit Scheduler/Elevation: Rollladen in dieser Phase schon automatisch bewegt.
    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())
    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    pending_up = data.setdefault("_pending_up", {})

    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []
    # Only areas in brightness mode with a sensor configured are tracked
    brightness_areas: list[dict] = []
    for a in areas:
        if not isinstance(a, dict):
            continue
        if str(a.get(CONF_AREA_MODE) or "") != AREA_MODE_BRIGHTNESS:
            continue
        sensor = str(a.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
        if sensor:
            brightness_areas.append(a)
    if not brightness_areas:
        _LOGGER.debug("No brightness areas configured, skipping")
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in brightness listener: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    opts = entry.options

    async def _set_cover_position_with_delay(
        hass: HomeAssistant,
        entity_id: str,
        position: float,
        reason: str,
        delay: int,
        index: int,
    ) -> None:
        if delay > 0 and index > 0:
            await asyncio.sleep(delay * index)
        await _set_cover_position(hass, entity_id, position, reason)

    @callback
    def _on_brightness_change(entity_id: str, old_state: Any, new_state: Any) -> None:
        if new_state is None or new_state.state in (None, "unknown", "unavailable"):
            return

        try:
            lux = float(new_state.state)
        except (TypeError, ValueError):
            return

        now = datetime.now()
        today = now.date()

        for area in brightness_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            if not _is_auto_enabled(hass, entry, area):
                continue

            sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
            if entity_id != sensor_id:
                continue

            try:
                down_threshold = int(area.get(CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD, DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD))
            except (TypeError, ValueError):
                down_threshold = DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD
            try:
                up_threshold = int(area.get(CONF_AREA_BRIGHTNESS_UP_THRESHOLD, DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD))
            except (TypeError, ValueError):
                up_threshold = DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD

            try:
                drive_delay = max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
            except (TypeError, ValueError):
                drive_delay = DEFAULT_AREA_DRIVE_DELAY

            handled_down = False
            handled_up = False

            # Down: within down window and lux <= threshold
            if _area_window(area, now, "down") and lux <= down_threshold:
                idx = 0
                for shutter in [s for s in shutters if str(s.get(CONF_AREA_DOWN_ID) or "") == area_id]:
                    cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
                    if not cover_entity:
                        continue
                    if cover_entity in covers_driven_down:
                        continue
                    pos = shutter.get(CONF_POSITION_CLOSED, 0)
                    drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
                    if drive_after and is_window_open_or_tilted(hass, shutter):
                        data.setdefault("drive_after_close_pending", {})[cover_entity] = {
                            "position": pos,
                            "reason": "Brightness down",
                            "shutter": shutter,
                        }
                        continue
                    pos = get_effective_close_position(hass, shutter, pos)
                    hass.async_create_task(
                        _set_cover_position_with_delay(
                            hass,
                            cover_entity,
                            pos,
                            "Brightness down",
                            drive_delay,
                            idx,
                        )
                    )
                    idx += 1
                    covers_driven_down.add(cover_entity)
                    covers_driven_up.discard(cover_entity)
                    handled_down = True

                if handled_down:
                    hass.async_create_task(run_group_light_action(hass, entry, area_id, "down"))

            # Up: within up window AND lux > threshold OR pending-up for today
            is_pending = pending_up.get(area_id) == today
            within_up = _area_window(area, now, "up")
            if within_up and lux <= up_threshold:
                # mark pending if within window but still too dark
                pending_up[area_id] = today
            elif (within_up or is_pending) and lux > up_threshold:
                idx = 0
                for shutter in [s for s in shutters if str(s.get(CONF_AREA_UP_ID) or "") == area_id]:
                    cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
                    if not cover_entity:
                        continue
                    if cover_entity in covers_driven_up:
                        continue
                    pos = shutter.get(CONF_POSITION_OPEN, 100)
                    hass.async_create_task(
                        _set_cover_position_with_delay(
                            hass,
                            cover_entity,
                            pos,
                            "Brightness up",
                            drive_delay,
                            idx,
                        )
                    )
                    idx += 1
                    covers_driven_up.add(cover_entity)
                    covers_driven_down.discard(cover_entity)
                    handled_up = True

                if handled_up:
                    hass.async_create_task(run_group_light_action(hass, entry, area_id, "up"))
                    if is_pending:
                        pending_up.pop(area_id, None)

    for area in brightness_areas:
        sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
        if not sensor_id:
            continue
        unsub = async_track_state_change(hass, sensor_id, _on_brightness_change)
        if unsub:
            data["_brightness_unsubs"].append(unsub)
        _LOGGER.info("Brightness listener: %s (area=%s)", sensor_id, area.get(CONF_AREA_ID))


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
