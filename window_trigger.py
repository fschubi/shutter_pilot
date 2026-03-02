"""Window trigger logic - React to window open/close for shutters."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_TRIGGER_MODE,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    TRIGGER_MODE_OFF,
    TRIGGER_MODE_ONLY_UP,
    TRIGGER_MODE_ONLY_DOWN,
    TRIGGER_MODE_UP_DOWN,
)
from .window_helper import get_window_state

_LOGGER = logging.getLogger(__name__)


def _get_target_position_for_window_state(
    shutter: dict, state_str: str
) -> float | None:
    """Return target position for window state. None = restore."""
    if state_str == "closed":
        return None
    if state_str == "tilted":
        tilted = shutter.get(CONF_WINDOW_TILTED_STATE, "none")
        if not tilted or tilted.lower() == "none":
            return shutter.get(CONF_POSITION_WHEN_WINDOW_OPEN, 100)
        return shutter.get(CONF_POSITION_WHEN_WINDOW_TILTED, 50)
    if state_str == "open":
        return shutter.get(CONF_POSITION_WHEN_WINDOW_OPEN, 100)
    return None


async def setup_window_triggers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up state listeners for window entities that trigger shutter changes."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    # Cancel previous listeners
    for unsub in data.get("_window_unsubs", []):
        unsub()
    data["_window_unsubs"] = []

    shutters = entry.options.get(CONF_SHUTTERS, [])
    last_positions = data["last_positions"]
    trigger_heights = data["trigger_heights"]
    trigger_actions = data["trigger_actions"]

    # Collect unique window entity IDs and their associated shutters
    window_to_shutters: dict[str, list[dict]] = {}
    for shutter in shutters:
        window_id = shutter.get(CONF_WINDOW_ENTITY_ID)
        if not window_id or (isinstance(window_id, list) and not window_id):
            continue
        if isinstance(window_id, list):
            window_id = window_id[0]
        if window_id not in window_to_shutters:
            window_to_shutters[window_id] = []
        window_to_shutters[window_id].append(shutter)

    @callback
    def _on_window_state_change(entity_id: str, old_state: Any, new_state: Any) -> None:
        if new_state is None:
            return

        try:
            new_val = new_state.state
        except AttributeError:
            new_val = getattr(new_state, "state", None)

        for shutter in window_to_shutters.get(entity_id, []):
            if not shutter.get(CONF_WINDOW_ENTITY_ID):
                continue

            cover_entity = shutter[CONF_COVER_ENTITY_ID]
            trigger_mode = shutter.get(CONF_TRIGGER_MODE, TRIGGER_MODE_UP_DOWN)
            pos_closed = shutter.get(CONF_POSITION_CLOSED, 0)

            # Use window_helper for consistent binary_sensor + sensor support
            window_state = get_window_state(hass, shutter)

            target_pos = _get_target_position_for_window_state(shutter, window_state)

            if window_state in ("open", "tilted") and target_pos is not None:
                # Window open or tilted -> drive to target (100 or 50)
                if trigger_mode in (TRIGGER_MODE_ONLY_UP, TRIGGER_MODE_UP_DOWN):
                    try:
                        cover_state = hass.states.get(cover_entity)
                        attrs = (cover_state.attributes or {}) if cover_state else {}
                        saved = float(attrs.get("current_position", pos_closed))
                    except (TypeError, ValueError):
                        saved = pos_closed
                    trigger_heights[cover_entity] = saved
                    trigger_actions[cover_entity] = "triggered"
                    reason = "Window tilted" if window_state == "tilted" else "Window opened"
                    hass.async_create_task(
                        _set_cover_position(hass, cover_entity, target_pos, reason)
                    )
            elif window_state == "closed":
                # Window closed -> restore saved position OR execute drive_after_close
                if trigger_mode in (TRIGGER_MODE_ONLY_DOWN, TRIGGER_MODE_UP_DOWN):
                    # Prüfe drive_after_close: war Schließen geplant?
                    pending = data.get("drive_after_close_pending", {})
                    pending_entry = pending.pop(cover_entity, None)
                    if pending_entry is not None:
                        target_pos = pending_entry.get("position", pos_closed)
                        reason = pending_entry.get("reason", "Drive after close")
                        hass.async_create_task(
                            _set_cover_position(
                                hass, cover_entity, target_pos, reason
                            )
                        )
                        _LOGGER.info(
                            "Fenster geschlossen – Drive-after-close: %s -> %d%%",
                            cover_entity, int(target_pos),
                        )
                    else:
                        restore_pos = trigger_heights.get(cover_entity)
                        if restore_pos is None:
                            restore_pos = last_positions.get(cover_entity, pos_closed)
                        hass.async_create_task(
                            _set_cover_position(
                                hass, cover_entity, restore_pos, "Window closed – restore"
                            )
                        )

    for window_id in window_to_shutters:
        unsub = async_track_state_change(
            hass, window_id, _on_window_state_change
        )
        if unsub:
            data["_window_unsubs"].append(unsub)
        _LOGGER.debug("Tracking window %s for shutter trigger", window_id)


async def _set_cover_position(
    hass: HomeAssistant, entity_id: str, position: float, reason: str
) -> None:
    """Set cover position via service call."""
    try:
        await hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )
        _LOGGER.info("%s: Set %s to %d%%", reason, entity_id, int(position))
    except Exception as e:
        _LOGGER.warning("Failed to set %s: %s", entity_id, e)
