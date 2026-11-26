"""Insect guard: once a day briefly all the way up, then back.

Asked for by Claus (simon42 #267). Wasps keep nesting in the boxes of venetian
blinds that stay down for weeks - shaded all summer, or simply never fully
opened. Running the blind up to its real top stop once a day disturbs them
before they start building.

Opt-in per shutter. It runs inside a time window, optionally only from a
minimum outside temperature (that is the wasp season - and it keeps the run out
of the frost, where the top of the box is exactly where a blind can freeze) and
only while a condition entity says "on" (nobody home, so the drive disturbs no
one). It skips the day when the blind went up to the top anyway.

Like the reference run it steps aside for everything that has a claim on the
blind: automation off, a lock, storm, frost lock, privacy, an open window, a
window cycle in progress or the frost opening position. Afterwards it returns
to where it stood, slats included - shading included, which is the case it
was asked for.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COVER_ENTITY_ID,
    CONF_INSECT_GUARD,
    CONF_INSECT_GUARD_ENTITY,
    CONF_INSECT_GUARD_FROM,
    CONF_INSECT_GUARD_TEMP_ENTITY,
    CONF_INSECT_GUARD_TEMP_MIN,
    CONF_INSECT_GUARD_TO,
    CONF_SHUTTERS,
    DEFAULT_INSECT_GUARD_FROM,
    DEFAULT_INSECT_GUARD_TEMP_MIN,
    DEFAULT_INSECT_GUARD_TO,
    DOMAIN,
    ROLE_CLOSED,
    ROLE_OPEN,
)
from .helpers import (
    automation_allowed,
    frost_opening_applies,
    get_cover_current_position,
    get_position_for_role,
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
REACHED_TOLERANCE_PCT = 3.0
STORE_VERSION = 1


def _text(shutter: dict[str, Any], key: str) -> str:
    return str(shutter.get(key) or "").strip()


def _clock(raw: str, fallback: str):
    try:
        return datetime.strptime((raw or fallback)[:5], "%H:%M").time()
    except ValueError:
        return datetime.strptime(fallback, "%H:%M").time()


def in_window(shutter: dict[str, Any], now: datetime) -> bool:
    """Inside the time window; a window over midnight wraps."""
    start = _clock(_text(shutter, CONF_INSECT_GUARD_FROM), DEFAULT_INSECT_GUARD_FROM)
    end = _clock(_text(shutter, CONF_INSECT_GUARD_TO), DEFAULT_INSECT_GUARD_TO)
    t = now.time()
    if start <= end:
        return start <= t < end
    return t >= start or t < end


def top_position(shutter: dict[str, Any]) -> float:
    """The real top stop, on whichever end of the scale "open" lies."""
    opened = get_position_for_role(shutter, ROLE_OPEN)
    closed = get_position_for_role(shutter, ROLE_CLOSED)
    return 100.0 if opened >= closed else 0.0


def warm_enough(hass: HomeAssistant, shutter: dict[str, Any]) -> bool:
    """Unset sensor = no temperature criterion; dead sensor = no."""
    entity_id = _text(shutter, CONF_INSECT_GUARD_TEMP_ENTITY)
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    try:
        value = float(state.state) if state is not None else None
    except (TypeError, ValueError):
        value = None
    if value is None:
        return False
    try:
        minimum = float(shutter.get(CONF_INSECT_GUARD_TEMP_MIN, DEFAULT_INSECT_GUARD_TEMP_MIN))
    except (TypeError, ValueError):
        minimum = float(DEFAULT_INSECT_GUARD_TEMP_MIN)
    return value >= minimum


def condition_met(hass: HomeAssistant, shutter: dict[str, Any]) -> bool:
    """Unset = yes, dead sensor = no - waiting a day is harmless."""
    entity_id = _text(shutter, CONF_INSECT_GUARD_ENTITY)
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if state is None:
        return False
    return str(state.state).lower() in ("on", "true", "1", "home", "open")


def _current_tilt(hass: HomeAssistant, cover: str) -> float | None:
    state = hass.states.get(cover)
    if state is None:
        return None
    try:
        return float((state.attributes or {}).get("current_tilt_position"))
    except (TypeError, ValueError):
        return None


async def setup_insect_guard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Watch the shutters that asked for the daily insect run."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return
    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    flagged = [
        s
        for s in only_shutters(shutters)
        if s.get(CONF_INSECT_GUARD) and _text(s, CONF_COVER_ENTITY_ID)
    ]
    if not flagged:
        register_minute_callback(data, "insect_guard", None)
        return

    # Persisted, so a restart at noon does not send the blind up a second time.
    store = Store(hass, STORE_VERSION, f"{DOMAIN}_insect_guard_{entry.entry_id}")
    loaded = await store.async_load() or {}
    last: dict[str, str] = dict(loaded.get("last", {}))
    data["_insect_last"] = last
    active: set[str] = data.setdefault("_insect_active", set())

    def _blocked(shutter: dict[str, Any], cover: str) -> str | None:
        if not is_system_enabled(hass, entry):
            return "system off"
        if not automation_allowed(hass, entry, shutter):
            return "automation off, locked, storm or frost"
        if privacy_active(hass, shutter):
            return "privacy active"
        if is_window_open_or_tilted(hass, shutter):
            return "window open"
        if data.get("trigger_actions", {}).get(cover) == "triggered":
            return "window contact active"
        if frost_opening_applies(hass, entry, shutter, data):
            return "frost opening position"
        return None

    async def _wait(cover: str, target: float) -> None:
        waited = 0.0
        recent = data.setdefault("recent_automation_covers", {})
        if get_cover_current_position(hass, cover) is None:
            recent[cover] = time.monotonic()
            await asyncio.sleep(BLIND_WAIT_SEC)
            return
        while waited < WAIT_MAX_SEC:
            # A long travel outlasts the tracker's grace for our own drives.
            recent[cover] = time.monotonic()
            current = get_cover_current_position(hass, cover)
            if current is None or abs(current - target) <= REACHED_TOLERANCE_PCT:
                return
            await asyncio.sleep(WAIT_POLL_SEC)
            waited += WAIT_POLL_SEC

    async def _save(cover: str, today: str) -> None:
        last[cover] = today
        await store.async_save({"last": last})

    async def _run(shutter: dict[str, Any], cover: str, today: str) -> None:
        try:
            top = top_position(shutter)
            previous = resting_position(hass, data, shutter, cover)
            if previous is not None and abs(previous - top) <= REACHED_TOLERANCE_PCT:
                # Already at the top: the box saw daylight today, nothing to do.
                await _save(cover, today)
                return
            if previous is None:
                # Without a position there is nothing to return to. Booked as
                # done, or it would try - and log - every minute until evening.
                _LOGGER.info("%s: insect guard skipped (position unknown)", cover)
                await _save(cover, today)
                return
            previous_tilt = _current_tilt(hass, cover)
            _LOGGER.info("%s: insect guard - up to %d %%", cover, int(top))
            await _save(cover, today)
            await set_cover_position(hass, entry, cover, top, "Insect guard")
            await _wait(cover, top)
            await set_cover_position(
                hass,
                entry,
                cover,
                previous,
                "Insect guard - back",
                tilt_position=previous_tilt,
            )
            _LOGGER.info("%s: insect guard done", cover)
        finally:
            active.discard(cover)

    def _tick(_now: datetime) -> None:
        local = dt_util.now()
        today = local.date().isoformat()
        for shutter in flagged:
            cover = _text(shutter, CONF_COVER_ENTITY_ID)
            if cover in active or last.get(cover) == today:
                continue
            if not in_window(shutter, local):
                continue
            if not (warm_enough(hass, shutter) and condition_met(hass, shutter)):
                continue
            reason = _blocked(shutter, cover)
            if reason:
                continue
            active.add(cover)
            hass.async_create_background_task(
                _run(shutter, cover, today), f"{DOMAIN}_insect_guard_{cover}"
            )

    register_minute_callback(data, "insect_guard", _tick)
    _LOGGER.info("Insect guard: %d shutter(s)", len(flagged))
