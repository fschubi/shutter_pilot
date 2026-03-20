"""Shutter Pilot - Rollladensteuerung für Home Assistant."""

from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREA_MODE,
    CONF_AREA_AUTO_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_UP_ID,
    CONF_AREA_DOWN_ID,
    CONF_NAME,
)
from .window_trigger import setup_window_triggers
from .brightness import setup_brightness_listener
from .scheduler import setup_schedulers
from .elevation import setup_elevation_listener
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PANEL_URL = "/shutter_pilot_panel"
PANEL_ICON = "mdi:window-shutter-settings"
PANEL_TITLE = "Shutter Pilot"

PLATFORMS: list[Platform] = [Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Shutter Pilot component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Shutter Pilot from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Shutter Pilot loaded from %s", __file__)

    shutters = entry.options.get(CONF_SHUTTERS, entry.data.get(CONF_SHUTTERS, []))
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in entry data: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []

    # Helpful visibility for debugging persisting "areas" across restarts.
    # If your newly created "laydown" area is missing here, the options update
    # is still not persisting correctly.
    areas = entry.options.get(CONF_AREAS, [])
    area_ids: list[str] = []
    if isinstance(areas, list):
        for a in areas:
            if not isinstance(a, dict):
                continue
            aid = str(a.get(CONF_AREA_ID) or "").strip()
            if aid:
                area_ids.append(aid)
    else:
        _LOGGER.warning(
            "Invalid areas options type in entry: %r – treating as empty list",
            type(areas),
        )
        area_ids = []

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

    # Register sidebar panel (only once)
    await _async_register_panel(hass)

    # Register WebSocket commands (only once)
    _async_register_websocket(hass)

    _LOGGER.info(
        "Shutter Pilot initialized with %d shutters; areas=%s",
        len(shutters),
        area_ids,
    )
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Update cached data only; do not reload entry here.
    # Reloading from inside update listener can race with options persistence and
    # roll back fresh changes.
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


# ---------------------------------------------------------------------------
#  Sidebar Panel
# ---------------------------------------------------------------------------

async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the Shutter Pilot sidebar panel (idempotent)."""
    if hass.data.get(f"{DOMAIN}_panel_registered"):
        return
    hass.data[f"{DOMAIN}_panel_registered"] = True

    panel_dir = os.path.join(os.path.dirname(__file__), "frontend")
    panel_file = os.path.join(panel_dir, "shutter-pilot-panel.js")

    hass.http.register_static_path(PANEL_URL, panel_file, cache_headers=False)

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path="shutter-pilot",
        require_admin=False,
        config={"_panel_custom": {
            "name": "shutter-pilot-panel",
            "embed_iframe": False,
            "trust_external": False,
            "js_url": PANEL_URL,
        }},
    )
    _LOGGER.debug("Shutter Pilot sidebar panel registered")


# ---------------------------------------------------------------------------
#  WebSocket API
# ---------------------------------------------------------------------------

def _async_register_websocket(hass: HomeAssistant) -> None:
    """Register WebSocket commands for the panel (idempotent)."""
    if hass.data.get(f"{DOMAIN}_ws_registered"):
        return
    hass.data[f"{DOMAIN}_ws_registered"] = True

    websocket_api.async_register_command(hass, _ws_get_status)
    websocket_api.async_register_command(hass, _ws_set_auto_mode)
    _LOGGER.debug("Shutter Pilot WebSocket commands registered")


def _find_entry_data(hass: HomeAssistant) -> tuple:
    """Find the first Shutter Pilot config entry and its runtime data."""
    domain_data = hass.data.get(DOMAIN, {})
    for entry_id, data in domain_data.items():
        if isinstance(data, dict) and "shutters" in data:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry:
                return entry, data
    return None, None


@websocket_api.websocket_command({vol.Required("type"): "shutter_pilot/get_status"})
@callback
def _ws_get_status(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Return current areas, shutters, and auto-mode states."""
    entry, data = _find_entry_data(hass)
    if not entry or not data:
        connection.send_result(msg["id"], {"areas": [], "shutters": [], "auto_modes": {}})
        return

    raw_areas = entry.options.get(CONF_AREAS, [])
    areas_out = []
    if isinstance(raw_areas, list):
        for a in raw_areas:
            if not isinstance(a, dict):
                continue
            areas_out.append({
                "id": str(a.get(CONF_AREA_ID) or ""),
                "name": str(a.get(CONF_AREA_NAME) or ""),
                "mode": str(a.get(CONF_AREA_MODE) or "time"),
            })

    raw_shutters = entry.options.get(CONF_SHUTTERS, [])
    shutters_out = []
    if isinstance(raw_shutters, list):
        for s in raw_shutters:
            if not isinstance(s, dict):
                continue
            shutters_out.append({
                "cover_entity_id": str(s.get(CONF_COVER_ENTITY_ID) or ""),
                "name": str(s.get(CONF_NAME) or ""),
                "area_up_id": str(s.get(CONF_AREA_UP_ID) or ""),
                "area_down_id": str(s.get(CONF_AREA_DOWN_ID) or ""),
            })

    auto_modes = data.get("auto_modes", {})

    connection.send_result(msg["id"], {
        "areas": areas_out,
        "shutters": shutters_out,
        "auto_modes": dict(auto_modes) if isinstance(auto_modes, dict) else {},
    })


@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/set_auto_mode",
    vol.Required("area_id"): str,
    vol.Required("enabled"): bool,
})
@callback
def _ws_set_auto_mode(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Toggle auto-mode for an area via its switch entity."""
    area_id = msg["area_id"]
    enabled = msg["enabled"]

    entry, data = _find_entry_data(hass)
    if not data:
        connection.send_error(msg["id"], "not_found", "No Shutter Pilot entry found")
        return

    auto_modes = data.setdefault("auto_modes", {})
    auto_modes[area_id] = enabled

    # Also toggle the actual switch entity if it exists
    raw_areas = entry.options.get(CONF_AREAS, []) if entry else []
    for a in raw_areas:
        if not isinstance(a, dict):
            continue
        if str(a.get(CONF_AREA_ID) or "") != area_id:
            continue
        entity_id = str(a.get(CONF_AREA_AUTO_ENTITY_ID) or "").strip()
        if entity_id:
            service = "turn_on" if enabled else "turn_off"
            hass.async_create_task(
                hass.services.async_call("switch", service, {"entity_id": entity_id})
            )
        break

    connection.send_result(msg["id"], {"ok": True})
