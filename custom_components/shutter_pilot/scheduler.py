"""Time-based scheduler for shutter up/down (Sunrise/Sunset and fixed times)."""

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
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_GROUP_UP,
    CONF_GROUP_DOWN,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_DRIVE_DELAY,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_BRIGHTNESS_ENTITY_ID,
    CONF_BRIGHTNESS_UP_THRESHOLD,
    CONF_AUTO_LIVING,
    CONF_AUTO_SLEEP,
    CONF_AUTO_CHILDREN,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
    GROUP_ALL,
    TIME_TYPE_FIXED,
    TIME_TYPE_SUNRISE,
    TIME_TYPE_SUNSET,
    CONF_LIVING_TYPE_UP,
    CONF_LIVING_TYPE_DOWN,
    CONF_LIVING_W_UP_MIN,
    CONF_LIVING_W_UP_MAX,
    CONF_LIVING_W_DOWN,
    CONF_LIVING_WE_UP_MIN,
    CONF_LIVING_WE_UP_MAX,
    CONF_LIVING_WE_DOWN,
    CONF_LIVING_SUNRISE_OFFSET,
    CONF_LIVING_SUNSET_OFFSET,
    CONF_SLEEP_TYPE_UP,
    CONF_SLEEP_TYPE_DOWN,
    CONF_SLEEP_W_UP_MIN,
    CONF_SLEEP_W_UP_MAX,
    CONF_SLEEP_W_DOWN,
    CONF_SLEEP_WE_UP_MIN,
    CONF_SLEEP_WE_UP_MAX,
    CONF_SLEEP_WE_DOWN,
    CONF_SLEEP_SUNRISE_OFFSET,
    CONF_SLEEP_SUNSET_OFFSET,
    CONF_CHILDREN_TYPE_UP,
    CONF_CHILDREN_TYPE_DOWN,
    CONF_CHILDREN_W_UP_MIN,
    CONF_CHILDREN_W_UP_MAX,
    CONF_CHILDREN_W_DOWN,
    CONF_CHILDREN_WE_UP_MIN,
    CONF_CHILDREN_WE_UP_MAX,
    CONF_CHILDREN_WE_DOWN,
    CONF_CHILDREN_SUNRISE_OFFSET,
    CONF_CHILDREN_SUNSET_OFFSET,
    CONF_W_SHUTTER_UP_MIN,
    CONF_W_SHUTTER_UP_MAX,
    CONF_W_SHUTTER_DOWN,
    CONF_WE_SHUTTER_UP_MIN,
    CONF_WE_SHUTTER_UP_MAX,
    CONF_WE_SHUTTER_DOWN,
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


def _brightness_blocks_scheduler_up(hass: HomeAssistant, opts: dict, now: datetime) -> bool:
    """True if a brightness sensor is configured and current lux is still <= up_threshold.
    In that case the scheduler must NOT drive shutters up; the brightness listener will do it
    when lux rises above the threshold.
    """
    raw_entity = opts.get(CONF_BRIGHTNESS_ENTITY_ID, "")
    if isinstance(raw_entity, list):
        brightness_entity = (raw_entity[0] if raw_entity else "") or ""
    else:
        brightness_entity = str(raw_entity or "").strip()
    if not brightness_entity:
        return False

    state = hass.states.get(brightness_entity)
    if not state or state.state in (None, "unknown", "unavailable"):
        return True  # sensor unavailable -> block to be safe
    try:
        lux = float(state.state)
    except (TypeError, ValueError):
        return True

    try:
        up_threshold = int(opts.get(CONF_BRIGHTNESS_UP_THRESHOLD, 500))
    except (TypeError, ValueError):
        up_threshold = 500

    if lux > up_threshold:
        return False
    return True


def _is_weekend(d: datetime) -> bool:
    """True if Saturday (5) or Sunday (6)."""
    return d.weekday() in (5, 6)


