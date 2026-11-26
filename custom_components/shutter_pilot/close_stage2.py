"""Second closing stage: the evening drive first, later a night position.

Asked for by Claus (simon42 #267) as the counterpart of the second opening
stage. In the evening the hall blind closes as configured (height 0, slats 80,
so some light still comes in); once it is really dark outside - five minutes
below 1 lx - it turns its slats to 60. Until now he did that with an extra
automation, which Shutter Pilot then took for a hand move.

Opt-in per shutter. The trigger is any combination of three criteria, all of
which have to hold: a brightness sensor below a threshold for some minutes, an
earliest time of night, a condition entity. With none of them set nothing
happens - the stage would only be a second copy of the evening position.

It only completes an evening drive that really happened and reached the
ordinary closed position: the shutter has to stand in `covers_driven_down`
*and* at `position_closed`. That leaves the mild-evening and the frost position
alone (both stop part way on purpose) and also a drive the lock protection cut
short. Nor does it overrule a decision made since: a hand move after the
evening drive, an open window, privacy, a lock or the automation switch keep
it where it is. Once a night: the next morning's opening clears the marker.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CLOSE_STAGE2,
    CONF_CLOSE_STAGE2_ENTITY,
    CONF_CLOSE_STAGE2_LUX,
    CONF_CLOSE_STAGE2_LUX_ENTITY,
    CONF_CLOSE_STAGE2_MINUTES,
    CONF_CLOSE_STAGE2_TIME,
    CONF_COVER_ENTITY_ID,
    CONF_SHUTTERS,
    DEFAULT_CLOSE_STAGE2_LUX,
    DEFAULT_CLOSE_STAGE2_MINUTES,
    DOMAIN,
    ROLE_CLOSED,
    ROLE_CLOSED_STAGE2,
)
from .helpers import (
    POSITION_TOLERANCE_PCT,
    automation_allowed,
    get_cover_current_position,
    get_tilt_for_role,
    is_system_enabled,
    only_shutters,
    privacy_active,
    register_minute_callback,
    role_position,
    set_cover_position,
)
from .window_helper import is_window_open_or_tilted

_LOGGER = logging.getLogger(__name__)

_NOON = 12 * 60


def _text(shutter: dict[str, Any], key: str) -> str:
    return str(shutter.get(key) or "").strip()


def _number(shutter: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(shutter.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def has_trigger(shutter: dict[str, Any]) -> bool:
    """At least one of brightness, time or condition is set."""
    return bool(
        _text(shutter, CONF_CLOSE_STAGE2_LUX_ENTITY)
        or _text(shutter, CONF_CLOSE_STAGE2_TIME)
        or _text(shutter, CONF_CLOSE_STAGE2_ENTITY)
    )


def _night_minutes(hour: int, minute: int) -> int:
    """Minutes since noon, so that 23:00 comes before 00:30.

    The evening drive happens in the afternoon or evening, the second stage
    after it - possibly past midnight. Counting from noon keeps that order on a
    single axis without a date.
    """
    return (hour * 60 + minute - _NOON) % (24 * 60)


def time_reached(shutter: dict[str, Any], now: datetime) -> bool:
    """The earliest time of night has come. Unset = no time criterion."""
    raw = _text(shutter, CONF_CLOSE_STAGE2_TIME)
    if not raw:
        return True
    try:
        at = datetime.strptime(raw[:5], "%H:%M").time()
    except ValueError:
        # A broken value must not fire the stage at noon.
        return False
    return _night_minutes(now.hour, now.minute) >= _night_minutes(at.hour, at.minute)


def _condition_met(hass: HomeAssistant, shutter: dict[str, Any]) -> bool:
    """Same rule as the opening stage: unset = yes, dead sensor = no."""
    entity_id = _text(shutter, CONF_CLOSE_STAGE2_ENTITY)
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if state is None:
        return False
    return str(state.state).lower() in ("on", "true", "1", "home", "open")


def _lux_dark(hass: HomeAssistant, shutter: dict[str, Any]) -> bool | None:
    """True/False for a readable sensor, None for an unreadable one."""
    entity_id = _text(shutter, CONF_CLOSE_STAGE2_LUX_ENTITY)
    state = hass.states.get(entity_id) if entity_id else None
    if state is None:
        return None
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None
    return value <= _number(shutter, CONF_CLOSE_STAGE2_LUX, DEFAULT_CLOSE_STAGE2_LUX)


def _at_closed_position(hass: HomeAssistant, shutter: dict[str, Any], cover: str) -> bool:
    """The evening drive reached the ordinary closed height.

    "Unchanged" for the closed height, or a cover that reports no position,
    leaves nothing to compare - the bookkeeping alone decides then.
    """
    target = role_position(shutter, ROLE_CLOSED)
    current = get_cover_current_position(hass, cover)
    if target is None or current is None:
        return True
    return abs(current - target) <= POSITION_TOLERANCE_PCT


async def setup_close_stage2(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Watch the shutters that asked for a second closing stage."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return
    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    flagged = [
        s
        for s in only_shutters(shutters)
        if s.get(CONF_CLOSE_STAGE2) and _text(s, CONF_COVER_ENTITY_ID) and has_trigger(s)
    ]
    if not flagged:
        register_minute_callback(data, "close_stage2", None)
        return

    # When the cover was first seen closed, so a hand move *after* the evening
    # drive counts and one from the afternoon does not. Monotonic, like
    # _hand_moved_at, which it is compared with.
    closed_since: dict[str, float] = data.setdefault("_close2_closed_since", {})
    done: set[str] = data.setdefault("_close2_done", set())
    # When the sensor first read dark, as wall-clock time of the tick. Tracked
    # independently of the evening drive: if it is already pitch dark when the
    # blind closes, the second stage follows straight away.
    dark_since: dict[str, datetime] = data.setdefault("_close2_dark_since", {})

    def _dark_long_enough(shutter: dict[str, Any], cover: str, now: datetime) -> bool:
        if not _text(shutter, CONF_CLOSE_STAGE2_LUX_ENTITY):
            return True
        dark = _lux_dark(hass, shutter)
        if not dark:
            # Light again, or a dead sensor: start over. Fail closed - waiting
            # is harmless, turning the slats shut at dusk is not what was asked.
            dark_since.pop(cover, None)
            return False
        since = dark_since.setdefault(cover, now)
        minutes = max(0.0, _number(shutter, CONF_CLOSE_STAGE2_MINUTES, DEFAULT_CLOSE_STAGE2_MINUTES))
        return now - since >= timedelta(minutes=minutes)

    def _ready(shutter: dict[str, Any], cover: str, now: datetime) -> bool:
        # Evaluated first and on every tick: the dark period has to be
        # measured even while the blind is still open.
        dark = _dark_long_enough(shutter, cover, now)
        if cover not in data.get("covers_driven_down", set()):
            closed_since.pop(cover, None)
            done.discard(cover)
            return False
        since = closed_since.setdefault(cover, time.monotonic())
        if cover in done or not dark:
            return False
        if not time_reached(shutter, now):
            return False
        if not (is_system_enabled(hass, entry) and automation_allowed(hass, entry, shutter)):
            return False
        if privacy_active(hass, shutter) or is_window_open_or_tilted(hass, shutter):
            return False
        if data.get("_hand_moved_at", {}).get(cover, float("-inf")) > since:
            return False
        if not _at_closed_position(hass, shutter, cover):
            return False
        return _condition_met(hass, shutter)

    @callback
    def _tick(_now) -> None:
        local = dt_util.now()
        for shutter in flagged:
            cover = _text(shutter, CONF_COVER_ENTITY_ID)
            if not _ready(shutter, cover, local):
                continue
            done.add(cover)
            _LOGGER.info("%s: second closing stage", cover)
            hass.async_create_task(
                set_cover_position(
                    hass,
                    entry,
                    cover,
                    role_position(shutter, ROLE_CLOSED_STAGE2),
                    "Closing stage 2",
                    tilt_position=get_tilt_for_role(shutter, ROLE_CLOSED_STAGE2),
                )
            )

    register_minute_callback(data, "close_stage2", _tick)
