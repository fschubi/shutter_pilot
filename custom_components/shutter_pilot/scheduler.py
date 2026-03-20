"""Time-based scheduler for shutter up/down (per area, time/sun modes)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_sunrise,
    async_track_sunset,
    async_track_time_change,
)

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    AREA_MODE_TIME,
    AREA_MODE_SUN,
    CONF_AREA_TIME_UP,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_SUNRISE_OFFSET,
    CONF_AREA_SUNSET_OFFSET,
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

_LOGGER = logging.getLogger(__name__)


def _parse_time(tstr: str) -> time:
    """Parse HH:MM to time."""
    try:
        parts = str(tstr or "06:00").strip().split(":")
        if len(parts) >= 2:
            return time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        pass
    return time(6, 0)


def _is_auto_enabled(hass: HomeAssistant, entry: ConfigEntry, area: dict) -> bool:
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


def _filter_by_area(shutters_list: list, area_id: str, use_up: bool) -> list:
    key = CONF_AREA_UP_ID if use_up else CONF_AREA_DOWN_ID
    return [s for s in shutters_list if str(s.get(key) or "").strip() == area_id]


async def setup_schedulers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up time-based and sun-based schedulers."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_scheduler_unsubs", []):
        unsub()
    data["_scheduler_unsubs"] = []
    data.setdefault("drive_after_close_pending", {})
    # Pending-Fahrten: Wenn Scheduler im Hoch-Fenster wegen Dunkelheit blockiert,
    # soll die Helligkeitslogik später „nachholen“ dürfen (z. B. Living 05:00–06:00,
    # Lux steigt aber erst 06:33 über Schwelle).
    pending_up: dict[str, object] = data.setdefault("_pending_up", {})

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in scheduler: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []

    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())

    async def drive_shutters(
        shutter_list: list[dict],
        default_position: float,
        direction: str,
        delay: int,
        apply_lock_protection: bool = False,
        area_id: str = "",
    ) -> None:
        for shutter in shutter_list:
            cover = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover:
                continue
            if default_position >= 50:
                position = shutter.get(CONF_POSITION_OPEN, default_position)
            else:
                position = shutter.get(CONF_POSITION_CLOSED, default_position)
            drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
            if apply_lock_protection and drive_after and is_window_open_or_tilted(hass, shutter):
                data["drive_after_close_pending"][cover] = {
                    "position": position,
                    "reason": direction,
                    "shutter": shutter,
                }
                _LOGGER.info(
                    "%s: %s Fenster offen – Fahrt wird nach Schließen ausgeführt (drive_after_close)",
                    direction, cover,
                )
                continue
            eff_pos = position
            if apply_lock_protection:
                eff_pos = get_effective_close_position(hass, shutter, position)
            try:
                await hass.services.async_call(
                    "cover", "set_cover_position",
                    {"entity_id": cover, "position": eff_pos},
                    blocking=True,
                )
                if default_position >= 50:
                    covers_driven_up.add(cover)
                    covers_driven_down.discard(cover)
                else:
                    covers_driven_down.add(cover)
                    covers_driven_up.discard(cover)
                if eff_pos != position:
                    _LOGGER.info("%s: %s -> %d%% (Aussperrschutz)", direction, cover, int(eff_pos))
                else:
                    _LOGGER.info("%s: %s -> %d%%", direction, cover, int(eff_pos))
            except Exception as e:
                _LOGGER.warning("Failed %s %s: %s", direction, cover, e)
            await asyncio.sleep(delay)

    def _run_up(area: dict) -> None:
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            return
        if not _is_auto_enabled(hass, entry, area):
            return
        filtered = _filter_by_area(shutters, area_id, use_up=True)
        # Rollläden weglassen, die in dieser Phase schon automatisch hochgefahren wurden.
        filtered = [s for s in filtered if (s.get(CONF_COVER_ENTITY_ID) or "") not in covers_driven_up]
        if not filtered:
            return
        # Falls es als „pending“ markiert war, jetzt erledigt.
        pending_up.pop(area_id, None)
        try:
            delay = max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            delay = DEFAULT_AREA_DRIVE_DELAY
        hass.async_create_task(
            drive_shutters(filtered, 100, f"Schedule up ({area_id})", delay, apply_lock_protection=False, area_id=area_id)
        )
        hass.async_create_task(run_group_light_action(hass, entry, area_id, "up"))

    def _run_down(area: dict) -> None:
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            return
        if not _is_auto_enabled(hass, entry, area):
            return
        filtered = _filter_by_area(shutters, area_id, use_up=False)
        # Rollläden weglassen, die in dieser Phase schon automatisch runtergefahren wurden.
        filtered = [s for s in filtered if (s.get(CONF_COVER_ENTITY_ID) or "") not in covers_driven_down]
        if not filtered:
            return
        try:
            delay = max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            delay = DEFAULT_AREA_DRIVE_DELAY
        hass.async_create_task(
            drive_shutters(
                filtered, 0, f"Schedule down ({area_id})",
                delay, apply_lock_protection=True, area_id=area_id
            )
        )
        hass.async_create_task(run_group_light_action(hass, entry, area_id, "down"))

    # Fixed-time schedule: run every minute, fire only once per event per day
    fired_today = data.setdefault("_scheduler_fired", {})

    @callback
    def _scheduler_tick(now: datetime) -> None:
        today = now.date()
        t = now.time()
        for area in areas:
            if not isinstance(area, dict):
                continue
            if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_TIME:
                continue
            area_id = str(area.get(CONF_AREA_ID) or "")
            if not area_id:
                continue
            up_t = _parse_time(area.get(CONF_AREA_TIME_UP, "07:00"))
            down_t = _parse_time(area.get(CONF_AREA_TIME_DOWN, "19:00"))
            if t >= up_t:
                key_up = f"up_{area_id}"
                if fired_today.get(key_up) != today:
                    fired_today[key_up] = today
                    _run_up(area)
            if t >= down_t:
                key_down = f"down_{area_id}"
                if fired_today.get(key_down) != today:
                    fired_today[key_down] = today
                    _run_down(area)

    u1 = async_track_time_change(
        hass, _scheduler_tick, hour="*", minute="*", second=0
    )
    if u1:
        data["_scheduler_unsubs"].append(u1)

    # Sunrise/Sunset: use HA's built-in trackers
    def _make_sunrise_cb(area: dict):
        @callback
        def _cb(event_time):
            _run_up(area)
        return _cb

    def _make_sunset_cb(area: dict):
        @callback
        def _cb(event_time):
            _run_down(area)
        return _cb

    for area in areas:
        if not isinstance(area, dict):
            continue
        if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_SUN:
            continue
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            continue
        off_up = area.get(CONF_AREA_SUNRISE_OFFSET, 0) or 0
        off_down = area.get(CONF_AREA_SUNSET_OFFSET, 0) or 0
        offset_up = timedelta(minutes=int(off_up))
        offset_down = timedelta(minutes=int(off_down))
        unsub_up = async_track_sunrise(hass, _make_sunrise_cb(area), offset=offset_up)
        if unsub_up:
            data["_scheduler_unsubs"].append(unsub_up)
        unsub_down = async_track_sunset(hass, _make_sunset_cb(area), offset=offset_down)
        if unsub_down:
            data["_scheduler_unsubs"].append(unsub_down)

    # Initial check for sun-mode areas: if HA restarts after sunrise, the
    # async_track_sunrise callback won't fire until the NEXT morning.
    # Evaluate current sun position and fire up/down as needed.
    sun_state = hass.states.get("sun.sun")
    if sun_state:
        try:
            current_elev = float(sun_state.attributes.get("elevation", 0))
        except (TypeError, ValueError, AttributeError):
            current_elev = None
        if current_elev is not None:
            for area in areas:
                if not isinstance(area, dict):
                    continue
                if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_SUN:
                    continue
                area_id = str(area.get(CONF_AREA_ID) or "")
                if not area_id:
                    continue
                if current_elev > 0:
                    _LOGGER.info(
                        "Scheduler sun initial: area=%s elev=%.1f > 0 → run_up",
                        area_id, current_elev,
                    )
                    _run_up(area)
                else:
                    _LOGGER.info(
                        "Scheduler sun initial: area=%s elev=%.1f <= 0 → run_down",
                        area_id, current_elev,
                    )
                    _run_down(area)

    _LOGGER.info("Scheduler: %d Rollläden, Bereiche=%d", len(shutters), len(areas))