def _get_group_schedule(opts: dict, group: str) -> dict:
    """Return schedule config for group. Falls back to legacy keys for Living."""
    def _offset_min(val) -> int:
        try:
            return int(val) if val is not None else 0
        except (TypeError, ValueError):
            return 0

    if group == GROUP_LIVING:
        return {
            "type_up": opts.get(CONF_LIVING_TYPE_UP, TIME_TYPE_FIXED),
            "type_down": opts.get(CONF_LIVING_TYPE_DOWN, TIME_TYPE_FIXED),
            "sunrise_offset": _offset_min(opts.get(CONF_LIVING_SUNRISE_OFFSET, 0)),
            "sunset_offset": _offset_min(opts.get(CONF_LIVING_SUNSET_OFFSET, 0)),
            "w_up_min": _parse_time(opts.get(CONF_LIVING_W_UP_MIN) or opts.get(CONF_W_SHUTTER_UP_MIN, "05:00")),
            "w_up_max": _parse_time(opts.get(CONF_LIVING_W_UP_MAX) or opts.get(CONF_W_SHUTTER_UP_MAX, "06:00")),
            "w_down": _parse_time(opts.get(CONF_LIVING_W_DOWN) or opts.get(CONF_W_SHUTTER_DOWN, "22:00")),
            "we_up_min": _parse_time(opts.get(CONF_LIVING_WE_UP_MIN) or opts.get(CONF_WE_SHUTTER_UP_MIN, "05:00")),
            "we_up_max": _parse_time(opts.get(CONF_LIVING_WE_UP_MAX) or opts.get(CONF_WE_SHUTTER_UP_MAX, "06:00")),
            "we_down": _parse_time(opts.get(CONF_LIVING_WE_DOWN) or opts.get(CONF_WE_SHUTTER_DOWN, "22:00")),
        }
    if group == GROUP_SLEEP:
        return {
            "type_up": opts.get(CONF_SLEEP_TYPE_UP, TIME_TYPE_FIXED),
            "type_down": opts.get(CONF_SLEEP_TYPE_DOWN, TIME_TYPE_FIXED),
            "sunrise_offset": _offset_min(opts.get(CONF_SLEEP_SUNRISE_OFFSET, 0)),
            "sunset_offset": _offset_min(opts.get(CONF_SLEEP_SUNSET_OFFSET, 0)),
            "w_up_min": _parse_time(opts.get(CONF_SLEEP_W_UP_MIN, "05:00")),
            "w_up_max": _parse_time(opts.get(CONF_SLEEP_W_UP_MAX, "06:00")),
            "w_down": _parse_time(opts.get(CONF_SLEEP_W_DOWN, "22:00")),
            "we_up_min": _parse_time(opts.get(CONF_SLEEP_WE_UP_MIN, "05:00")),
            "we_up_max": _parse_time(opts.get(CONF_SLEEP_WE_UP_MAX, "06:00")),
            "we_down": _parse_time(opts.get(CONF_SLEEP_WE_DOWN, "22:00")),
        }
    if group == GROUP_CHILDREN:
        return {
            "type_up": opts.get(CONF_CHILDREN_TYPE_UP, TIME_TYPE_FIXED),
            "type_down": opts.get(CONF_CHILDREN_TYPE_DOWN, TIME_TYPE_FIXED),
            "sunrise_offset": _offset_min(opts.get(CONF_CHILDREN_SUNRISE_OFFSET, 0)),
            "sunset_offset": _offset_min(opts.get(CONF_CHILDREN_SUNSET_OFFSET, 0)),
            "w_up_min": _parse_time(opts.get(CONF_CHILDREN_W_UP_MIN, "05:00")),
            "w_up_max": _parse_time(opts.get(CONF_CHILDREN_W_UP_MAX, "06:00")),
            "w_down": _parse_time(opts.get(CONF_CHILDREN_W_DOWN, "22:00")),
            "we_up_min": _parse_time(opts.get(CONF_CHILDREN_WE_UP_MIN, "05:00")),
            "we_up_max": _parse_time(opts.get(CONF_CHILDREN_WE_UP_MAX, "06:00")),
            "we_down": _parse_time(opts.get(CONF_CHILDREN_WE_DOWN, "22:00")),
        }
    return {}


def _is_auto_enabled(hass: HomeAssistant, opts: dict, group: str) -> bool:
    """True if automation is enabled for this group. No entity = enabled."""
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


def _filter_by_group(shutters_list: list, group: str, use_group_up: bool) -> list:
    key = CONF_GROUP_UP if use_group_up else CONF_GROUP_DOWN
    if group == GROUP_ALL:
        return shutters_list
    return [s for s in shutters_list if s.get(key) == group]


