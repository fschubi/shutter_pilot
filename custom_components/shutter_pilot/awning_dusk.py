"""Dusk retract for awnings: drive in once, never back out on its own.

Asked for in the forum (bjoerg): an awning should come in when it gets dark
in the evening, without an automatic re-extend the next day - especially
while nobody is home. The existing shading system was the wrong tool for
this: it drives on the *same* kind of condition and would extend the awning
again the moment the condition holds once more, which is exactly the part
that was not wanted.

This module only ever drives inward. Extending an awning back out remains
shading's job, if an area has it enabled, or a manual action - never this
one's. Independent of `sun_protect_enabled`: shading and dusk retract answer
two different questions ("is there sun to block" vs. "is it dark now"), and
an awning can have either, both, or neither.

Deliberately its own condition slot rather than a fourth awning-guard slot
next to wind/rain/ice: the guard ignores every automation switch by design,
because a storm must not care whether someone switched the awning off. A
comfort feature like this one should not carry that same exemption - it
respects the master switch, the area automation and the awning's own switch,
exactly like shading and ventilation do.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    AWNING_DUSK_SLOT,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_SHUTTERS,
    DOMAIN,
    sun_condition_keys,
)
from .helpers import (
    awning_dusk_condition_met,
    get_position_for_role,
    get_tilt_for_role,
    is_auto_enabled,
    is_awning,
    is_shutter_automation_enabled,
    is_system_enabled,
    register_minute_callback,
    rest_role,
    set_cover_position,
)

_LOGGER = logging.getLogger(__name__)


async def setup_awning_dusk(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Watch every awning's own dusk condition, if it has one configured."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []
    areas_by_id = {
        str(a.get(CONF_AREA_ID) or "").strip(): a
        for a in areas
        if isinstance(a, dict)
    }

    entity_key = sun_condition_keys(AWNING_DUSK_SLOT)[0]
    awnings = [
        s
        for s in shutters
        if isinstance(s, dict)
        and is_awning(s)
        and str(s.get(entity_key) or "").strip()
    ]
    if not awnings:
        register_minute_callback(data, "awning_dusk", None)
        return

    # Which covers are already resting because of this condition - so a long
    # dark evening drives the motor once, not every minute, and so a cleared
    # condition (dawn) is the only thing that lets it fire again next dusk.
    retracted: set[str] = data.setdefault("_dusk_retracted", set())

    async def _evaluate() -> None:
        if not is_system_enabled(hass, entry):
            return
        for shutter in awnings:
            cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
            if not cover:
                continue
            if not is_shutter_automation_enabled(hass, entry, shutter):
                continue
            area_id = str(shutter.get(CONF_AREA_DOWN_ID) or "").strip()
            area = areas_by_id.get(area_id)
            if area is not None and not is_auto_enabled(hass, entry, area):
                continue

            met = awning_dusk_condition_met(hass, shutter, data)
            if not met:
                # Bright again - ready to fire on the next dusk. Extending
                # back out is never this module's job, so there is nothing
                # to drive here.
                retracted.discard(cover)
                continue
            if cover in retracted:
                continue

            role = rest_role(shutter)
            pos = get_position_for_role(shutter, role)
            tilt = get_tilt_for_role(shutter, role)
            _LOGGER.info(
                "[awning-dusk] %s: condition met -> retract to %d%%",
                cover, int(pos),
            )
            ok = await set_cover_position(
                hass,
                entry,
                cover,
                pos,
                "Dusk retract",
                tilt_position=tilt,
                area_id=area_id or None,
            )
            if ok:
                retracted.add(cover)

    def _tick(_now: Any) -> None:
        hass.async_create_task(_evaluate())

    register_minute_callback(data, "awning_dusk", _tick)
    hass.async_create_task(_evaluate())
    _LOGGER.info(
        "Awning dusk retract: %d awning(s) configured (minute tick)", len(awnings)
    )
