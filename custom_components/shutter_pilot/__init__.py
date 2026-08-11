"""Shutter Pilot - Rollladensteuerung für Home Assistant."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from copy import deepcopy

from .const import (
    DOMAIN,
    AREA_MODE_SUN,
    CONF_SHUTTERS,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_AUTO_ENTITY_ID,
    CONF_COVER_ENTITY_ID,
    CONF_MASTER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTER_AUTOMATION_ENABLED,
    CONF_SHUTTER_AUTO_ENTITY_ID,
    CONF_VERIFY_AFTER,
    CONF_VERIFY_ENABLED,
    CONF_VERIFY_RETRIES,
    CONF_VERIFY_TOLERANCE,
    CONF_MIN_DRIVE_GAP,
    CONF_WEATHER_ENTITY,
    DEFAULT_MIN_DRIVE_GAP,
    DEFAULT_VERIFY_AFTER,
    DEFAULT_VERIFY_RETRIES,
    DEFAULT_VERIFY_TOLERANCE,
)
from .window_trigger import cancel_all_window_close, setup_window_triggers
from .awning_guard import setup_awning_guard
from .brightness import setup_brightness_listener
from .scheduler import setup_schedulers
from .elevation import setup_elevation_listener
from .ventilation import setup_ventilation
from .cover_verify import cancel_all as cancel_all_verifications
from .weather_data import setup_weather
from .services import async_setup_services
from .cover_tracker import (
    async_restore_positions_on_startup,
    setup_cover_position_tracker,
)
from .position_store import get_position_store
from .schedule_times import get_sun_mode_trigger_details
from .helpers import (
    apply_covers_driven_from_persisted,
    get_sun_protect_status_for_areas,
    restore_drive_after_close,
)

_LOGGER = logging.getLogger(__name__)

PANEL_URL = "/shutter_pilot_panel"


def _read_manifest_version() -> str:
    """Integration version from manifest.json (single source of truth)."""
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
        with open(manifest_path, encoding="utf-8") as f:
            v = json.load(f).get("version")
            return str(v).strip() if v else "0.0.0"
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return "0.0.0"


PANEL_ASSET_VERSION = _read_manifest_version()
PANEL_ICON = "mdi:window-shutter-settings"
PANEL_TITLE = "Shutter Pilot"

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

# Shutter Pilot is set up from the UI only; there is no YAML configuration.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Shutter Pilot component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate an old config entry. Only version 1 exists so far."""
    _LOGGER.debug("Migration check for entry version %s", entry.version)
    return True


