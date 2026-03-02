"""Helper to check window state and apply lock protection (Aussperrschutz)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_POSITION_CLOSED,
)


def _normalize_state(val: Any) -> str:
    if val is None:
        return ""
    return str(val).lower().strip()


def get_window_state(hass: HomeAssistant, shutter: dict) -> str:
    """
    Return: "closed" | "tilted" | "open"
    Supports both binary_sensor and sensor domain:
    - binary_sensor: uses window_open_state / window_tilted_state (e.g. on/off, tilted)
    - sensor: uses state directly - "open", "tilted", "closed" (or similar variants)
    """
    window_id = shutter.get(CONF_WINDOW_ENTITY_ID)
    if not window_id:
        return "closed"  # No window = treat as closed

    if isinstance(window_id, list):
        window_id = window_id[0] if window_id else ""

    state = hass.states.get(window_id)
    if not state:
        return "closed"

    current = _normalize_state(state.state)
    parts = str(window_id).split(".", 1)
    domain = parts[0] if len(parts) > 1 else "binary_sensor"

    # Sensor domain: state is typically "open", "tilted", "closed" (or translations)
    if domain == "sensor":
        if current in ("open", "offen", "geöffnet"):
            return "open"
        if current in ("tilted", "gekippt", "kipp"):
            return "tilted"
        # closed, closed, geschlossen, zu, etc.
        return "closed"

    # binary_sensor: use configured open/tilted states
    open_val = _normalize_state(shutter.get(CONF_WINDOW_OPEN_STATE, "on"))
    tilted_val = _normalize_state(shutter.get(CONF_WINDOW_TILTED_STATE, "none"))

    if tilted_val and tilted_val != "none" and current == tilted_val:
        return "tilted"
    if current == open_val:
        return "open"
    return "closed"


def is_window_open_or_tilted(hass: HomeAssistant, shutter: dict) -> bool:
    """True if window is open or tilted (for lock protection check)."""
    return get_window_state(hass, shutter) in ("open", "tilted")


def get_effective_close_position(
    hass: HomeAssistant, shutter: dict, target_position: float
) -> float:
    """
    Apply lock protection (Aussperrschutz):
    - If lock_protection and window open/tilted: return min_position_when_open
      (so we never fully close - you can't lock yourself out)
    - Otherwise return target_position
    """
    if not shutter.get(CONF_LOCK_PROTECTION, False):
        return target_position

    if not is_window_open_or_tilted(hass, shutter):
        return target_position

    min_pos = shutter.get(CONF_MIN_POSITION_WHEN_OPEN, 20)
    # If target would close further than min_pos, cap at min_pos
    # Cover: 0 = closed, 100 = open. So lower = more closed.
    if target_position < min_pos:
        return float(min_pos)
    return target_position
