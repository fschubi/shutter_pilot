"""Shutter Pilot services - open_group, close_group, sun_protect_group (area-based)."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_UP_ID,
    CONF_AREA_DOWN_ID,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_POSITION_SUN_PROTECT,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
)
from .window_helper import get_effective_close_position

_LOGGER = logging.getLogger(__name__)

SERVICE_OPEN_GROUP = "open_group"
SERVICE_CLOSE_GROUP = "close_group"
SERVICE_SUN_PROTECT_GROUP = "sun_protect_group"

SERVICE_SCHEMA = vol.Schema(
    {vol.Required("area_id"): str}
)


def _filter_shutters(shutters: list, area_id: str, use_up: bool) -> list:
    key = CONF_AREA_UP_ID if use_up else CONF_AREA_DOWN_ID
    return [s for s in shutters if str(s.get(key) or "").strip() == area_id]


async def _drive_group(
    hass: HomeAssistant,
    shutters: list,
    position: float,
    direction: str,
    delay: int,
    apply_lock_protection: bool = False,
) -> None:
    for shutter in shutters:
        cover = shutter.get(CONF_COVER_ENTITY_ID)
        if not cover:
            continue
        eff_pos = position
        if apply_lock_protection:
            eff_pos = get_effective_close_position(hass, shutter, position)
        try:
            await hass.services.async_call(
                "cover",
                "set_cover_position",
                {"entity_id": cover, "position": eff_pos},
                blocking=True,
            )
            if eff_pos != position:
                _LOGGER.info("%s: %s -> %d%% (Aussperrschutz: Tür offen)", direction, cover, int(eff_pos))
            else:
                _LOGGER.info("%s: %s -> %d%%", direction, cover, int(eff_pos))
        except Exception as e:
            _LOGGER.warning("Failed %s %s: %s", direction, cover, e)
        await asyncio.sleep(delay)


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register Shutter Pilot services."""
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []

    def _delay_for_area(area_id: str) -> int:
        for a in areas:
            if not isinstance(a, dict):
                continue
            if str(a.get(CONF_AREA_ID) or "").strip() != area_id:
                continue
            try:
                return max(0, int(a.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
            except (TypeError, ValueError):
                return DEFAULT_AREA_DRIVE_DELAY
        return DEFAULT_AREA_DRIVE_DELAY

    async def open_group(call) -> None:
        area_id = str(call.data.get("area_id") or "").strip()
        if not area_id:
            return
        shutters = entry.options.get(CONF_SHUTTERS, [])
        if not isinstance(shutters, list):
            _LOGGER.warning(
                "Invalid shutters options type in open_group service: %r – resetting to empty list",
                type(shutters),
            )
            shutters = []
        shutters = _filter_shutters(shutters, area_id, use_up=True)
        await _drive_group(
            hass, shutters, 100, f"open_group({area_id})", _delay_for_area(area_id)
        )

    async def close_group(call) -> None:
        area_id = str(call.data.get("area_id") or "").strip()
        if not area_id:
            return
        shutters = entry.options.get(CONF_SHUTTERS, [])
        if not isinstance(shutters, list):
            _LOGGER.warning(
                "Invalid shutters options type in close_group service: %r – resetting to empty list",
                type(shutters),
            )
            shutters = []
        shutters = _filter_shutters(shutters, area_id, use_up=False)
        await _drive_group(
            hass, shutters, 0, f"close_group({area_id})", _delay_for_area(area_id),
            apply_lock_protection=True,
        )

    async def sun_protect_group(call) -> None:
        area_id = str(call.data.get("area_id") or "").strip()
        if not area_id:
            return
        shutters = entry.options.get(CONF_SHUTTERS, [])
        if not isinstance(shutters, list):
            _LOGGER.warning(
                "Invalid shutters options type in sun_protect_group service: %r – resetting to empty list",
                type(shutters),
            )
            shutters = []
        shutters = _filter_shutters(shutters, area_id, use_up=False)
        # Use first shutter's sun protect position or default 50
        pos = 50
        if shutters:
            pos = shutters[0].get(CONF_POSITION_SUN_PROTECT, 50)
        await _drive_group(
            hass, shutters, pos, f"sun_protect_group({area_id})", _delay_for_area(area_id),
            apply_lock_protection=True,
        )

    def _unregister() -> None:
        hass.services.async_remove(DOMAIN, SERVICE_OPEN_GROUP)
        hass.services.async_remove(DOMAIN, SERVICE_CLOSE_GROUP)
        hass.services.async_remove(DOMAIN, SERVICE_SUN_PROTECT_GROUP)
        _LOGGER.debug("Services unregistered")

    hass.services.async_register(
        DOMAIN, SERVICE_OPEN_GROUP, open_group, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLOSE_GROUP, close_group, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SUN_PROTECT_GROUP, sun_protect_group, schema=SERVICE_SCHEMA
    )
    entry.async_on_unload(_unregister)
    _LOGGER.info("Services registered: open_group, close_group, sun_protect_group")
