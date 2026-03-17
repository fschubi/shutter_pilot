"""Shutter Pilot - Rollladensteuerung für Home Assistant."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
)
from .window_trigger import setup_window_triggers
from .brightness import setup_brightness_listener
from .scheduler import setup_schedulers
from .elevation import setup_elevation_listener
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Shutter Pilot component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Shutter Pilot from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    shutters = entry.options.get(CONF_SHUTTERS, entry.data.get(CONF_SHUTTERS, []))
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in entry data: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    last_positions: dict[str, float] = {}
    trigger_heights: dict[str, float] = {}
    trigger_actions: dict[str, str] = {}
    brightness_down_state = False

    hass.data[DOMAIN][entry.entry_id] = {
        "shutters": shutters,
        "last_positions": last_positions,
        "trigger_heights": trigger_heights,
        "trigger_actions": trigger_actions,
        "brightness_down": brightness_down_state,
        "drive_after_close_pending": {},
        # Gemeinsame Sperren: Rollladen wurde in dieser Phase schon automatisch hoch/runter gefahren.
        # Verhindert, dass Helligkeit/Scheduler/Elevation manuelle Stellung sofort überschreiben.
        "covers_driven_up": set(),
        "covers_driven_down": set(),
    }

    async def _on_ha_started(_: Any) -> None:
        """Start Shutter Pilot when HA is ready."""
        await setup_window_triggers(hass, entry)
        await setup_brightness_listener(hass, entry)
        await setup_schedulers(hass, entry)
        await setup_elevation_listener(hass, entry)

    if hass.is_running:
        await _on_ha_started(None)
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_setup_services(hass, entry)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _LOGGER.info("Shutter Pilot initialized with %d shutters", len(shutters))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Update cached data
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        data = hass.data[DOMAIN][entry.entry_id]
        shutters = entry.options.get(CONF_SHUTTERS, [])
        if not isinstance(shutters, list):
            _LOGGER.warning(
                "Invalid shutters options type in update listener: %r – resetting to empty list",
                type(shutters),
            )
            shutters = []
        data["shutters"] = shutters
    # Re-setup listeners with new config
    await setup_window_triggers(hass, entry)
    await setup_brightness_listener(hass, entry)
    await setup_schedulers(hass, entry)
    await setup_elevation_listener(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok
