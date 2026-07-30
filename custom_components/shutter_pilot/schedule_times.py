"""Shared schedule maths: weekday detection, random jitter, trigger times.

This module is deliberately free of side effects so the trickier parts of the
scheduling logic can be unit-tested without a running Home Assistant.
"""

from __future__ import annotations

import logging
import random
from datetime import date, datetime, time, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    AREA_MODE_BRIGHTNESS,
    AREA_MODE_SUN,
    AREA_MODE_TIME,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_RANDOM_OFFSET,
    CONF_AREA_SUNRISE_OFFSET,
    CONF_AREA_SUNSET_OFFSET,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_TIME_WE_DOWN,
    CONF_AREA_TIME_WE_UP,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WORKDAY_SENSOR,
    DEFAULT_AREA_RANDOM_OFFSET,
)

_LOGGER = logging.getLogger(__name__)

DIRECTION_UP = "up"
DIRECTION_DOWN = "down"


def parse_time(tstr: str, fallback: time | None = None) -> time:
    """Parse "HH:MM" into a time object."""
    try:
        parts = str(tstr or "").strip().split(":")
        if len(parts) >= 2:
            hour, minute = int(parts[0]), int(parts[1])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)
    except (ValueError, IndexError):
        pass
    return fallback if fallback is not None else time(6, 0)


def is_weekend_schedule(hass: HomeAssistant | None, area: dict, now: datetime) -> bool:
    """True if the weekend schedule applies.

    When a workday sensor is configured it wins over the calendar: "off" means
    no workday, so the weekend schedule is used. This covers public holidays,
    vacation and shift work. If the sensor is missing or unavailable we fall
    back to Saturday/Sunday.
    """
    sensor_id = str(area.get(CONF_AREA_WORKDAY_SENSOR) or "").strip()
    if sensor_id and hass is not None:
        state = hass.states.get(sensor_id)
        if state is not None and state.state not in ("unknown", "unavailable"):
            return str(state.state).lower() not in ("on", "true", "1")
        _LOGGER.debug(
            "Workday sensor %s unavailable – falling back to calendar weekend",
            sensor_id,
        )
    return now.weekday() >= 5


def get_random_offset(area: dict, day: date, direction: str) -> int:
    """Return the presence-simulation jitter in minutes for one day.

    Deterministic per (area, day, direction) so the scheduler and the "next
    action" sensor always agree, and so the value does not change while the
    minute ticker re-evaluates.
    """
    try:
        span = int(area.get(CONF_AREA_RANDOM_OFFSET, DEFAULT_AREA_RANDOM_OFFSET) or 0)
    except (TypeError, ValueError):
        return 0
    if span <= 0:
        return 0
    span = min(abs(span), 120)
    area_id = str(area.get(CONF_AREA_ID) or "")
    rng = random.Random(f"{area_id}|{day.isoformat()}|{direction}")
    return rng.randint(-span, span)


def infer_today_sun_time(
    next_event: datetime | None, now: datetime
) -> datetime | None:
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


def get_time_mode_triggers(
    hass: HomeAssistant | None, area: dict, now: datetime
) -> tuple[time, time]:
    """Return (up, down) times for a time-mode area, jitter included."""
    if is_weekend_schedule(hass, area, now):
        up_raw = area.get(CONF_AREA_TIME_WE_UP) or area.get(CONF_AREA_TIME_UP, "07:00")
        down_raw = area.get(CONF_AREA_TIME_WE_DOWN) or area.get(CONF_AREA_TIME_DOWN, "19:00")
    else:
        up_raw = area.get(CONF_AREA_TIME_UP, "07:00")
        down_raw = area.get(CONF_AREA_TIME_DOWN, "19:00")

    up_t = parse_time(up_raw, time(7, 0))
    down_t = parse_time(down_raw, time(19, 0))

    day = now.date()
    up_t = _shift_time(up_t, get_random_offset(area, day, DIRECTION_UP))
    down_t = _shift_time(down_t, get_random_offset(area, day, DIRECTION_DOWN))
    return up_t, down_t


