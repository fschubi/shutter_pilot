"""Privacy position: a helper entity (bathroom occupied, light on) pulls the
shutter to its own height and slat angle for as long as it says "on".

Asked for by Claus (simon42 #172): the bathroom blind must not open in the
morning while someone is in the room, and the sun protection must not drive
it away from the privacy angle either. So it outranks the opening drive,
shading and ventilation - while the evening close keeps running, or the house
would stand open all night because someone was in the bath at dusk.

When the entity goes off again the shutter returns to where it stood before,
but only if it still stands at the privacy position: a hand move, or the
evening close, in the meantime is a newer decision. A morning opening that was
held back is caught up instead of restoring the night position.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_PRIVACY_ENTITY,
    CONF_SHUTTERS,
    DOMAIN,
    ROLE_OPEN,
    ROLE_PRIVACY,
)
from .helpers import (
    automation_allowed,
    get_tilt_for_role,
    get_tracked_position,
    is_system_enabled,
    only_shutters,
    privacy_active,
    privacy_role,
    register_minute_callback,
    resting_position,
    role_position,
    set_cover_position,
)

_LOGGER = logging.getLogger(__name__)

_AT_PRIVACY_TOLERANCE_PCT = 8.0


def _current_tilt(hass: HomeAssistant, cover: str) -> float | None:
    state = hass.states.get(cover)
    if state is None:
        return None
    try:
        return float((state.attributes or {}).get("current_tilt_position"))
    except (TypeError, ValueError):
        return None


async def setup_privacy(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Listen to every privacy entity and keep the shutters in step with it."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return
    for unsub in data.get("_privacy_unsubs", []):
        unsub()
    data["_privacy_unsubs"] = []

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    watched = [
        s
        for s in only_shutters(shutters)
        if str(s.get(CONF_PRIVACY_ENTITY) or "").strip()
        and str(s.get(CONF_COVER_ENTITY_ID) or "").strip()
    ]
    if not watched:
        register_minute_callback(data, "privacy", None)
        return

    state: dict[str, dict[str, Any]] = data.setdefault("_privacy", {})
    by_entity: dict[str, list[dict]] = {}
    for shutter in watched:
        by_entity.setdefault(str(shutter[CONF_PRIVACY_ENTITY]).strip(), []).append(
            shutter
        )

    def _role(shutter: dict) -> str:
        areas = entry.options.get(CONF_AREAS, [])
        down_id = str(shutter.get(CONF_AREA_DOWN_ID) or "").strip()
        area = next(
            (
                a
                for a in areas
                if isinstance(a, dict) and str(a.get(CONF_AREA_ID) or "").strip() == down_id
            ),
            None,
        ) if isinstance(areas, list) else None
        return privacy_role(hass, shutter, area)

    async def _start(shutter: dict, cover: str) -> None:
        if not (is_system_enabled(hass, entry) and automation_allowed(hass, entry, shutter)):
            return
        role = _role(shutter)
        pos = role_position(shutter, role)
        tilt = get_tilt_for_role(shutter, role)
        state[cover] = {
            "pos": resting_position(hass, data, shutter, cover),
            "tilt": _current_tilt(hass, cover),
            "sent": pos,
            "role": role,
            "at": time.monotonic(),
        }
        _LOGGER.info("%s: privacy on -> %s", cover, "height unchanged" if pos is None else f"{pos:.0f}%")
        await set_cover_position(
            hass, entry, cover, pos, "Privacy", tilt_position=tilt
        )

    async def _switch_role(shutter: dict, cover: str, role: str) -> None:
        """The sun moved in front of (or away from) the window while privacy holds."""
        record = state[cover]
        if not (is_system_enabled(hass, entry) and automation_allowed(hass, entry, shutter)):
            return
        # A hand move since our last privacy drive is a newer decision: leave it.
        if data.get("_hand_moved_at", {}).get(cover, float("-inf")) > record["at"]:
            return
        pos = role_position(shutter, role)
        tilt = get_tilt_for_role(shutter, role)
        record.update(role=role, sent=pos, at=time.monotonic())
        _LOGGER.info("%s: privacy position -> %s", cover, role)
        await set_cover_position(
            hass, entry, cover, pos, "Privacy", tilt_position=tilt
        )

    async def _end(shutter: dict, cover: str) -> None:
        record = state.pop(cover, None)
        missed = cover in data.get("_privacy_missed_up", set())
        data.get("_privacy_missed_up", set()).discard(cover)
        if record is None:
            return
        if not (is_system_enabled(hass, entry) and automation_allowed(hass, entry, shutter)):
            return
        # Newer decisions win: a hand move since the privacy drive, or an
        # evening close that left the privacy position.
        if data.get("_hand_moved_at", {}).get(cover, float("-inf")) > record["at"]:
            return
        sent = record["sent"]
        current = get_tracked_position(hass, shutter, cover)
        if (
            sent is not None
            and current is not None
            and abs(current - sent) > _AT_PRIVACY_TOLERANCE_PCT
        ):
            return
        if missed:
            pos = role_position(shutter, ROLE_OPEN)
            tilt = get_tilt_for_role(shutter, ROLE_OPEN)
            data.setdefault("covers_driven_up", set()).add(cover)
            data.setdefault("covers_driven_down", set()).discard(cover)
            reason = "Privacy end - held opening"
        else:
            pos, tilt = record["pos"], record["tilt"]
            if sent is None:
                pos = None  # the height was never touched
            reason = "Privacy end - restore"
        if pos is None and tilt is None:
            return
        _LOGGER.info("%s: privacy off -> %s", cover, reason)
        await set_cover_position(hass, entry, cover, pos, reason, tilt_position=tilt)

    async def _sync(shutters_to_check: list[dict]) -> None:
        for shutter in shutters_to_check:
            cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
            active = privacy_active(hass, shutter)
            if active and cover not in state:
                await _start(shutter, cover)
            elif not active and cover in state:
                await _end(shutter, cover)
            elif active:
                role = _role(shutter)
                if role != state[cover].get("role", ROLE_PRIVACY):
                    await _switch_role(shutter, cover, role)

    @callback
    def _on_change(event) -> None:
        entity = str(event.data.get("entity_id") or "")
        hass.async_create_task(_sync(by_entity.get(entity, [])))

    for entity in by_entity:
        unsub = async_track_state_change_event(hass, entity, _on_change)
        if unsub:
            data["_privacy_unsubs"].append(unsub)

    @callback
    def _tick(_now) -> None:
        hass.async_create_task(_sync(watched))

    register_minute_callback(data, "privacy", _tick)
    hass.async_create_task(_sync(watched))
