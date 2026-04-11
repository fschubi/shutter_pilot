"""Window trigger logic - React to window open/close for shutters."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
)
from .helpers import get_cover_current_position, set_cover_position
from .window_helper import get_window_state

_LOGGER = logging.getLogger(__name__)

_CLOSED_TOLERANCE_PCT = 8.0


def _is_cover_effectively_closed(shutter: dict, current_position: float) -> bool:
    """True if cover is close enough to its configured closed position."""
    try:
        pos_closed = float(shutter.get(CONF_POSITION_CLOSED, 0))
    except (TypeError, ValueError):
        pos_closed = 0.0
    return current_position <= (pos_closed + _CLOSED_TOLERANCE_PCT)


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
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in window triggers: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
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
    def _on_window_state_change(event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        entity_id = event.data.get("entity_id", "")

        try:
            new_val = new_state.state
        except AttributeError:
            new_val = getattr(new_state, "state", None)

        for shutter in window_to_shutters.get(entity_id, []):
            if not shutter.get(CONF_WINDOW_ENTITY_ID):
                continue

            cover_entity = shutter[CONF_COVER_ENTITY_ID]
            pos_closed = shutter.get(CONF_POSITION_CLOSED, 0)

            # Use window_helper for consistent binary_sensor + sensor support
            window_state = get_window_state(hass, shutter)

            target_pos = _get_target_position_for_window_state(shutter, window_state)

            if window_state in ("open", "tilted") and target_pos is not None:
                # Window open or tilted -> only drive to target if the cover is (nearly) closed.
                # Rationale: During daytime (cover already opened by automation), opening a window/door
                # must NOT force the cover into a "ventilation" position.
                current_pos = get_cover_current_position(hass, cover_entity)
                if current_pos is None:
                    # Fail-safe: if we can't read current position, do nothing.
                    trigger_actions.pop(cover_entity, None)
                    trigger_heights.pop(cover_entity, None)
                    continue
                if not _is_cover_effectively_closed(shutter, current_pos):
                    # Not in "closed" state -> no window-trigger cycle active.
                    # Clear stale cycle markers so a later "closed" event cannot restore/close.
                    trigger_actions.pop(cover_entity, None)
                    trigger_heights.pop(cover_entity, None)
                    continue

                saved = current_pos
                trigger_heights[cover_entity] = saved
                trigger_actions[cover_entity] = "triggered"
                reason = "Window tilted" if window_state == "tilted" else "Window opened"
                hass.async_create_task(
                    set_cover_position(hass, cover_entity, target_pos, reason)
                )
            elif window_state == "closed":
                # Window closed -> restore saved position OR execute drive_after_close
                # Prüfe drive_after_close: war Schließen geplant?
                pending = data.get("drive_after_close_pending", {})
                pending_entry = pending.pop(cover_entity, None)
                if pending_entry is not None:
                    target_pos = pending_entry.get("position", pos_closed)
                    reason = pending_entry.get("reason", "Drive after close")
                    hass.async_create_task(
                        set_cover_position(
                            hass, cover_entity, target_pos, reason
                        )
                    )
                    _LOGGER.info(
                        "Fenster geschlossen – Drive-after-close: %s -> %d%%",
                        cover_entity, int(target_pos),
                    )
                else:
                    # Restore only if this window cycle actually triggered a movement.
                    if trigger_actions.get(cover_entity) == "triggered":
                        restore_pos = trigger_heights.get(cover_entity)
                        if restore_pos is None:
                            restore_pos = last_positions.get(cover_entity, pos_closed)
                        hass.async_create_task(
                            set_cover_position(
                                hass, cover_entity, restore_pos, "Window closed – restore"
                            )
                        )
                    trigger_actions.pop(cover_entity, None)
                    trigger_heights.pop(cover_entity, None)

    for window_id in window_to_shutters:
        unsub = async_track_state_change_event(
            hass, window_id, _on_window_state_change
        )
        if unsub:
            data["_window_unsubs"].append(unsub)
        _LOGGER.debug("Tracking window %s for shutter trigger", window_id)
