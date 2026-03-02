"""Shutter Pilot services - open_group, close_group, sun_protect_group."""

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
    CONF_GROUP_UP,
    CONF_GROUP_DOWN,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_POSITION_SUN_PROTECT,
    CONF_DRIVE_DELAY,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
    GROUP_ALL,
)
from .window_helper import get_effective_close_position

_LOGGER = logging.getLogger(__name__)

SERVICE_OPEN_GROUP = "open_group"
SERVICE_CLOSE_GROUP = "close_group"
SERVICE_SUN_PROTECT_GROUP = "sun_protect_group"

SERVICE_SCHEMA = vol.Schema(
    {vol.Required("group"): vol.In([GROUP_LIVING, GROUP_SLEEP, GROUP_CHILDREN, GROUP_ALL])}
)


def _filter_shutters(shutters: list, group: str, use_up: bool) -> list:
    key = CONF_GROUP_UP if use_up else CONF_GROUP_DOWN
    if group == GROUP_ALL:
        return shutters
    return [s for s in shutters if s.get(key) == group]


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
    drive_delay = entry.options.get(CONF_DRIVE_DELAY, 10)

    async def open_group(call) -> None:
        group = call.data["group"]
        shutters = entry.options.get(CONF_SHUTTERS, [])
        shutters = _filter_shutters(shutters, group, use_up=True)
        await _drive_group(
            hass, shutters, 100, "open_group", drive_delay
        )

    async def close_group(call) -> None:
        group = call.data["group"]
        shutters = entry.options.get(CONF_SHUTTERS, [])
        shutters = _filter_shutters(shutters, group, use_up=False)
        await _drive_group(
            hass, shutters, 0, "close_group", drive_delay,
            apply_lock_protection=True,
        )

    async def sun_protect_group(call) -> None:
        group = call.data["group"]
        shutters = entry.options.get(CONF_SHUTTERS, [])
        shutters = _filter_shutters(shutters, group, use_up=False)
        # Use first shutter's sun protect position or default 50
        pos = 50
        if shutters:
            pos = shutters[0].get(CONF_POSITION_SUN_PROTECT, 50)
        await _drive_group(
            hass, shutters, pos, "sun_protect_group", drive_delay,
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
