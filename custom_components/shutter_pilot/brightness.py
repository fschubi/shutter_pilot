"""Brightness sensor logic - per area (brightness mode)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_B_DOWN_AFTER_SUNSET,
    CONF_AREA_B_UP_BEFORE_SUNRISE,
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
    CONF_DRIVE_AFTER_CLOSE,
    ROLE_CLOSED,
    ROLE_OPEN,
)
from .helpers import (
    clear_manual_override_for_covers,
    clear_stale_window_cycle_after_automated_up,
    get_position_for_role,
    get_tilt_for_role,
    is_auto_enabled,
    is_shutter_automation_enabled,
    remember_drive_after_close,
    resolve_close_role,
    set_cover_position,
    should_skip_automated_up,
    sun_protect_area_ids_from_options,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action
from .schedule_times import (
    _local_sun_time,
    infer_today_sun_time,
    is_weekend_schedule,
    parse_time,
)

_LOGGER = logging.getLogger(__name__)

_parse_time = parse_time


def _sun_bound_ok(
    hass: HomeAssistant | None, area: dict, now: datetime, direction: str
) -> bool:
    """True unless a sun-relative bound still blocks this direction.

    The clock windows cannot express "not before sunset minus 60 minutes",
    because sunset moves through the year. Without it a thunderstorm in the
    afternoon pushed the lux below the threshold and closed the shutters in
    broad daylight.
    """
    if hass is None:
        return True
    key = (
        CONF_AREA_B_DOWN_AFTER_SUNSET
        if direction == "down"
        else CONF_AREA_B_UP_BEFORE_SUNRISE
    )
    raw = area.get(key)
    if raw is None or str(raw).strip() == "":
        return True
    try:
        offset = int(raw)
    except (TypeError, ValueError):
        return True

    sun_state = hass.states.get("sun.sun")
    if sun_state is None:
        # No sun data – never block, same fail-open rule as everywhere else.
        return True
    attrs = sun_state.attributes or {}
    now_local = dt_util.as_local(now)
    event = _local_sun_time(
        attrs.get("next_setting" if direction == "down" else "next_rising")
    )
    today = infer_today_sun_time(event, now_local)
    if today is None:
        return True

    if direction == "down":
        # "Not before sunset minus N minutes".
        return now_local >= today - timedelta(minutes=offset)
    # "Not before sunrise minus N minutes".
    return now_local >= today - timedelta(minutes=offset)


def _area_window(
    area: dict, now: datetime, direction: str, hass: HomeAssistant | None = None
) -> bool:
    """True if `now` lies inside the allowed window. direction: 'up' or 'down'."""
    if not _sun_bound_ok(hass, area, now, direction):
        return False
    is_we = is_weekend_schedule(hass, area, now)
    if direction == "up":
        f_key = CONF_AREA_WE_UP_FROM if is_we else CONF_AREA_W_UP_FROM
        t_key = CONF_AREA_WE_UP_TO if is_we else CONF_AREA_W_UP_TO
    else:
        f_key = CONF_AREA_WE_DOWN_FROM if is_we else CONF_AREA_W_DOWN_FROM
        t_key = CONF_AREA_WE_DOWN_TO if is_we else CONF_AREA_W_DOWN_TO
    start = parse_time(area.get(f_key, "00:00"))
    end = parse_time(area.get(t_key, "23:59"))
    t = now.time()
    if start <= end:
        return start <= t <= end
    return t >= start or t <= end


async def setup_brightness_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up brightness sensor listener."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_brightness_unsubs", []):
        unsub()
    data["_brightness_unsubs"] = []

    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())
    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    pending_up = data.setdefault("_pending_up", {})

    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []
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
        shutters = []

    raw_areas_opts = entry.options.get(CONF_AREAS, [])
    if not isinstance(raw_areas_opts, list):
        raw_areas_opts = []
    sun_protect_area_ids = sun_protect_area_ids_from_options(raw_areas_opts)

    async def _set_cover_position_with_delay(
        entity_id: str,
        position: float,
        reason: str,
        delay: int,
        index: int,
        tilt: float | None = None,
        area_id: str = "",
    ) -> None:
        if delay > 0 and index > 0:
            await asyncio.sleep(delay * index)
        await set_cover_position(
            hass,
            entry,
            entity_id,
            position,
            reason,
            tilt_position=tilt,
            area_id=area_id,
        )

    def _process_brightness(entity_id: str, new_state) -> None:
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
                continue

            sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
            if entity_id != sensor_id:
                continue

            try:
                down_threshold = int(
                    area.get(CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD, DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD)
                )
            except (TypeError, ValueError):
                down_threshold = DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD
            try:
                up_threshold = int(
                    area.get(CONF_AREA_BRIGHTNESS_UP_THRESHOLD, DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD)
                )
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

            moved_down = False
            moved_up = False

            if _area_window(area, now, "down", hass) and lux <= down_threshold:
                idx = 0
                down_covers: list[str] = []
                for shutter in [s for s in shutters if str(s.get(CONF_AREA_DOWN_ID) or "") == area_id]:
                    cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
                    if not cover_entity:
                        continue
                    if cover_entity in covers_driven_down:
                        continue
                    if not is_shutter_automation_enabled(hass, entry, shutter):
                        continue
                    # Same decision as the scheduler: a shutter that must not
                    # freeze shut, or only close part way on a mild evening,
                    # has to behave that way here too.
                    close_role = resolve_close_role(hass, area, shutter, data)
                    pos = get_position_for_role(shutter, close_role)
                    tilt = get_tilt_for_role(shutter, close_role)
                    drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
                    if drive_after and is_window_open_or_tilted(hass, shutter):
                        remember_drive_after_close(
                            hass, entry, data, cover_entity,
                            position=pos, tilt=tilt,
                            reason="Brightness down", shutter=shutter,
                        )
                        # Wie im Scheduler: die Fahrt gilt als erledigt, sie
                        # wartet nur noch aufs Fenster. Sonst ueberspringt der
                        # naechste Morgen genau diesen Rollladen – und der
                        # Merker wuerde hier jede Minute neu geschrieben.
                        covers_driven_down.add(cover_entity)
                        covers_driven_up.discard(cover_entity)
                        continue
                    pos = get_effective_close_position(hass, shutter, pos)
                    down_covers.append(cover_entity)
                    hass.async_create_task(
                        _set_cover_position_with_delay(
                            cover_entity, pos, "Brightness down", drive_delay, idx,
                            tilt=tilt, area_id=area_id,
                        )
                    )
                    idx += 1
                    covers_driven_down.add(cover_entity)
                    covers_driven_up.discard(cover_entity)
                    moved_down = True

                if moved_down:
                    hass.async_create_task(
                        clear_manual_override_for_covers(hass, entry, down_covers)
                    )
                    hass.async_create_task(run_group_light_action(hass, entry, area_id, "down"))

            is_pending = pending_up.get(area_id) == today
            within_up = _area_window(area, now, "up", hass)

            if within_up and lux <= up_threshold:
                pending_up[area_id] = today
                _LOGGER.info(
                    "Brightness: area %s marked pending (lux %.1f <= %d)",
                    area_id, lux, up_threshold,
                )
            elif (within_up or is_pending) and lux > up_threshold:
                # Shading is judged per shutter inside the loop. Asking the
                # area aggregate here as well held back every window of the
                # room as soon as a single one was shaded – rooms whose windows
                # face different ways are exactly the case that has its own
                # sensors and its own direction.
                idx = 0
                up_covers: list[str] = []
                for shutter in [s for s in shutters if str(s.get(CONF_AREA_UP_ID) or "") == area_id]:
                    cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
                    if not cover_entity:
                        continue
                    if cover_entity in covers_driven_up:
                        continue
                    if not is_shutter_automation_enabled(hass, entry, shutter):
                        continue
                    if should_skip_automated_up(
                        hass,
                        entry,
                        shutter,
                        data,
                        sun_protect_area_ids,
                        within_up_window=within_up or is_pending,
                        area=area,
                    ):
                        _LOGGER.info(
                            "Brightness up: %s übersprungen (Sonnenschutz/manuelle Position)",
                            cover_entity,
                        )
                        continue
                    pos = get_position_for_role(shutter, ROLE_OPEN)
                    tilt = get_tilt_for_role(shutter, ROLE_OPEN)
                    _LOGGER.info("Brightness up: driving %s -> %d%%", cover_entity, pos)
                    up_covers.append(cover_entity)
                    hass.async_create_task(
                        _set_cover_position_with_delay(
                            cover_entity, pos, "Brightness up", drive_delay, idx,
                            tilt=tilt, area_id=area_id,
                        )
                    )
                    idx += 1
                    covers_driven_up.add(cover_entity)
                    covers_driven_down.discard(cover_entity)
                    clear_stale_window_cycle_after_automated_up(data, cover_entity)
                    moved_up = True

                if moved_up:
                    hass.async_create_task(
                        clear_manual_override_for_covers(hass, entry, up_covers)
                    )
                    hass.async_create_task(run_group_light_action(hass, entry, area_id, "up"))
                    if is_pending:
                        pending_up.pop(area_id, None)

    @callback
    def _on_brightness_change(event) -> None:
        new_state = event.data.get("new_state")
        entity_id = event.data.get("entity_id", "")
        _process_brightness(entity_id, new_state)

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
