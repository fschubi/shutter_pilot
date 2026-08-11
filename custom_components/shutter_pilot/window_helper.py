"""Helper to check window state and apply lock protection (Aussperrschutz)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_ENTITY_ID,
    CONF_WINDOW_TILTED_ENTITY_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    DEFAULT_WINDOW_TILTED_ENTITY_STATE,
)
from .helpers import is_awning


def _normalize_state(val: Any) -> str:
    if val is None:
        return ""
    return str(val).lower().strip()


# A binary_sensor only ever reports "on" or "off", but the form lets you pick
# the word that means "open" – and "open" is the obvious pick, so people take
# it. It then never equals "on", the contact reads as permanently closed and
# nothing reacts to that window at all. Both sides are folded into the same two
# tokens instead, which leaves every exact match exactly as it was.
_STATE_SYNONYMS = {
    "on": "on",
    "true": "on",
    "1": "on",
    "open": "on",
    "offen": "on",
    "geöffnet": "on",
    "geoeffnet": "on",
    "auf": "on",
    "off": "off",
    "false": "off",
    "0": "off",
    "closed": "off",
    "geschlossen": "off",
    "zu": "off",
}


def _canonical_state(val: Any) -> str:
    """Fold on/off vocabulary onto one token; leave anything else untouched.

    Words like "tilted" or "2" are no synonym of either and stay themselves, so
    a three-state contact keeps matching only what it really reports.
    """
    text = _normalize_state(val)
    return _STATE_SYNONYMS.get(text, text)


def _first_entity_id(value: Any) -> str:
    """Accept both a plain entity id and a single-element list."""
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()


def get_tilt_entity_id(shutter: dict) -> str:
    """Entity id of the optional separate tilt contact, or empty string."""
    return _first_entity_id(shutter.get(CONF_WINDOW_TILTED_ENTITY_ID))


def has_separate_tilt_entity(shutter: dict) -> bool:
    """True if this shutter uses a dedicated entity for the tilted state."""
    return bool(get_tilt_entity_id(shutter))


def _separate_tilt_active(hass: HomeAssistant, shutter: dict) -> bool:
    """True if the dedicated tilt contact currently reports 'tilted'."""
    entity_id = get_tilt_entity_id(shutter)
    if not entity_id:
        return False
    state = hass.states.get(entity_id)
    if not state:
        return False
    expected = _normalize_state(
        shutter.get(CONF_WINDOW_TILTED_ENTITY_STATE, DEFAULT_WINDOW_TILTED_ENTITY_STATE)
    ) or DEFAULT_WINDOW_TILTED_ENTITY_STATE
    return _canonical_state(state.state) == _canonical_state(expected)


def has_tilt_state(shutter: dict) -> bool:
    """True if this shutter can tell "tilted" apart from "open".

    Either through a 3-state contact or through a second, dedicated entity.
    Without it the contact is two-valued and the tilt position is what gets
    driven, "open" included – so the export has to ask this too.
    """
    if has_separate_tilt_entity(shutter):
        return True
    tilted = shutter.get(CONF_WINDOW_TILTED_STATE, "none")
    return bool(tilted) and str(tilted).lower() != "none"


def get_window_state(hass: HomeAssistant, shutter: dict) -> str:
    """
    Return: "closed" | "tilted" | "open"
    Supports both binary_sensor and sensor domain:
    - binary_sensor: uses window_open_state / window_tilted_state (e.g. on/off, tilted)
    - sensor: uses state directly - "open", "tilted", "closed" (or similar variants)
    """
    # A dedicated tilt contact wins: some hardware reports "open" and "tilted"
    # as two separate entities, and while tilted both may read as open.
    if _separate_tilt_active(hass, shutter):
        return "tilted"

    window_id = _first_entity_id(shutter.get(CONF_WINDOW_ENTITY_ID))
    if not window_id:
        # Only a tilt contact configured – it is not tilted, so it is closed.
        return "closed"

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

    if tilted_val and tilted_val != "none" and _canonical_state(
        current
    ) == _canonical_state(tilted_val):
        return "tilted"
    if _canonical_state(current) == _canonical_state(open_val):
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
    # An awning must never be capped from below: the cap exists so a shutter
    # cannot close in front of an open door, and on an awning "lower" means
    # retracted – the safe end, not the dangerous one. A leftover lock_protection
    # from a converted shutter would stop it coming in at 20%.
    if is_awning(shutter):
        return target_position

    if not shutter.get(CONF_LOCK_PROTECTION, False):
        return target_position

    if not is_window_open_or_tilted(hass, shutter):
        return target_position

    min_pos = shutter.get(CONF_MIN_POSITION_WHEN_OPEN, 20)
    # If target would close further than min_pos, cap at min_pos
    # Cover: 0 = closed, 100 = open. So lower = more closed.
    try:
        min_pos_float = float(min_pos)
    except (TypeError, ValueError):
        min_pos_float = 20.0
    if target_position < min_pos_float:
        return min_pos_float
    return target_position
