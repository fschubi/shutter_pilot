"""Brightness sensor logic - per area (brightness mode)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD,
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
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_UP_ID,
    CONF_AREA_DOWN_ID,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_DRIVE_AFTER_CLOSE,
)
from .helpers import is_auto_enabled, set_cover_position
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action
from .scheduler import _parse_time

_LOGGER = logging.getLogger(__name__)


def _is_weekend(d: datetime) -> bool:
    return d.weekday() in (5, 6)


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
        await set_cover_position(hass, entity_id, position, reason)

    def _process_brightness(entity_id: str, new_state) -> None:
        """Evaluate brightness for a sensor state (used by listener AND initial check)."""
        if new_state is None:
            return
        state_str = getattr(new_state, "state", None)
        if state_str in (None, "unknown", "unavailable"):
            return
        try:
            lux = float(state_str)
        except (TypeError, ValueError):
            return

        now = datetime.now()
        today = now.date()

        for area in brightness_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            if not is_auto_enabled(hass, entry, area):
                _LOGGER.debug("Brightness: area %s auto disabled, skip", area_id)
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

            _LOGGER.info(
                "Brightness eval: area=%s sensor=%s lux=%.1f up_thresh=%d down_thresh=%d",
                area_id, sensor_id, lux, up_threshold, down_threshold,
            )

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

            _LOGGER.debug(
                "Brightness UP check: area=%s within_up=%s is_pending=%s lux=%.1f > thresh=%d => %s",
                area_id, within_up, is_pending, lux, up_threshold, lux > up_threshold,
            )

            if within_up and lux <= up_threshold:
                pending_up[area_id] = today
                _LOGGER.info("Brightness: area %s marked pending (lux %.1f <= %d)", area_id, lux, up_threshold)
            elif (within_up or is_pending) and lux > up_threshold:
                idx = 0
                for shutter in [s for s in shutters if str(s.get(CONF_AREA_UP_ID) or "") == area_id]:
                    cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
                    if not cover_entity:
                        continue
                    if cover_entity in covers_driven_up:
                        _LOGGER.debug("Brightness up: %s already driven up, skip", cover_entity)
                        continue
                    pos = shutter.get(CONF_POSITION_OPEN, 100)
                    _LOGGER.info("Brightness up: driving %s -> %d%%", cover_entity, pos)
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

    @callback
    def _on_brightness_change(event) -> None:
        """Handle brightness sensor state change event."""
        new_state = event.data.get("new_state")
        entity_id = event.data.get("entity_id", "")
        _process_brightness(entity_id, new_state)

    # Register listeners for each brightness sensor
    tracked_sensors: set[str] = set()
    for area in brightness_areas:
        sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
        if not sensor_id or sensor_id in tracked_sensors:
            continue
        tracked_sensors.add(sensor_id)
        unsub = async_track_state_change_event(hass, sensor_id, _on_brightness_change)
        if unsub:
            data["_brightness_unsubs"].append(unsub)
        _LOGGER.info("Brightness listener registered: %s (area=%s)", sensor_id, area.get(CONF_AREA_ID))

    # Initial check: evaluate current sensor values so shutters react even
    # if the sensor was already above/below threshold when HA started.
    for area in brightness_areas:
        sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
        if not sensor_id:
            continue
        current_state = hass.states.get(sensor_id)
        if current_state is not None:
            _LOGGER.info(
                "Brightness initial check: sensor=%s current=%s",
                sensor_id, current_state.state,
            )
            _process_brightness(sensor_id, current_state)
