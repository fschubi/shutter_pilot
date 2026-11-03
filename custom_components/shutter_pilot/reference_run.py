"""Reference run for venetian blinds: up, down, back - once every N days.

Asked for by Claus (simon42 #172). A blind that is driven by counting motor
time drifts over the months until "50 %" is no longer 50 % and the slat angle
no longer matches. Driving to both ends once in a while resets the count.

Opt-in per shutter, at night, and only when nothing else has a claim on the
blind: automation off, locked, storm, privacy, an open window or a window
cycle in progress all skip the run for the day and try again the next minute.
The "ends" are the shutter's own configured open and closed positions - that is
what the owner calls up and down, and a blind with an inverted scale (open 0)
works without a special case. Afterwards it returns to where it stood.
"""

from __future__ import annotations

import asyncio
import calendar
import logging
import time
from datetime import date, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COVER_ENTITY_ID,
    CONF_REFERENCE_RUN,
    CONF_REFERENCE_RUN_DAYS,
    CONF_REFERENCE_RUN_FULL,
    CONF_REFERENCE_RUN_MONTHDAY,
    CONF_REFERENCE_RUN_TIME,
    CONF_REFERENCE_RUN_WEEKDAY,
    CONF_SHUTTERS,
    DEFAULT_REFERENCE_RUN_DAYS,
    DEFAULT_REFERENCE_RUN_TIME,
    DOMAIN,
    MAX_REFERENCE_RUN_DAYS,
    ROLE_CLOSED,
    ROLE_OPEN,
)
from .helpers import (
    automation_allowed,
    get_cover_current_position,
    get_position_for_role,
    get_tilt_for_role,
    is_system_enabled,
    only_shutters,
    privacy_active,
    register_minute_callback,
    resting_position,
    set_cover_position,
)
from .window_helper import is_window_open_or_tilted

_LOGGER = logging.getLogger(__name__)

WAIT_POLL_SEC = 2.0
WAIT_MAX_SEC = 240.0
# A cover that reports no position cannot be waited for; give it a fixed time.
BLIND_WAIT_SEC = 60.0
REACHED_TOLERANCE_PCT = 5.0
STORE_VERSION = 1


def _interval_days(shutter: dict[str, Any]) -> int:
    try:
        days = int(shutter.get(CONF_REFERENCE_RUN_DAYS, DEFAULT_REFERENCE_RUN_DAYS))
    except (TypeError, ValueError):
        return DEFAULT_REFERENCE_RUN_DAYS
    return max(1, min(days, MAX_REFERENCE_RUN_DAYS))


def _weekday(shutter: dict[str, Any]) -> int | None:
    try:
        day = int(shutter.get(CONF_REFERENCE_RUN_WEEKDAY))
    except (TypeError, ValueError):
        return None
    return day if 0 <= day <= 6 else None


def _monthday(shutter: dict[str, Any]) -> int | None:
    try:
        day = int(shutter.get(CONF_REFERENCE_RUN_MONTHDAY))
    except (TypeError, ValueError):
        return None
    return min(day, 31) if day >= 1 else None


def _end_positions(shutter: dict[str, Any]) -> tuple[float, float]:
    """Where the run drives to for "open" and "closed".

    The shutter's own positions by default; with the full-travel hook the real
    end stops. Which end is "open" follows the configured scale, so a blind
    with open 0 / closed 15 still opens towards 0.
    """
    opened = get_position_for_role(shutter, ROLE_OPEN)
    closed = get_position_for_role(shutter, ROLE_CLOSED)
    if not shutter.get(CONF_REFERENCE_RUN_FULL, False):
        return opened, closed
    return (100.0, 0.0) if opened >= closed else (0.0, 100.0)


def _run_time(shutter: dict[str, Any]):
    raw = str(shutter.get(CONF_REFERENCE_RUN_TIME) or DEFAULT_REFERENCE_RUN_TIME)
    try:
        return datetime.strptime(raw[:5], "%H:%M").time()
    except ValueError:
        return datetime.strptime(DEFAULT_REFERENCE_RUN_TIME, "%H:%M").time()


def _current_tilt(hass: HomeAssistant, cover: str) -> float | None:
    state = hass.states.get(cover)
    if state is None:
        return None
    try:
        return float((state.attributes or {}).get("current_tilt_position"))
    except (TypeError, ValueError):
        return None


