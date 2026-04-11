"""Time-based scheduler for shutter up/down (per area, time/sun modes)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    AREA_MODE_TIME,
    AREA_MODE_SUN,
    CONF_AREA_TIME_UP,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_WE_UP,
    CONF_AREA_TIME_WE_DOWN,
    CONF_AREA_SUNRISE_OFFSET,
    CONF_AREA_SUNSET_OFFSET,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_DRIVE_AFTER_CLOSE,
)
from .helpers import (
    clear_stale_window_cycle_after_automated_up,
    filter_shutters_by_area,
    is_auto_enabled,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action

_LOGGER = logging.getLogger(__name__)


def _infer_today_sun_time(next_event: datetime | None, now: datetime) -> datetime | None:
    """Map sun.sun next_rising / next_setting to today's occurrence.

    After today's sunrise/sunset, HA reports the *next* event (often tomorrow).
    Subtract one day to approximate today's time (DST edge cases are rare).
    """
    if next_event is None:
        return None
    try:
        if next_event.date() == now.date():
            return next_event
        return next_event - timedelta(days=1)
    except (TypeError, OverflowError, ValueError):
        return None


def _parse_time(tstr: str) -> time:
    """Parse HH:MM to time."""
    try:
        parts = str(tstr or "06:00").strip().split(":")
        if len(parts) >= 2:
            return time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        pass
    return time(6, 0)


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
                    clear_stale_window_cycle_after_automated_up(data, cover)
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

    def _run_up(area: dict, trigger: str = "scheduler") -> None:
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            return
        if not is_auto_enabled(hass, entry, area):
            _LOGGER.info("[%s] area=%s: auto disabled – skipping UP", trigger, area_id)
            return
        filtered = filter_shutters_by_area(shutters, area_id, use_up=True)
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

    def _run_down(area: dict, trigger: str = "scheduler") -> None:
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            return
        if not is_auto_enabled(hass, entry, area):
            _LOGGER.info("[%s] area=%s: auto disabled – skipping DOWN", trigger, area_id)
            return
        filtered = filter_shutters_by_area(shutters, area_id, use_up=False)
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

    # Fixed-time schedule: run every minute, fire only once per event per day.
    # On setup/reload we pre-mark already-passed times for today to avoid
    # immediate catch-up movement after restart.
    fired_today = data.setdefault("_scheduler_fired", {})
    setup_now = datetime.now()
    setup_today = setup_now.date()
    setup_time = setup_now.time()
    setup_is_weekend = setup_now.weekday() >= 5
    for area in areas:
        if not isinstance(area, dict):
            continue
        if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_TIME:
            continue
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            continue
        if setup_is_weekend:
            up_t = _parse_time(area.get(CONF_AREA_TIME_WE_UP) or area.get(CONF_AREA_TIME_UP, "07:00"))
            down_t = _parse_time(area.get(CONF_AREA_TIME_WE_DOWN) or area.get(CONF_AREA_TIME_DOWN, "19:00"))
        else:
            up_t = _parse_time(area.get(CONF_AREA_TIME_UP, "07:00"))
            down_t = _parse_time(area.get(CONF_AREA_TIME_DOWN, "19:00"))
        if setup_time >= up_t:
            fired_today[f"up_{area_id}"] = setup_today
        if setup_time >= down_t:
            fired_today[f"down_{area_id}"] = setup_today

    fired_sun_up: dict[str, object] = data.setdefault("_sun_fired_up", {})
    fired_sun_down: dict[str, object] = data.setdefault("_sun_fired_down", {})

    def _sun_minute_tick(now: datetime) -> None:
        """Sun mode: drive by computed trigger times every minute.

        We do *not* rely on async_track_sunrise/sunset alone: after the astronomical
        sunrise, HA's next_rising points at tomorrow, so offset triggers for *today*
        are often never scheduled. A periodic check matches time/brightness reliability.
        """
        sun_state = hass.states.get("sun.sun")
        if not sun_state:
            _LOGGER.warning("Sun mode: sun.sun not available, skipping sun tick")
            return
        attrs = sun_state.attributes or {}
        next_rising = dt_util.parse_datetime(attrs.get("next_rising"))
        next_setting = dt_util.parse_datetime(attrs.get("next_setting"))
        now_local = dt_util.as_local(now)
        today = now_local.date()
        today_sr = _infer_today_sun_time(next_rising, now_local)
        today_ss = _infer_today_sun_time(next_setting, now_local)
        if today_sr is None or today_ss is None:
            return

        for area in areas:
            if not isinstance(area, dict):
                continue
            if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_SUN:
                continue
            area_id = str(area.get(CONF_AREA_ID) or "")
            if not area_id:
                continue
            try:
                off_up = int(area.get(CONF_AREA_SUNRISE_OFFSET, 0) or 0)
                off_down = int(area.get(CONF_AREA_SUNSET_OFFSET, 0) or 0)
            except (TypeError, ValueError):
                off_up, off_down = 0, 0
            trigger_up = today_sr + timedelta(minutes=off_up)
            trigger_down = today_ss + timedelta(minutes=off_down)

            # UP once per day: after sunrise+offset, before sunset+offset (day window)
            if fired_sun_up.get(area_id) != today:
                if trigger_up <= now_local < trigger_down and is_auto_enabled(
                    hass, entry, area
                ):
                    fired_sun_up[area_id] = today
                    _LOGGER.info(
                        "[sun-minute] area=%s: UP window (trigger=%s) – running UP",
                        area_id,
                        trigger_up.isoformat(),
                    )
                    _run_up(area, trigger="sun-minute")

            # DOWN once per day: after sunset+offset on that calendar day
            if fired_sun_down.get(area_id) != today:
                if (
                    trigger_down.date() == today
                    and now_local >= trigger_down
                    and is_auto_enabled(hass, entry, area)
                ):
                    fired_sun_down[area_id] = today
                    _LOGGER.info(
                        "[sun-minute] area=%s: DOWN (trigger=%s) – running DOWN",
                        area_id,
                        trigger_down.isoformat(),
                    )
                    _run_down(area, trigger="sun-minute")

    @callback
    def _scheduler_tick(now: datetime) -> None:
        now_local = dt_util.as_local(now)
        today = now_local.date()
        t = now_local.time()
        is_weekend = now_local.weekday() >= 5  # 5=Saturday, 6=Sunday
        for area in areas:
            if not isinstance(area, dict):
                continue
            if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_TIME:
                continue
            area_id = str(area.get(CONF_AREA_ID) or "")
            if not area_id:
                continue
            if is_weekend:
                up_t = _parse_time(area.get(CONF_AREA_TIME_WE_UP) or area.get(CONF_AREA_TIME_UP, "07:00"))
                down_t = _parse_time(area.get(CONF_AREA_TIME_WE_DOWN) or area.get(CONF_AREA_TIME_DOWN, "19:00"))
            else:
                up_t = _parse_time(area.get(CONF_AREA_TIME_UP, "07:00"))
                down_t = _parse_time(area.get(CONF_AREA_TIME_DOWN, "19:00"))
            if t >= up_t:
                key_up = f"up_{area_id}"
                if fired_today.get(key_up) != today:
                    fired_today[key_up] = today
                    _LOGGER.info("[time-scheduler] area=%s: time_up=%s reached – triggering UP", area_id, up_t)
                    _run_up(area, trigger="time-scheduler")
            if t >= down_t:
                key_down = f"down_{area_id}"
                if fired_today.get(key_down) != today:
                    fired_today[key_down] = today
                    _LOGGER.info("[time-scheduler] area=%s: time_down=%s reached – triggering DOWN", area_id, down_t)
                    _run_down(area, trigger="time-scheduler")

        _sun_minute_tick(now)

    u1 = async_track_time_change(
        hass, _scheduler_tick, hour="*", minute="*", second=0
    )
    if u1:
        data["_scheduler_unsubs"].append(u1)

    _LOGGER.info("Scheduler: %d Rollläden, Bereiche=%d", len(shutters), len(areas))
