"""Automatic ventilation: drive to the ventilation position on conditions.

Until now ventilating was purely manual – a service and a dashboard button.
This adds the automation branch that was asked for in the forum: name a couple
of entities that all have to hold, and the shutters open that far by themselves.

Ranking, deliberately: the window contact wins over everything (it reacts to
what someone physically did), shading wins over ventilation (heat comes first),
and ventilation only ever touches shutters that are otherwise sitting still.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_VENT_ENABLED,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_SHUTTERS,
    DEFAULT_AREA_DRIVE_DELAY,
    ROLE_VENTILATION,
)
from .helpers import (
    get_tracked_position,
    get_position_for_role,
    get_tilt_for_role,
    is_auto_enabled,
    is_cover_sun_protected,
    is_shutter_automation_enabled,
    register_minute_callback,
    set_cover_position,
    vent_conditions_met,
)
from .window_helper import is_window_open_or_tilted

_LOGGER = logging.getLogger(__name__)


def is_cover_ventilating(data: dict[str, Any], cover_entity_id: str) -> bool:
    """True while automatic ventilation holds this cover."""
    return cover_entity_id in data.get("vent_covers", set())


async def setup_ventilation(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Watch the ventilation conditions of every area that enabled them."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []

    vent_areas = [
        a
        for a in areas
        if isinstance(a, dict) and bool(a.get(CONF_AREA_VENT_ENABLED, False))
    ]
    if not vent_areas:
        register_minute_callback(data, "ventilation", None)
        return

    active: set[str] = data.setdefault("vent_covers", set())
    # Where each cover stood before ventilation started. Same idea as the
    # window trigger's trigger_heights: releasing to "open" would be wrong at
    # night, so the previous position is what we drive back to.
    heights: dict[str, float] = data.setdefault("vent_heights", {})

    def _delay_for(area: dict) -> int:
        try:
            return max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            return DEFAULT_AREA_DRIVE_DELAY

    def _blocked(shutter: dict, cover: str) -> str | None:
        """Reason this shutter is off limits for ventilation right now."""
        if not is_shutter_automation_enabled(hass, entry, shutter):
            return "automation off"
        if is_cover_sun_protected(data, cover):
            return "shading active"
        if data.get("trigger_actions", {}).get(cover) == "triggered":
            return "window contact active"
        if is_window_open_or_tilted(hass, shutter):
            return "window open"
        return None

    async def _drive(area: dict, targets: list[tuple[dict, float]], reason: str) -> None:
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        delay = _delay_for(area)
        for idx, (shutter, pos) in enumerate(targets):
            cover = shutter.get(CONF_COVER_ENTITY_ID)
            tilt = get_tilt_for_role(shutter, ROLE_VENTILATION)
            _LOGGER.info(
                "[ventilation] area=%s: %s (%s) → %s -> %d%%",
                area_id, reason, cover, cover, int(pos),
            )
            if idx > 0 and delay > 0:
                await asyncio.sleep(delay)
            await set_cover_position(
                hass,
                entry,
                cover,
                pos,
                f"Ventilation {reason} (area={area_id})",
                tilt_position=tilt,
                area_id=area_id,
            )

    async def _evaluate() -> None:
        for area in vent_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            wanted = vent_conditions_met(hass, area, data)
            if wanted and not is_auto_enabled(hass, entry, area):
                # Master or area switch is off: do not start, but do keep
                # releasing below so nothing stays stuck part way open.
                wanted = False

            to_open: list[tuple[dict, float]] = []
            to_close: list[tuple[dict, float]] = []

            for shutter in shutters:
                cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
                if not cover:
                    continue
                if str(shutter.get(CONF_AREA_DOWN_ID) or "").strip() != area_id:
                    continue
                running = cover in active

                if wanted:
                    if running:
                        continue
                    blocked = _blocked(shutter, cover)
                    if blocked:
                        _LOGGER.debug(
                            "[ventilation] %s skipped: %s", cover, blocked
                        )
                        continue
                    current = get_tracked_position(hass, shutter, cover)
                    target = get_position_for_role(shutter, ROLE_VENTILATION)
                    if current is None or abs(current - target) < 1:
                        # Nothing to do, but remember it so the release does
                        # not drive somewhere unexpected either.
                        continue
                    heights[cover] = current
                    active.add(cover)
                    to_open.append((shutter, target))
                    continue

                if not running:
                    continue
                active.discard(cover)
                back_to = heights.pop(cover, None)
                if back_to is None:
                    continue
                if not is_shutter_automation_enabled(hass, entry, shutter):
                    continue
                to_close.append((shutter, back_to))

            if to_open:
                await _drive(area, to_open, "on")
            if to_close:
                await _drive(area, to_close, "off")

    def _tick(_now) -> None:
        hass.async_create_task(_evaluate())

    register_minute_callback(data, "ventilation", _tick)
    hass.async_create_task(_evaluate())
    _LOGGER.info("Automatic ventilation: %d areas (minute tick)", len(vent_areas))