def _shift_time(base: time, minutes: int) -> time:
    """Shift a time by minutes, clamped inside the same day."""
    if not minutes:
        return base
    total = base.hour * 60 + base.minute + minutes
    total = max(0, min(24 * 60 - 1, total))
    return time(total // 60, total % 60)


def get_sun_mode_triggers(
    hass: HomeAssistant, area: dict, now: datetime
) -> tuple[datetime | None, datetime | None]:
    """Return (up, down) datetimes for a sun-mode area, jitter included."""
    sun_state = hass.states.get("sun.sun")
    if not sun_state:
        return None, None
    attrs = sun_state.attributes or {}
    next_rising = dt_util.parse_datetime(attrs.get("next_rising"))
    next_setting = dt_util.parse_datetime(attrs.get("next_setting"))
    now_local = dt_util.as_local(now)
    today_sr = infer_today_sun_time(next_rising, now_local)
    today_ss = infer_today_sun_time(next_setting, now_local)
    if today_sr is None or today_ss is None:
        return None, None

    try:
        off_up = int(area.get(CONF_AREA_SUNRISE_OFFSET, 0) or 0)
        off_down = int(area.get(CONF_AREA_SUNSET_OFFSET, 0) or 0)
    except (TypeError, ValueError):
        off_up, off_down = 0, 0

    day = now_local.date()
    off_up += get_random_offset(area, day, DIRECTION_UP)
    off_down += get_random_offset(area, day, DIRECTION_DOWN)

    return (
        today_sr + timedelta(minutes=off_up),
        today_ss + timedelta(minutes=off_down),
    )


def get_next_action(
    hass: HomeAssistant, area: dict, now: datetime | None = None
) -> tuple[datetime | None, str | None]:
    """Return (when, direction) of the next scheduled movement for an area.

    For brightness areas the exact moment depends on the lux sensor, so the
    start of the next allowed time window is reported instead.
    """
    now_local = dt_util.as_local(now or dt_util.now())
    mode = str(area.get(CONF_AREA_MODE) or AREA_MODE_TIME)

    if mode == AREA_MODE_SUN:
        up_dt, down_dt = get_sun_mode_triggers(hass, area, now_local)
        candidates = [
            (up_dt, DIRECTION_UP),
            (down_dt, DIRECTION_DOWN),
        ]
        future = [(dt, d) for dt, d in candidates if dt is not None and dt > now_local]
        if future:
            return min(future, key=lambda item: item[0])
        # Everything for today has passed – tomorrow's sunrise is the next one.
        if up_dt is not None:
            return up_dt + timedelta(days=1), DIRECTION_UP
        return None, None

    if mode == AREA_MODE_BRIGHTNESS:
        weekend = is_weekend_schedule(hass, area, now_local)
        up_key = CONF_AREA_WE_UP_FROM if weekend else CONF_AREA_W_UP_FROM
        down_key = CONF_AREA_WE_DOWN_FROM if weekend else CONF_AREA_W_DOWN_FROM
        up_t = parse_time(area.get(up_key), time(5, 0))
        down_t = parse_time(area.get(down_key), time(16, 0))
    else:
        up_t, down_t = get_time_mode_triggers(hass, area, now_local)

    return _next_from_times(now_local, up_t, down_t)


def _next_from_times(
    now_local: datetime, up_t: time, down_t: time
) -> tuple[datetime, str]:
    """Pick the next of two daily times, rolling over to tomorrow."""
    today = now_local.date()
    candidates: list[tuple[datetime, str]] = []
    for t, direction in ((up_t, DIRECTION_UP), (down_t, DIRECTION_DOWN)):
        dt_today = datetime.combine(today, t, tzinfo=now_local.tzinfo)
        if dt_today > now_local:
            candidates.append((dt_today, direction))
        else:
            candidates.append((dt_today + timedelta(days=1), direction))
    return min(candidates, key=lambda item: item[0])