async def setup_reference_run(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Schedule the reference run for every shutter that asked for it."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return
    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    by_cover = {
        str(s.get(CONF_COVER_ENTITY_ID) or "").strip(): s
        for s in only_shutters(shutters)
        if str(s.get(CONF_COVER_ENTITY_ID) or "").strip()
    }
    data["_reference_run"] = None
    flagged = [s for s in by_cover.values() if s.get(CONF_REFERENCE_RUN, False)]
    if not by_cover:
        register_minute_callback(data, "reference_run", None)
        return

    store = Store(hass, STORE_VERSION, f"{DOMAIN}_reference_run_{entry.entry_id}")
    loaded = await store.async_load() or {}
    last: dict[str, str] = dict(loaded.get("last", {}))
    data["_refrun_last"] = last
    active: set[str] = data.setdefault("_refrun_active", set())

    today = dt_util.now().date()
    changed = False
    for shutter in flagged:
        cover = str(shutter[CONF_COVER_ENTITY_ID]).strip()
        if cover not in last:
            # First sight: the first run comes after one interval, not tonight.
            last[cover] = today.isoformat()
            changed = True
    if changed:
        await store.async_save({"last": last})

    def _blocked(shutter: dict[str, Any], cover: str) -> str | None:
        if not is_system_enabled(hass, entry):
            return "system off"
        if not automation_allowed(hass, entry, shutter):
            return "automation off, locked or storm"
        if privacy_active(hass, shutter):
            return "privacy active"
        if is_window_open_or_tilted(hass, shutter):
            return "window open"
        if data.get("trigger_actions", {}).get(cover) == "triggered":
            return "window contact active"
        if cover in active:
            return "already running"
        return None

    async def _wait(cover: str, target: float) -> None:
        waited = 0.0
        recent = data.setdefault("recent_automation_covers", {})
        if get_cover_current_position(hass, cover) is None:
            # No feedback: keep the tracker from reading the travel as a hand
            # move for as long as it is assumed to take.
            recent[cover] = time.monotonic()
            await asyncio.sleep(BLIND_WAIT_SEC)
            return
        while waited < WAIT_MAX_SEC:
            # The tracker books a position nobody asked for as a hand move; a
            # long travel outlasts its 90 s grace, so keep renewing it.
            recent[cover] = time.monotonic()
            current = get_cover_current_position(hass, cover)
            if current is None or abs(current - target) <= REACHED_TOLERANCE_PCT:
                return
            await asyncio.sleep(WAIT_POLL_SEC)
            waited += WAIT_POLL_SEC

    async def _run(shutter: dict[str, Any], forced: bool = False) -> bool:
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
        reason = _blocked(shutter, cover)
        if reason:
            _LOGGER.info("%s: reference run skipped (%s)", cover, reason)
            return False
        previous = resting_position(hass, data, shutter, cover)
        if previous is None:
            _LOGGER.info("%s: reference run skipped (position unknown)", cover)
            return False
        previous_tilt = _current_tilt(hass, cover)
        active.add(cover)
        try:
            _LOGGER.info("%s: reference run starts%s", cover, " (forced)" if forced else "")
            ends = dict(zip((ROLE_OPEN, ROLE_CLOSED), _end_positions(shutter)))
            for role in (ROLE_OPEN, ROLE_CLOSED):
                position = ends[role]
                await set_cover_position(
                    hass,
                    entry,
                    cover,
                    position,
                    "Reference run",
                    tilt_position=get_tilt_for_role(shutter, role),
                )
                await _wait(cover, position)
            await set_cover_position(
                hass,
                entry,
                cover,
                previous,
                "Reference run - back",
                tilt_position=previous_tilt,
            )
            last[cover] = dt_util.now().date().isoformat()
            await store.async_save({"last": last})
            _LOGGER.info("%s: reference run done", cover)
            return True
        finally:
            active.discard(cover)

    def _due(shutter: dict[str, Any], cover: str, now: datetime) -> bool:
        try:
            last_run = date.fromisoformat(last.get(cover, ""))
        except ValueError:
            return False
        if now.time() < _run_time(shutter):
            return False
        today = now.date()
        monthday = _monthday(shutter)
        if monthday is not None:
            # Once a month on that day (31 = the last day of a short month);
            # the interval does not apply, or "the 1st" would drift whenever a
            # month is shorter than the interval.
            last_day = calendar.monthrange(today.year, today.month)[1]
            return today.day == min(monthday, last_day) and last_run < today
        if (today - last_run).days < _interval_days(shutter):
            return False
        weekday = _weekday(shutter)
        return weekday is None or today.weekday() == weekday

    def _tick(_now: datetime) -> None:
        local = dt_util.now()
        for shutter in flagged:
            cover = str(shutter[CONF_COVER_ENTITY_ID]).strip()
            if cover in active or not _due(shutter, cover, local):
                continue
            if _blocked(shutter, cover):
                continue
            hass.async_create_background_task(
                _run(shutter), f"{DOMAIN}_reference_run_{cover}"
            )

    async def run_now(cover: str) -> bool:
        """Forced run for the service: ignores the interval and the flag."""
        shutter = by_cover.get(cover)
        if shutter is None:
            return False
        return await _run(shutter, forced=True)

    data["_reference_run"] = run_now
    register_minute_callback(data, "reference_run", _tick if flagged else None)
    _LOGGER.info("Reference run: %d shutter(s) scheduled", len(flagged))