async def setup_schedulers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up time-based and sun-based schedulers."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_scheduler_unsubs", []):
        unsub()
    data["_scheduler_unsubs"] = []
    data.setdefault("drive_after_close_pending", {})

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in scheduler: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    drive_delay = entry.options.get(CONF_DRIVE_DELAY, 10)
    opts = entry.options

    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())

    async def drive_shutters(
        shutter_list: list[dict],
        position: float,
        direction: str,
        apply_lock_protection: bool = False,
        group: str = GROUP_LIVING,
    ) -> None:
        for shutter in shutter_list:
            cover = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover:
                continue
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
                if position >= 50:
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
            await asyncio.sleep(drive_delay)

    def _run_up(group_name: str) -> None:
        if not _is_auto_enabled(hass, opts, group_name):
            return
        filtered = _filter_by_group(shutters, group_name, use_group_up=True)
        # Rollläden weglassen, die in dieser Phase schon automatisch hochgefahren wurden.
        filtered = [s for s in filtered if (s.get(CONF_COVER_ENTITY_ID) or "") not in covers_driven_up]
        if not filtered:
            return
        hass.async_create_task(
            drive_shutters(filtered, 100, f"Schedule up ({group_name})", apply_lock_protection=False, group=group_name)
        )
        hass.async_create_task(run_group_light_action(hass, entry, group_name, "up"))

    def _run_down(group_name: str) -> None:
        if not _is_auto_enabled(hass, opts, group_name):
            return
        filtered = _filter_by_group(shutters, group_name, use_group_up=False)
        # Rollläden weglassen, die in dieser Phase schon automatisch runtergefahren wurden.
        filtered = [s for s in filtered if (s.get(CONF_COVER_ENTITY_ID) or "") not in covers_driven_down]
        if not filtered:
            return
        hass.async_create_task(
            drive_shutters(
                filtered, 0, f"Schedule down ({group_name})",
                apply_lock_protection=True, group=group_name
            )
        )
        hass.async_create_task(run_group_light_action(hass, entry, group_name, "down"))

    # Fixed-time schedule: run every minute, fire only once per event per day
    fired_today = data.setdefault("_scheduler_fired", {})

    @callback
    def _scheduler_tick(now: datetime) -> None:
        today = now.date()
        is_we = _is_weekend(now)
        for group_name in [GROUP_LIVING, GROUP_SLEEP, GROUP_CHILDREN]:
            sched = _get_group_schedule(opts, group_name)
            if not sched:
                continue
            up_min = sched["we_up_min"] if is_we else sched["w_up_min"]
            up_max = sched["we_up_max"] if is_we else sched["w_up_max"]
            down_t = sched["we_down"] if is_we else sched["w_down"]
            t = now.time()

            if sched["type_up"] == TIME_TYPE_FIXED and up_min <= t <= up_max:
                if _brightness_blocks_scheduler_up(hass, opts, now):
                    continue
                key_up = f"up_{group_name}"
                if fired_today.get(key_up) != today:
                    fired_today[key_up] = today
                    _run_up(group_name)
            if sched["type_down"] == TIME_TYPE_FIXED and t >= down_t:
                key_down = f"down_{group_name}"
                if fired_today.get(key_down) != today:
                    fired_today[key_down] = today
                    _run_down(group_name)

    u1 = async_track_time_change(
        hass, _scheduler_tick, hour="*", minute="*", second=0
    )
    if u1:
        data["_scheduler_unsubs"].append(u1)

    # Sunrise/Sunset: use HA's built-in trackers
    def _make_sunrise_cb(g):
        @callback
        def _cb(event_time):
            if _brightness_blocks_scheduler_up(hass, opts, datetime.now()):
                return
            if _is_auto_enabled(hass, opts, g):
                _run_up(g)
        return _cb

    def _make_sunset_cb(g):
        @callback
        def _cb(event_time):
            if _is_auto_enabled(hass, opts, g):
                _run_down(g)
        return _cb

    for group_name in [GROUP_LIVING, GROUP_SLEEP, GROUP_CHILDREN]:
        sched = _get_group_schedule(opts, group_name)
        if not sched:
            continue
        off_up = sched.get("sunrise_offset", 0) or 0
        off_down = sched.get("sunset_offset", 0) or 0
        offset_up = timedelta(minutes=int(off_up))
        offset_down = timedelta(minutes=int(off_down))
        if sched["type_up"] == TIME_TYPE_SUNRISE:
            unsub_up = async_track_sunrise(hass, _make_sunrise_cb(group_name), offset=offset_up)
            if unsub_up:
                data["_scheduler_unsubs"].append(unsub_up)
        if sched["type_down"] == TIME_TYPE_SUNSET:
            unsub_down = async_track_sunset(hass, _make_sunset_cb(group_name), offset=offset_down)
            if unsub_down:
                data["_scheduler_unsubs"].append(unsub_down)

    _LOGGER.info("Scheduler: %d Rollläden, Verzögerung=%ds", len(shutters), drive_delay)