@callback
def _setup_minute_ticker(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register one shared per-minute timer for scheduler and sun protection."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data or data.get("_minute_ticker_unsub"):
        return

    @callback
    def _tick(now: Any) -> None:
        for name, cb in list(data.get("_minute_callbacks", {}).items()):
            try:
                cb(now)
            except Exception:  # pragma: no cover - one bad callback must not
                _LOGGER.exception("Minute callback %s failed", name)

    data["_minute_ticker_unsub"] = async_track_time_change(
        hass, _tick, hour="*", minute="*", second=0
    )
    _LOGGER.debug("Shared minute ticker registered")


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
        "pending_automation_covers": set(),
        "recent_automation_covers": {},
        "sun_protect_active": {},
        "master_enabled": True,
        # Jedes Speichern im Panel laedt den Entry neu und baut dieses Dict
        # frisch auf – alle Merker oben stehen danach wieder leer. Ohne den
        # Zeitstempel liest sich das im Export wie ein Fehler, und der erste
        # Bericht dieser Art kam prompt aus dem Forum.
        "_runtime_started": dt_util.utcnow(),
    }

    get_position_store(hass, entry.entry_id)

    async def _on_ha_started(_: Any) -> None:
        """Start Shutter Pilot when HA is ready."""
        store = get_position_store(hass, entry.entry_id)
        await store.async_load()
        apply_covers_driven_from_persisted(hass, entry, shutters, store)
        await restore_drive_after_close(hass, entry, hass.data[DOMAIN][entry.entry_id])
        await setup_cover_position_tracker(hass, entry)
        await setup_window_triggers(hass, entry)
        await setup_brightness_listener(hass, entry)
        await setup_schedulers(hass, entry)
        await setup_elevation_listener(hass, entry)
        # After shading: the guard must already know its verdict when the
        # first shading evaluation asks whether an awning may go out.
        await setup_awning_guard(hass, entry)
        await setup_ventilation(hass, entry)
        await setup_weather(hass, entry)
        _setup_minute_ticker(hass, entry)
        hass.async_create_task(async_restore_positions_on_startup(hass, entry))

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

    store = get_position_store(hass, entry.entry_id)
    await store.async_load()
    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    apply_covers_driven_from_persisted(hass, entry, shutters, store)
    await setup_cover_position_tracker(hass, entry)
    await setup_window_triggers(hass, entry)
    await setup_brightness_listener(hass, entry)
    await setup_schedulers(hass, entry)
    await setup_elevation_listener(hass, entry)
    await setup_awning_guard(hass, entry)
    await setup_ventilation(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        data = hass.data[DOMAIN][entry.entry_id]
        if isinstance(data, dict):
            for key in (
                "_brightness_unsubs",
                "_window_unsubs",
                "_cover_tracker_unsubs",
                "_awning_guard_unsubs",
            ):
                for unsub in data.get(key, []):
                    try:
                        unsub()
                    except Exception:
                        pass
                data[key] = []

            cancel_all_verifications(data)
            cancel_all_window_close(data)

            ticker = data.pop("_minute_ticker_unsub", None)
            if ticker:
                try:
                    ticker()
                except Exception:
                    pass
            data["_minute_callbacks"] = {}
            _LOGGER.debug("Shutter Pilot: all listeners cancelled for unload")

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

    await hass.http.async_register_static_paths(
        [StaticPathConfig(PANEL_URL, panel_file, cache_headers=False)]
    )

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path="shutter-pilot",
        # Das Panel bleibt für alle Benutzer sichtbar: Es ist zugleich die
        # Bedienoberfläche für die Rollläden (hoch, runter, Sonnenschutz,
        # Lüften) und die läuft über die normalen cover-Dienste, für die Home
        # Assistant selbst die Rechte prüft. Konfiguriert werden kann hier
        # nichts ohne Administratorrechte: Jeder ändernde WebSocket-Befehl
        # trägt @websocket_api.require_admin, und das Panel blendet die
        # Konfigurationsbereiche bei Nicht-Administratoren aus.
        require_admin=False,
        config={
            "shutter_pilot_version": PANEL_ASSET_VERSION,
            "_panel_custom": {
                "name": "shutter-pilot-panel",
                "embed_iframe": False,
                "trust_external": False,
                "js_url": f"{PANEL_URL}?v={PANEL_ASSET_VERSION}",
            },
        },
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

    for cmd in (
        _ws_get_status, _ws_set_auto_mode, _ws_set_master_enabled,
        _ws_set_shutter_automation,
        _ws_save_area, _ws_delete_area,
        _ws_save_shutter, _ws_delete_shutter,
        _ws_save_settings, _ws_export_config,
    ):
        websocket_api.async_register_command(hass, cmd)
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


def _update_entry_options(hass: HomeAssistant, entry: ConfigEntry, new_opts: dict) -> None:
    """Persist new options (deep-copied) to the config entry."""
    hass.config_entries.async_update_entry(entry, options=deepcopy(new_opts))


async def _reload_entry_delayed(hass: HomeAssistant, entry_id: str) -> None:
    """Reload the config entry after a short delay to let persistence settle."""
    await asyncio.sleep(0.5)
    await hass.config_entries.async_reload(entry_id)


def _sun_area_triggers(hass: HomeAssistant, areas: list) -> dict:
    """Compute the real drive times for every sun-mode area.

    The panel used to show the raw sunrise, which ignored the clock bounds and
    the presence jitter – it cannot compute either. Areas without a result are
    left out so an older panel simply falls back to its own display.
    """
    triggers: dict[str, dict] = {}
    now = dt_util.now()
    for area in areas:
        if not isinstance(area, dict):
            continue
        if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_SUN:
            continue
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            continue
        try:
            details = get_sun_mode_trigger_details(hass, area, now)
        except Exception:  # pragma: no cover - get_status must never go blank
            _LOGGER.exception("Could not compute sun triggers for area %s", area_id)
            continue
        if details.get("up") is None or details.get("down") is None:
            continue
        triggers[area_id] = {
            "up": details["up"].isoformat(),
            "up_bound": details.get("up_bound"),
            "up_bound_time": details.get("up_bound_time"),
            "up_jitter": details.get("up_jitter", 0),
            "down": details["down"].isoformat(),
            "down_bound": details.get("down_bound"),
            "down_bound_time": details.get("down_bound_time"),
            "down_jitter": details.get("down_jitter", 0),
        }
    return triggers


# -- get_status ---------------------------------------------------------------

@websocket_api.websocket_command({vol.Required("type"): "shutter_pilot/get_status"})
@callback
def _ws_get_status(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Return full areas, shutters, and auto-mode states for the panel."""
    entry, data = _find_entry_data(hass)
    if not entry or not data:
        connection.send_result(
            msg["id"],
            {
                "areas": [],
                "shutters": [],
                "auto_modes": {},
                "master_enabled": True,
                "sun_protect_status": {},
                "settings": {},
                "weather": {},
                "area_triggers": {},
                "version": PANEL_ASSET_VERSION,
            },
        )
        return

    raw_areas = entry.options.get(CONF_AREAS, [])
    areas_out = []
    if isinstance(raw_areas, list):
        for a in raw_areas:
            if isinstance(a, dict):
                areas_out.append(dict(a))

    raw_shutters = entry.options.get(CONF_SHUTTERS, [])
    shutters_out = []
    if isinstance(raw_shutters, list):
        for s in raw_shutters:
            if isinstance(s, dict):
                shutters_out.append(dict(s))

    auto_modes = data.get("auto_modes", {})
    master_enabled = data.get("master_enabled", True)
    sun_protect_status = get_sun_protect_status_for_areas(hass, entry, raw_areas if isinstance(raw_areas, list) else [])

    sun_info = {}
    sun_state = hass.states.get("sun.sun")
    if sun_state:
        sun_attrs = sun_state.attributes or {}
        sun_info = {
            "elevation": sun_attrs.get("elevation"),
            "next_rising": sun_attrs.get("next_rising"),
            "next_setting": sun_attrs.get("next_setting"),
        }

    connection.send_result(msg["id"], {
        "areas": areas_out,
        "shutters": shutters_out,
        "settings": {
            k: entry.options.get(k, d)
            for k, d in (
                (CONF_WEATHER_ENTITY, ""),
                (CONF_VERIFY_ENABLED, False),
                (CONF_VERIFY_AFTER, DEFAULT_VERIFY_AFTER),
                (CONF_VERIFY_TOLERANCE, DEFAULT_VERIFY_TOLERANCE),
                (CONF_VERIFY_RETRIES, DEFAULT_VERIFY_RETRIES),
                (CONF_MIN_DRIVE_GAP, DEFAULT_MIN_DRIVE_GAP),
            )
        },
        "weather": dict(data.get("weather") or {}),
        "auto_modes": dict(auto_modes) if isinstance(auto_modes, dict) else {},
        "master_enabled": bool(master_enabled),
        "sun_protect_status": sun_protect_status,
        "sun": sun_info,
        "area_triggers": _sun_area_triggers(
            hass, raw_areas if isinstance(raw_areas, list) else []
        ),
        "version": PANEL_ASSET_VERSION,
    })


# -- set_master_enabled -------------------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/set_master_enabled",
    vol.Required("enabled"): bool,
})
@callback
def _ws_set_master_enabled(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Toggle global Shutter Pilot master switch."""
    enabled = msg["enabled"]
    entry, data = _find_entry_data(hass)
    if not data:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    data["master_enabled"] = bool(enabled)
    if entry:
        master_id = str(entry.options.get(CONF_MASTER_ENTITY_ID) or "").strip()
        if master_id:
            hass.async_create_task(
                hass.services.async_call(
                    "switch",
                    "turn_on" if enabled else "turn_off",
                    {"entity_id": master_id},
                )
            )
    connection.send_result(msg["id"], {"ok": True})


# -- set_auto_mode ------------------------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/set_auto_mode",
    vol.Required("area_id"): str,
    vol.Required("enabled"): bool,
})
@callback
def _ws_set_auto_mode(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Toggle auto-mode for an area."""
    area_id, enabled = msg["area_id"], msg["enabled"]
    entry, data = _find_entry_data(hass)
    if not data:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    data.setdefault("auto_modes", {})[area_id] = enabled
    raw_areas = entry.options.get(CONF_AREAS, []) if entry else []
    for a in raw_areas:
        if not isinstance(a, dict):
            continue
        if str(a.get(CONF_AREA_ID) or "") != area_id:
            continue
        eid = str(a.get(CONF_AREA_AUTO_ENTITY_ID) or "").strip()
        if eid:
            hass.async_create_task(
                hass.services.async_call("switch", "turn_on" if enabled else "turn_off", {"entity_id": eid})
            )
        break
    connection.send_result(msg["id"], {"ok": True})


# -- set_shutter_automation ---------------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/set_shutter_automation",
    vol.Required("cover_entity_id"): str,
    vol.Required("enabled"): bool,
})
@callback
def _ws_set_shutter_automation(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Toggle automation for a single shutter, straight from the panel."""
    cover, enabled = str(msg["cover_entity_id"]).strip(), msg["enabled"]
    entry, data = _find_entry_data(hass)
    if not data:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    # Laufzeitwert sofort setzen, damit die nächste Auswertung ihn schon sieht,
    # und den Schalter nachziehen – der ist die Anzeige in Home Assistant.
    data.setdefault("shutter_automation", {})[cover] = enabled
    raw_shutters = entry.options.get(CONF_SHUTTERS, []) if entry else []
    for s in raw_shutters:
        if not isinstance(s, dict):
            continue
        if str(s.get(CONF_COVER_ENTITY_ID) or "").strip() != cover:
            continue
        eid = str(s.get(CONF_SHUTTER_AUTO_ENTITY_ID) or "").strip()
        if eid:
            hass.async_create_task(
                hass.services.async_call("switch", "turn_on" if enabled else "turn_off", {"entity_id": eid})
            )
        break
    connection.send_result(msg["id"], {"ok": True})


# -- save_area (create / update) ----------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/save_area",
    vol.Required("area"): dict,
})
@websocket_api.async_response
async def _ws_save_area(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Create or update an area. The 'area' dict must contain at least 'id'."""
    entry, data = _find_entry_data(hass)
    if not entry:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    area_data = msg["area"]
    area_id = str(area_data.get("id") or "").strip()
    if not area_id:
        connection.send_error(msg["id"], "invalid", "area.id is required")
        return
    opts = deepcopy(dict(entry.options or {}))
    areas = opts.setdefault(CONF_AREAS, [])
    idx = next((i for i, a in enumerate(areas) if isinstance(a, dict) and str(a.get(CONF_AREA_ID) or "") == area_id), None)
    if idx is not None:
        areas[idx].update(area_data)
    else:
        areas.append(area_data)
    _update_entry_options(hass, entry, opts)
    hass.async_create_task(_reload_entry_delayed(hass, entry.entry_id))
    connection.send_result(msg["id"], {"ok": True})


# -- delete_area --------------------------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/delete_area",
    vol.Required("area_id"): str,
})
@websocket_api.async_response
async def _ws_delete_area(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Delete an area by id."""
    entry, _ = _find_entry_data(hass)
    if not entry:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    area_id = msg["area_id"]
    opts = deepcopy(dict(entry.options or {}))
    areas = opts.setdefault(CONF_AREAS, [])
    opts[CONF_AREAS] = [a for a in areas if not (isinstance(a, dict) and str(a.get(CONF_AREA_ID) or "") == area_id)]
    _update_entry_options(hass, entry, opts)
    registry = er.async_get(hass)
    uid = f"{entry.entry_id}_auto_area_{area_id}"
    entity_id = registry.async_get_entity_id("switch", DOMAIN, uid)
    if entity_id:
        registry.async_remove(entity_id)
    hass.async_create_task(_reload_entry_delayed(hass, entry.entry_id))
    connection.send_result(msg["id"], {"ok": True})


def _apply_shutter_automation_state(
    hass: HomeAssistant, entry: ConfigEntry, shutter: dict
) -> None:
    """Keep the per-shutter automation switch in step with the saved value.

    The checkbox in the panel writes into the options, the switch entity is
    what the automation actually reads. Without this the two would drift apart
    after a reload, because the switch restores its own last state.
    """
    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
    if not cover:
        return
    enabled = bool(shutter.get(CONF_SHUTTER_AUTOMATION_ENABLED, True))

    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if isinstance(data, dict):
        data.setdefault("shutter_automation", {})[cover] = enabled

    switch_id = str(shutter.get(CONF_SHUTTER_AUTO_ENTITY_ID) or "").strip()
    if not switch_id:
        return
    state = hass.states.get(switch_id)
    if state is not None and (str(state.state).lower() in ("on", "true", "1")) == enabled:
        return
    hass.async_create_task(
        hass.services.async_call(
            "switch",
            "turn_on" if enabled else "turn_off",
            {"entity_id": switch_id},
        )
    )


# -- save_shutter (create / update) -------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/save_shutter",
    vol.Required("shutter"): dict,
    vol.Optional("index"): vol.Any(int, None),
})
@websocket_api.async_response
async def _ws_save_shutter(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Create or update a shutter. Pass index to update, omit to create."""
    entry, _ = _find_entry_data(hass)
    if not entry:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    shutter_data = msg["shutter"]
    idx = msg.get("index")
    opts = deepcopy(dict(entry.options or {}))
    shutters = opts.setdefault(CONF_SHUTTERS, [])

    # Derselbe Rollladen zweimal angelegt, mit verschiedenen Bereichen, faehrt
    # im Minutentakt hin und her: jeder Eintrag entscheidet fuer sich, und die
    # beiden widersprechen sich. Das ist keine Einstellung, die jemand meint –
    # es passiert durch einen Fehlklick, und im Panel sieht man es kaum.
    cover = str(shutter_data.get(CONF_COVER_ENTITY_ID) or "").strip()
    if cover:
        clash = next(
            (
                other
                for i, other in enumerate(shutters)
                if isinstance(other, dict)
                and i != idx
                and str(other.get(CONF_COVER_ENTITY_ID) or "").strip() == cover
            ),
            None,
        )
        if clash is not None:
            connection.send_error(
                msg["id"],
                "duplicate_cover",
                f"{cover} is already configured as "
                f"\"{clash.get(CONF_NAME) or cover}\"",
            )
            return

    if idx is not None and 0 <= idx < len(shutters):
        shutters[idx] = shutter_data
    else:
        shutters.append(shutter_data)
    _update_entry_options(hass, entry, opts)
    _apply_shutter_automation_state(hass, entry, shutter_data)
    hass.async_create_task(_reload_entry_delayed(hass, entry.entry_id))
    connection.send_result(msg["id"], {"ok": True})


# -- save_settings (global options) -------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/save_settings",
    vol.Required("settings"): dict,
})
@websocket_api.async_response
async def _ws_save_settings(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Store global options such as the weather entity."""
    entry, _ = _find_entry_data(hass)
    if not entry:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    opts = deepcopy(dict(entry.options or {}))
    for key, value in msg["settings"].items():
        if key in (CONF_AREAS, CONF_SHUTTERS):
            continue  # areas and shutters have their own commands
        opts[key] = value
    _update_entry_options(hass, entry, opts)
    hass.async_create_task(_reload_entry_delayed(hass, entry.entry_id))
    connection.send_result(msg["id"], {"ok": True})


# -- delete_shutter -----------------------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): "shutter_pilot/delete_shutter",
    vol.Required("index"): int,
})
@websocket_api.async_response
async def _ws_delete_shutter(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Delete a shutter by index."""
    entry, _ = _find_entry_data(hass)
    if not entry:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    idx = msg["index"]
    opts = deepcopy(dict(entry.options or {}))
    shutters = opts.setdefault(CONF_SHUTTERS, [])
    if 0 <= idx < len(shutters):
        shutters.pop(idx)
    _update_entry_options(hass, entry, opts)
    hass.async_create_task(_reload_entry_delayed(hass, entry.entry_id))
    connection.send_result(msg["id"], {"ok": True})


# -- export_config ------------------------------------------------------------

@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "shutter_pilot/export_config"})
@websocket_api.async_response
async def _ws_export_config(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Return every setting plus the shading decision of this moment.

    Admin only, like every other write command here – the report names each
    entity of the installation, which is more than a guest account should get
    handed in one piece.
    """
    entry, _ = _find_entry_data(hass)
    if not entry:
        connection.send_error(msg["id"], "not_found", "No entry found")
        return
    from .export import async_build_export

    connection.send_result(msg["id"], await async_build_export(hass, entry))
