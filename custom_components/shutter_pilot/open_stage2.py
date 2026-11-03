"""Second opening stage: first only the slats, later the whole blind.

Asked for by Claus (simon42 #225): in the morning the hall blind only turns its
slats open (height unchanged, the ordinary opening with "unchanged" ticked) and
from ten o'clock - when somebody is home and the weather is fine - it goes all
the way up. Opt-in per shutter: a time, an optional condition entity and its
own position and angle.

It only completes an opening that really happened: the shutter has to stand in
`covers_driven_up`, so a day on which the morning drive was held back (weekend
lock, privacy, "do not open") never reaches the second stage on its own. Nor
does it overrule a decision: a hand move today, an open window, the shading or
the automation switch each keep it where it is. It fires once a day; the
evening drive clears the bookkeeping it depends on.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COVER_ENTITY_ID,
    CONF_OPEN_STAGE2,
    CONF_OPEN_STAGE2_ENTITY,
    CONF_OPEN_STAGE2_TIME,
    CONF_SHUTTERS,
    DEFAULT_OPEN_STAGE2_TIME,
    DOMAIN,
    ROLE_OPEN_STAGE2,
)
from .helpers import (
    automation_allowed,
    get_tilt_for_role,
    is_cover_sun_protected,
    is_system_enabled,
    only_shutters,
    privacy_active,
    register_minute_callback,
    role_position,
    set_cover_position,
)
from .window_helper import is_window_open_or_tilted

_LOGGER = logging.getLogger(__name__)


def _stage_time(shutter: dict[str, Any]):
    raw = str(shutter.get(CONF_OPEN_STAGE2_TIME) or DEFAULT_OPEN_STAGE2_TIME)
    try:
        return datetime.strptime(raw[:5], "%H:%M").time()
    except ValueError:
        return datetime.strptime(DEFAULT_OPEN_STAGE2_TIME, "%H:%M").time()


def _condition_met(hass: HomeAssistant, shutter: dict[str, Any]) -> bool:
    """The optional condition entity says "on". Unset = no condition.

    Fail closed: a dead sensor leaves the slats-only stage in place, which is
    harmless and can be waited out - the opposite mistake opens the blind fully
    against the owner's wish.
    """
    entity_id = str(shutter.get(CONF_OPEN_STAGE2_ENTITY) or "").strip()
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if state is None:
        return False
    return str(state.state).lower() in ("on", "true", "1", "home", "open")


async def setup_open_stage2(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Watch the shutters that asked for a second opening stage."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return
    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    flagged = [
        s
        for s in only_shutters(shutters)
        if s.get(CONF_OPEN_STAGE2)
        and str(s.get(CONF_COVER_ENTITY_ID) or "").strip()
    ]
    if not flagged:
        register_minute_callback(data, "open_stage2", None)
        return

    done: dict[str, str] = data.setdefault("_open2_done", {})

    def _hand_moved_today(cover: str, now: datetime) -> bool:
        stamp = data.get("_hand_moved_at", {}).get(cover)
        if stamp is None:
            return False
        since_midnight = (
            now - now.replace(hour=0, minute=0, second=0, microsecond=0)
        ).total_seconds()
        return time.monotonic() - stamp < since_midnight

    def _ready(shutter: dict[str, Any], cover: str, now: datetime) -> bool:
        today: date = now.date()
        if done.get(cover) == today.isoformat():
            return False
        if now.time() < _stage_time(shutter):
            return False
        if cover not in data.get("covers_driven_up", set()):
            return False
        if cover in data.get("covers_driven_down", set()):
            return False
        if not (is_system_enabled(hass, entry) and automation_allowed(hass, entry, shutter)):
            return False
        if privacy_active(hass, shutter) or is_window_open_or_tilted(hass, shutter):
            return False
        if is_cover_sun_protected(data, cover):
            return False
        if _hand_moved_today(cover, now):
            return False
        return _condition_met(hass, shutter)

    @callback
    def _tick(_now) -> None:
        local = dt_util.now()
        for shutter in flagged:
            cover = str(shutter[CONF_COVER_ENTITY_ID]).strip()
            if not _ready(shutter, cover, local):
                continue
            done[cover] = local.date().isoformat()
            _LOGGER.info("%s: second opening stage", cover)
            hass.async_create_task(
                set_cover_position(
                    hass,
                    entry,
                    cover,
                    role_position(shutter, ROLE_OPEN_STAGE2),
                    "Opening stage 2",
                    tilt_position=get_tilt_for_role(shutter, ROLE_OPEN_STAGE2),
                )
            )

    register_minute_callback(data, "open_stage2", _tick)
