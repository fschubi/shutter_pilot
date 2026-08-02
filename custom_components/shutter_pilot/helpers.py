"""Shared helper functions for Shutter Pilot."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_ID,
    CONF_AREA_AUTO_ENTITY_ID,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ELEVATION_THRESHOLD,
    CLOSE_CONDITION_SLOT,
    CONF_AREA_MANUAL_OVERRIDE,
    CONF_AREA_SEASON_FROM,
    CONF_AREA_SEASON_TO,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_SUN_GEOMETRY_OVERRIDE,
    CONF_POSITION_CLOSED_ALT,
    ROLE_CLOSED_ALT,
    CONF_AREA_UP_ID,
    CONF_COVER_ENTITY_ID,
    CONF_MASTER_ENTITY_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTER_AUTOMATION_ENABLED,
    CONF_SHUTTER_AUTO_ENTITY_ID,
    DEFAULT_POSITION_WHEN_WINDOW_TILTED,
    ROLE_VENTILATION,
    SUN_CONDITION_SLOTS,
    sun_condition_keys,
    CONF_TILT_CLOSED,
    CONF_TILT_ENABLED,
    CONF_TILT_OPEN,
    CONF_TILT_SUN_PROTECT,
    DEFAULT_AREA_AZIMUTH_MAX,
    DEFAULT_AREA_AZIMUTH_MIN,
    DEFAULT_AREA_ELEVATION_MIN,
    DEFAULT_AREA_ELEVATION_THRESHOLD,
    DEFAULT_AREA_MANUAL_OVERRIDE,
    DEFAULT_TILT_CLOSED,
    DEFAULT_TILT_OPEN,
    DEFAULT_TILT_SUN_PROTECT,
    EVENT_COVER_MOVED,
    OVERRIDE_DAILY,
    OVERRIDE_NEXT_ACTION,
    ROLE_CLOSED,
    ROLE_OPEN,
    ROLE_SUN_PROTECT,
)
from .position_store import (
    SOURCE_AUTOMATION,
    SOURCE_MANUAL,
    ShutterPositionStore,
    get_position_store,
)

_LOGGER = logging.getLogger(__name__)

POSITION_TOLERANCE_PCT = 8.0
AUTOMATION_STATE_GRACE_SEC = 90.0


def register_minute_callback(
    data: dict[str, Any], name: str, callback_fn: Any | None
) -> None:
    """Register (or clear) a callback for the shared minute ticker.

    Scheduler and sun protection both need to run once per minute. Keeping them
    on one ticker avoids duplicate timers and guarantees a stable order after a
    reload, because re-registering under the same name replaces the old entry.
    """
    callbacks = data.setdefault("_minute_callbacks", {})
    if callback_fn is None:
        callbacks.pop(name, None)
    else:
        callbacks[name] = callback_fn


def is_system_enabled(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """True if the global Shutter Pilot master switch is on."""
    domain_data = hass.data.get(DOMAIN)
    if not isinstance(domain_data, dict) or entry.entry_id not in domain_data:
        return True
    data = domain_data.get(entry.entry_id, {})
    if not isinstance(data, dict):
        return True
    if "master_enabled" in data:
        return bool(data.get("master_enabled"))

    entity_id = str(entry.options.get(CONF_MASTER_ENTITY_ID) or "").strip()
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if not state:
        return True
    return str(state.state).lower() in ("on", "true", "1")


def is_auto_enabled(hass: HomeAssistant, entry: ConfigEntry, area: dict) -> bool:
    """True if automation is enabled for this area."""
    if not is_system_enabled(hass, entry):
        return False

    area_id = str(area.get(CONF_AREA_ID) or "")
    domain_data = hass.data.get(DOMAIN)
    if not isinstance(domain_data, dict) or entry.entry_id not in domain_data:
        _LOGGER.debug("is_auto_enabled: no runtime data for %s – returning False (fail-safe)", area_id)
        return False
    data = domain_data.get(entry.entry_id, {})
    if not isinstance(data, dict):
        return False

    auto_modes = data.get("auto_modes", {})
    if isinstance(auto_modes, dict) and area_id in auto_modes:
        return bool(auto_modes.get(area_id))

    entity_id = str(area.get(CONF_AREA_AUTO_ENTITY_ID) or "").strip()
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if not state:
        _LOGGER.debug("is_auto_enabled: switch entity %s not found – returning False (fail-safe)", entity_id)
        return False
    return str(state.state).lower() in ("on", "true", "1")


def is_shutter_automation_enabled(
    hass: HomeAssistant, entry: ConfigEntry, shutter: dict
) -> bool:
    """True if automated driving is allowed for this single shutter.

    Third level below master switch and area switch. Unlike those two this one
    fails *open*: an unknown state must not stop a shutter, because the usual
    case is a shutter that was never switched off at all. Manual paths
    (services, dashboard buttons) never ask this.
    """
    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
    domain_data = hass.data.get(DOMAIN)
    if isinstance(domain_data, dict):
        data = domain_data.get(entry.entry_id, {})
        if isinstance(data, dict) and cover:
            runtime = data.get("shutter_automation", {})
            if isinstance(runtime, dict) and cover in runtime:
                return bool(runtime.get(cover))

    entity_id = str(shutter.get(CONF_SHUTTER_AUTO_ENTITY_ID) or "").strip()
    if entity_id:
        state = hass.states.get(entity_id)
        if state is not None and str(state.state).lower() in ("on", "off", "true", "false", "1", "0"):
            return str(state.state).lower() in ("on", "true", "1")

    return bool(shutter.get(CONF_SHUTTER_AUTOMATION_ENABLED, True))


def get_elevation_bounds(area: dict) -> tuple[float, float]:
    """Return (min, max) elevation for sun protection range."""
    elev_max = area.get(CONF_AREA_ELEVATION_MAX)
    elev_min = area.get(CONF_AREA_ELEVATION_MIN)
    if elev_max is None:
        elev_max = area.get(CONF_AREA_ELEVATION_THRESHOLD, DEFAULT_AREA_ELEVATION_THRESHOLD)
    if elev_min is None:
        try:
            elev_min = max(DEFAULT_AREA_ELEVATION_MIN, float(elev_max) - 3.0)
        except (TypeError, ValueError):
            elev_min = DEFAULT_AREA_ELEVATION_MIN
    try:
        e_min = float(elev_min)
        e_max = float(elev_max)
    except (TypeError, ValueError):
        e_min = DEFAULT_AREA_ELEVATION_MIN
        e_max = float(DEFAULT_AREA_ELEVATION_THRESHOLD)
    if e_min > e_max:
        e_min, e_max = e_max, e_min
    return e_min, e_max


def elevation_in_sun_protect_range(elevation: float, area: dict) -> bool:
    """True when sun elevation is within the configured protection window."""
    e_min, e_max = get_elevation_bounds(area)
    return e_min <= elevation <= e_max


def get_azimuth_bounds(area: dict) -> tuple[float, float]:
    """Return (min, max) azimuth for the windows of this area, in degrees."""
    try:
        a_min = float(area.get(CONF_AREA_AZIMUTH_MIN, DEFAULT_AREA_AZIMUTH_MIN))
    except (TypeError, ValueError):
        a_min = DEFAULT_AREA_AZIMUTH_MIN
    try:
        a_max = float(area.get(CONF_AREA_AZIMUTH_MAX, DEFAULT_AREA_AZIMUTH_MAX))
    except (TypeError, ValueError):
        a_max = DEFAULT_AREA_AZIMUTH_MAX
    return a_min % 360.0, a_max % 360.0


def azimuth_in_sun_protect_range(azimuth: float | None, area: dict) -> bool:
    """True when the sun stands in front of this area's windows.

    Ranges may wrap around north (e.g. 300°–60° for a north-facing room), which
    is why this is not a plain min <= x <= max comparison. If the azimuth check
    is switched off the answer is always True, preserving legacy behaviour.
    """
    if not bool(area.get(CONF_AREA_AZIMUTH_ENABLED, False)):
        return True
    if azimuth is None:
        # Without a reading we must not block shading – fail open.
        return True
    a_min, a_max = get_azimuth_bounds(area)
    az = float(azimuth) % 360.0
    if a_min == a_max:
        return True
    if a_min < a_max:
        return a_min <= az <= a_max
    return az >= a_min or az <= a_max


def sun_protect_conditions_met(
    elevation: float | None, azimuth: float | None, area: dict
) -> bool:
    """True when both elevation and compass direction call for shading."""
    if elevation is None:
        return False
    if not elevation_in_sun_protect_range(elevation, area):
        return False
    return azimuth_in_sun_protect_range(azimuth, area)


def _condition_slot_met(
    hass: HomeAssistant,
    area: dict[str, Any],
    slot: str,
    memory: dict[str, bool],
) -> bool:
    """Evaluate one extra shading condition, remembering it for hysteresis.

    A binary sensor answers directly. A numeric sensor becomes satisfied at
    `on_above` and stays satisfied until it drops below `off_below`, so a
    passing cloud does not make the shutters bounce. Anything unusable – no
    sensor, unknown, unavailable, non-numeric – never blocks shading.
    """
    entity_key, on_key, off_key, states_key = sun_condition_keys(slot)
    entity_id = str(area.get(entity_key) or "").strip()
    if not entity_id:
        return True

    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        _LOGGER.debug(
            "Sun condition %s: %s unavailable – not blocking shading",
            slot,
            entity_id,
        )
        return True

    # A list of allowed states wins: that covers weather entities and scrape
    # sensors whose state is text like "sunny" or "bewölkt".
    allowed = area.get(states_key)
    if isinstance(allowed, str):
        allowed = [p.strip() for p in allowed.split(",")]
    if isinstance(allowed, (list, tuple)) and any(str(x).strip() for x in allowed):
        wanted = {str(x).strip().lower() for x in allowed if str(x).strip()}
        met = str(state.state).strip().lower() in wanted
        memory[slot] = met
        return met

    if entity_id.startswith("binary_sensor."):
        met = str(state.state).lower() in ("on", "true", "1")
        memory[slot] = met
        return met

    try:
        value = float(state.state)
    except (TypeError, ValueError):
        # Text state without a configured state list. Previously this passed
        # silently, so a scrape sensor looked configured but did nothing.
        _LOGGER.warning(
            "Sun condition %s: %s reports the non-numeric state %r. Configure "
            "the allowed states for this condition, otherwise it is ignored.",
            slot,
            entity_id,
            state.state,
        )
        return True

    try:
        on_above = float(area.get(on_key))
    except (TypeError, ValueError):
        # Threshold not configured – the sensor alone cannot decide anything.
        return True

    try:
        off_below = float(area.get(off_key))
    except (TypeError, ValueError):
        off_below = on_above
    if off_below > on_above:
        off_below = on_above

    if memory.get(slot):
        met = value >= off_below
    else:
        met = value >= on_above
    memory[slot] = met
    return met


def sun_extra_conditions_met(
    hass: HomeAssistant,
    area: dict[str, Any],
    data: dict[str, Any],
    cover_entity_id: str | None = None,
) -> bool:
    """True when every configured extra condition for shading is satisfied.

    Pass the cover id when evaluating a merged per-shutter config, so each
    window keeps its own hysteresis state.
    """
    area_id = str(area.get(CONF_AREA_ID) or "")
    memory = condition_memory(data, area_id, cover_entity_id)
    for slot in SUN_CONDITION_SLOTS:
        if not _condition_slot_met(hass, area, slot, memory):
            return False
    return True


def close_condition_met(
    hass: HomeAssistant, area: dict[str, Any], data: dict[str, Any]
) -> bool:
    """True when the area's condition for a partial evening close applies.

    Uses the same evaluation as the shading conditions, just its own slot.
    Without a configured entity this is False, so nothing changes for anyone
    who has not set it up – unlike the shading conditions, where an unset
    condition must not block.
    """
    entity_key = sun_condition_keys(CLOSE_CONDITION_SLOT)[0]
    if not str(area.get(entity_key) or "").strip():
        return False
    area_id = str(area.get(CONF_AREA_ID) or "")
    return _condition_slot_met(
        hass, area, CLOSE_CONDITION_SLOT, condition_memory(data, area_id)
    )


def season_allows_shading(area: dict[str, Any], now: datetime | None = None) -> bool:
    """True if today lies inside the configured shading season.

    Months are inclusive and may wrap across the turn of the year, so 10 to 3
    means October through March. Same wrap-around idea as the azimuth range.
    Unset means all year round.
    """
    try:
        start = int(area.get(CONF_AREA_SEASON_FROM) or 0)
        end = int(area.get(CONF_AREA_SEASON_TO) or 0)
    except (TypeError, ValueError):
        return True
    if not (1 <= start <= 12) or not (1 <= end <= 12):
        return True

    month = (now or datetime.now()).month
    if start <= end:
        return start <= month <= end
    return month >= start or month <= end


def resolve_sun_geometry(
    area: dict[str, Any], shutter: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Merge area and shutter shading geometry into one config dict.

    A room can have windows facing different directions, so elevation and
    azimuth may be overridden per shutter. Returning a merged dict keeps
    get_elevation_bounds(), get_azimuth_bounds() and sun_protect_conditions_met()
    working unchanged – they simply read from the merged config.
    """
    if not shutter or not bool(shutter.get(CONF_SUN_GEOMETRY_OVERRIDE, False)):
        return area

    merged = dict(area)
    for key in (
        CONF_AREA_ELEVATION_MIN,
        CONF_AREA_ELEVATION_MAX,
        CONF_AREA_AZIMUTH_ENABLED,
        CONF_AREA_AZIMUTH_MIN,
        CONF_AREA_AZIMUTH_MAX,
    ):
        if shutter.get(key) is not None:
            merged[key] = shutter[key]
    # A per-shutter override replaces the legacy single threshold as well,
    # otherwise get_elevation_bounds() would fall back to the area value.
    merged.pop(CONF_AREA_ELEVATION_THRESHOLD, None)
    return merged


def resolve_shading_config(
    area: dict[str, Any], shutter: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Merge area and shutter shading settings into one config dict.

    Geometry follows the existing all-or-nothing override switch. The extra
    conditions fall back **per slot**: a slot with an entity set on the shutter
    replaces that slot completely, an empty one keeps the area's value.

    That way the default lives in the area and only the exception sits on the
    window – a brightness sensor per window, while the weather condition stays
    configured once for the whole area.
    """
    merged = resolve_sun_geometry(area, shutter)
    if not shutter:
        return merged

    overridden: list[str] = []
    for slot in SUN_CONDITION_SLOTS:
        entity_key, on_key, off_key, states_key = sun_condition_keys(slot)
        if not str(shutter.get(entity_key) or "").strip():
            continue
        if merged is area:
            merged = dict(area)
        for key in (entity_key, on_key, off_key, states_key):
            merged[key] = shutter.get(key)
        overridden.append(slot)

    if overridden:
        _LOGGER.debug(
            "Shutter %s overrides condition slots %s",
            shutter.get(CONF_COVER_ENTITY_ID),
            ", ".join(overridden),
        )
    return merged


def condition_memory(
    data: dict[str, Any], area_id: str, cover_entity_id: str | None = None
) -> dict[str, bool]:
    """Hysteresis memory for one area, or for one cover inside it.

    Two windows of the same area can watch different sensors, so they must not
    share a hysteresis state – otherwise one window's cloud would release the
    other one's shading.
    """
    key = f"{area_id}|{cover_entity_id}" if cover_entity_id else area_id
    return data.setdefault("sun_cond_state", {}).setdefault(key, {})


def is_cover_sun_protected(data: dict[str, Any], cover_entity_id: str) -> bool:
    """True if shading currently holds this specific cover."""
    covers = data.get("sun_protect_covers")
    return isinstance(covers, set) and cover_entity_id in covers


def set_cover_sun_protected(
    data: dict[str, Any], cover_entity_id: str, active: bool
) -> None:
    """Track shading per cover, so windows facing different ways act apart."""
    covers = data.setdefault("sun_protect_covers", set())
    if active:
        covers.add(cover_entity_id)
    else:
        covers.discard(cover_entity_id)


def get_sun_condition_status(
    hass: HomeAssistant, area: dict[str, Any]
) -> list[dict[str, Any]]:
    """Per-slot status of the extra shading conditions, for the dashboard."""
    out: list[dict[str, Any]] = []
    for slot in SUN_CONDITION_SLOTS:
        entity_key, on_key, _off_key, states_key = sun_condition_keys(slot)
        entity_id = str(area.get(entity_key) or "").strip()
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        out.append(
            {
                "slot": slot,
                "entity_id": entity_id,
                "state": state.state if state else None,
                "on_above": area.get(on_key),
                "states": area.get(states_key),
                "available": state is not None
                and state.state not in ("unknown", "unavailable"),
            }
        )
    return out


def is_sun_protect_active(data: dict[str, Any], area_id: str) -> bool:
    """Runtime flag: sun protection currently active for an area."""
    active = data.get("sun_protect_active", {})
    if not isinstance(active, dict):
        return False
    return bool(active.get(area_id))


def set_sun_protect_active(data: dict[str, Any], area_id: str, active: bool) -> None:
    """Update runtime sun protection state for dashboard and skip logic."""
    state = data.setdefault("sun_protect_active", {})
    if active:
        state[area_id] = True
    else:
        state.pop(area_id, None)


_ROLE_POSITION_KEYS = {
    ROLE_OPEN: (CONF_POSITION_OPEN, 100),
    ROLE_CLOSED: (CONF_POSITION_CLOSED, 0),
    ROLE_SUN_PROTECT: (CONF_POSITION_SUN_PROTECT, 50),
    # Ventilation deliberately reuses the tilted-window position instead of
    # introducing a fourth setting users would have to fill in twice.
    ROLE_VENTILATION: (
        CONF_POSITION_WHEN_WINDOW_TILTED,
        DEFAULT_POSITION_WHEN_WINDOW_TILTED,
    ),
    ROLE_CLOSED_ALT: (CONF_POSITION_CLOSED_ALT, 50),
}


def has_alt_close_position(shutter: dict[str, Any]) -> bool:
    """True if this shutter defines a partial closing position."""
    raw = shutter.get(CONF_POSITION_CLOSED_ALT)
    if raw is None or str(raw).strip() == "":
        return False
    try:
        float(raw)
    except (TypeError, ValueError):
        return False
    return True

_ROLE_TILT_KEYS = {
    ROLE_OPEN: (CONF_TILT_OPEN, DEFAULT_TILT_OPEN),
    ROLE_CLOSED: (CONF_TILT_CLOSED, DEFAULT_TILT_CLOSED),
    ROLE_SUN_PROTECT: (CONF_TILT_SUN_PROTECT, DEFAULT_TILT_SUN_PROTECT),
    ROLE_VENTILATION: (CONF_TILT_SUN_PROTECT, DEFAULT_TILT_SUN_PROTECT),
    ROLE_CLOSED_ALT: (CONF_TILT_CLOSED, DEFAULT_TILT_CLOSED),
}


def get_position_for_role(shutter: dict[str, Any], role: str) -> float:
    """Return the configured cover position for open/closed/sun_protect."""
    key, fallback = _ROLE_POSITION_KEYS.get(role, (CONF_POSITION_OPEN, 100))
    try:
        return float(shutter.get(key, fallback))
    except (TypeError, ValueError):
        return float(fallback)


def get_tilt_for_role(shutter: dict[str, Any], role: str) -> float | None:
    """Return the slat angle for a role, or None when tilt is not used."""
    if not bool(shutter.get(CONF_TILT_ENABLED, False)):
        return None
    key, fallback = _ROLE_TILT_KEYS.get(role, (CONF_TILT_OPEN, DEFAULT_TILT_OPEN))
    try:
        value = float(shutter.get(key, fallback))
    except (TypeError, ValueError):
        return float(fallback)
    return max(0.0, min(100.0, value))


def filter_shutters_by_area(shutters: list, area_id: str, use_up: bool) -> list:
    """Filter shutters by area_up_id or area_down_id."""
    key = CONF_AREA_UP_ID if use_up else CONF_AREA_DOWN_ID
    return [s for s in shutters if str(s.get(key) or "").strip() == area_id]


def get_cover_current_position(hass: HomeAssistant, entity_id: str) -> float | None:
    """Return cover current_position (0..100) if available."""
    try:
        st = hass.states.get(entity_id)
        attrs = (st.attributes or {}) if st else {}
        cur = attrs.get("current_position")
        if cur is None:
            return None
        return float(cur)
    except (TypeError, ValueError):
        return None


def positions_differ_significantly(
    a: float, b: float, tolerance: float = POSITION_TOLERANCE_PCT
) -> bool:
    """True if two positions differ by more than tolerance percent."""
    return abs(a - b) > tolerance


def _position_near(value: float, target: float, tolerance: float = POSITION_TOLERANCE_PCT) -> bool:
    return abs(value - target) <= tolerance


def mark_automation_pending(hass: HomeAssistant, entry: ConfigEntry, cover_entity_id: str) -> None:
    """Mark cover so the next state change is recorded as automation, not manual."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        return
    pending = data.setdefault("pending_automation_covers", set())
    pending.add(cover_entity_id)
    recent = data.setdefault("recent_automation_covers", {})
    recent[cover_entity_id] = time.monotonic()


def is_recent_automation(data: dict[str, Any], cover_entity_id: str) -> bool:
    """True if this cover was moved by automation within the grace window."""
    if cover_entity_id in data.get("pending_automation_covers", set()):
        return True
    recent = data.get("recent_automation_covers", {})
    if not isinstance(recent, dict):
        return False
    ts = recent.get(cover_entity_id)
    if ts is None:
        return False
    try:
        return (time.monotonic() - float(ts)) < AUTOMATION_STATE_GRACE_SEC
    except (TypeError, ValueError):
        return False


def sun_protect_area_ids_from_options(areas: list[Any]) -> set[str]:
    """Area ids where elevation-based sun protection is enabled."""
    out: set[str] = set()
    if not isinstance(areas, list):
        return out
    for a in areas:
        if not isinstance(a, dict):
            continue
        if not bool(a.get(CONF_AREA_SUN_PROTECT_ENABLED, False)):
            continue
        aid = str(a.get(CONF_AREA_ID) or "").strip()
        if aid:
            out.add(aid)
    return out


def clear_covers_driven_for_direction(data: dict[str, Any], direction: str) -> None:
    """Clear phase locks when a new up/down cycle begins."""
    if direction == "up":
        data["covers_driven_up"] = set()
    elif direction == "down":
        data["covers_driven_down"] = set()


async def clear_manual_override_for_covers(
    hass: HomeAssistant, entry: ConfigEntry, cover_entity_ids: list[str]
) -> None:
    """Allow scheduled automation to drive covers after a manual override."""
    store = get_position_store(hass, entry.entry_id)
    for cover in cover_entity_ids:
        if not cover:
            continue
        rec = store.get_record(cover)
        if not rec or rec.get("source") != SOURCE_MANUAL:
            continue
        try:
            pos = float(rec["position"])
        except (TypeError, ValueError, KeyError):
            continue
        await store.async_set_position(cover, pos, SOURCE_AUTOMATION)


def should_skip_full_open_preserving_sun_protect(
    hass: HomeAssistant,
    shutter: dict[str, Any],
    data: dict[str, Any],
    sun_protect_area_ids: set[str],
) -> bool:
    """True if automated full-open should not run (active sun protection at cover)."""
    down_id = str(shutter.get(CONF_AREA_DOWN_ID) or "").strip()
    if not down_id or down_id not in sun_protect_area_ids:
        return False
    if not is_sun_protect_active(data, down_id):
        return False
    cover = shutter.get(CONF_COVER_ENTITY_ID)
    if not cover:
        return False
    cur = get_cover_current_position(hass, cover)
    if cur is None:
        cur = _persisted_position(hass, cover)
    if cur is None:
        return False
    try:
        pos_open = float(shutter.get(CONF_POSITION_OPEN, 100))
        pos_sp = float(shutter.get(CONF_POSITION_SUN_PROTECT, 50))
    except (TypeError, ValueError):
        return False
    if cur >= pos_open - 5.0:
        return False
    if abs(cur - pos_sp) > 10.0:
        return False
    return True


def _persisted_position(hass: HomeAssistant, cover_entity_id: str) -> float | None:
    """Read last persisted position from any config entry store."""
    domain_data = hass.data.get(DOMAIN, {})
    if not isinstance(domain_data, dict):
        return None
    for entry_id, data in domain_data.items():
        if not isinstance(data, dict):
            continue
        store = data.get("position_store")
        if isinstance(store, ShutterPositionStore):
            pos = store.get_position_sync(cover_entity_id)
            if pos is not None:
                return pos
    return None


def manual_override_still_blocks(
    store: ShutterPositionStore, cover_entity_id: str, area: dict[str, Any] | None
) -> bool:
    """True if a manual position should keep blocking automated opening.

    The behaviour is configurable per area:
      never       – manual wins until the next close cycle (legacy default)
      daily       – manual only counts on the calendar day it was set
      next_action – scheduled actions always win
    """
    mode = DEFAULT_AREA_MANUAL_OVERRIDE
    if isinstance(area, dict):
        mode = str(area.get(CONF_AREA_MANUAL_OVERRIDE) or DEFAULT_AREA_MANUAL_OVERRIDE)

    if mode == OVERRIDE_NEXT_ACTION:
        return False

    if mode == OVERRIDE_DAILY:
        rec = store.get_record(cover_entity_id) or {}
        raw = rec.get("updated")
        if not raw:
            return True
        try:
            updated = datetime.fromisoformat(str(raw))
        except (TypeError, ValueError):
            return True
        if updated.date() < datetime.now().astimezone().date():
            _LOGGER.debug(
                "Manual override for %s expired (set on %s)",
                cover_entity_id,
                updated.date().isoformat(),
            )
            return False
        return True

    return True


def should_skip_automated_up(
    hass: HomeAssistant,
    entry: ConfigEntry,
    shutter: dict[str, Any],
    data: dict[str, Any],
    sun_protect_area_ids: set[str],
    *,
    within_up_window: bool = True,
    area: dict[str, Any] | None = None,
) -> bool:
    """True if an automated UP should not run for this shutter."""
    if should_skip_full_open_preserving_sun_protect(
        hass, shutter, data, sun_protect_area_ids
    ):
        return True

    if not within_up_window:
        return False

    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
    if not cover:
        return False

    store = get_position_store(hass, entry.entry_id)
    source = store.get_source_sync(cover)
    if source != SOURCE_MANUAL:
        return False

    if not manual_override_still_blocks(store, cover, area):
        return False

    try:
        pos_open = float(shutter.get(CONF_POSITION_OPEN, 100))
    except (TypeError, ValueError):
        return False

    cur = get_cover_current_position(hass, cover)
    persisted = store.get_position_sync(cover)
    check_pos = persisted if persisted is not None else cur
    if check_pos is None:
        return False

    if check_pos < pos_open - POSITION_TOLERANCE_PCT:
        _LOGGER.debug(
            "Skip automated UP for %s: manual position %.0f%% (HA reports %.0f%%)",
            cover,
            check_pos,
            cur if cur is not None else -1,
        )
        return True

    return False


def apply_covers_driven_from_persisted(
    hass: HomeAssistant,
    entry: ConfigEntry,
    shutters: list,
    store: ShutterPositionStore,
) -> None:
    """Load last_positions from store after restart (no phase locks)."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        return

    last_positions: dict[str, float] = data.setdefault("last_positions", {})

    for shutter in shutters:
        if not isinstance(shutter, dict):
            continue
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
        if not cover:
            continue

        rec = store.get_record(cover)
        if not rec:
            continue

        try:
            pos = float(rec["position"])
        except (TypeError, ValueError, KeyError):
            continue

        last_positions[cover] = pos

    _LOGGER.debug("Loaded %d persisted positions into last_positions", len(last_positions))


def clear_stale_window_cycle_after_automated_up(
    data: dict[str, Any], cover_entity_id: str
) -> None:
    """Drop window open/tilt restore state after automation opened the cover (day phase)."""
    if not cover_entity_id:
        return
    ta = data.get("trigger_actions")
    if isinstance(ta, dict):
        ta.pop(cover_entity_id, None)
    th = data.get("trigger_heights")
    if isinstance(th, dict):
        th.pop(cover_entity_id, None)
    pending = data.get("drive_after_close_pending")
    if isinstance(pending, dict):
        pending.pop(cover_entity_id, None)


def get_sun_protect_status_for_areas(
    hass: HomeAssistant, entry: ConfigEntry, areas: list
) -> dict[str, dict[str, Any]]:
    """Runtime sun protection status per area for the dashboard."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    if not isinstance(data, dict):
        data = {}

    elev, azim = get_sun_angles(hass)

    out: dict[str, dict[str, Any]] = {}
    if not isinstance(areas, list):
        return out

    for area in areas:
        if not isinstance(area, dict):
            continue
        if not bool(area.get(CONF_AREA_SUN_PROTECT_ENABLED, False)):
            continue
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            continue
        e_min, e_max = get_elevation_bounds(area)
        a_min, a_max = get_azimuth_bounds(area)
        azimuth_used = bool(area.get(CONF_AREA_AZIMUTH_ENABLED, False))
        out[area_id] = {
            "active": is_sun_protect_active(data, area_id),
            "in_range": sun_protect_conditions_met(elev, azim, area),
            "elevation_in_range": elev is not None
            and elevation_in_sun_protect_range(elev, area),
            "azimuth_in_range": azimuth_in_sun_protect_range(azim, area),
            "elevation_min": e_min,
            "elevation_max": e_max,
            "current_elevation": elev,
            "azimuth_enabled": azimuth_used,
            "azimuth_min": a_min,
            "azimuth_max": a_max,
            "current_azimuth": azim,
        }
    return out


def get_sun_angles(hass: HomeAssistant) -> tuple[float | None, float | None]:
    """Return (elevation, azimuth) from sun.sun, or (None, None)."""
    sun_state = hass.states.get("sun.sun")
    if not sun_state:
        return None, None
    attrs = sun_state.attributes or {}

    def _num(key: str) -> float | None:
        try:
            value = attrs.get(key)
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    return _num("elevation"), _num("azimuth")


async def set_cover_position(
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_id: str,
    position: float,
    reason: str,
    *,
    source: str | None = None,
    tilt_position: float | None = None,
    area_id: str | None = None,
) -> None:
    """Set cover position (and optionally slat angle) and persist the result."""
    mark_automation_pending(hass, entry, entity_id)
    try:
        await hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )
        _LOGGER.info("%s: %s -> %d%%", reason, entity_id, int(position))

        if tilt_position is not None:
            await _set_cover_tilt(hass, entity_id, tilt_position, reason)

        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if isinstance(data, dict):
            data.setdefault("last_positions", {})[entity_id] = float(position)

        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(
            entity_id,
            position,
            source or SOURCE_AUTOMATION,
        )

        hass.bus.async_fire(
            EVENT_COVER_MOVED,
            {
                "entity_id": entity_id,
                "position": float(position),
                "tilt_position": tilt_position,
                "reason": reason,
                "area_id": area_id,
                "source": source or SOURCE_AUTOMATION,
            },
        )

        # Check later whether the cover really got there. Imported lazily
        # because cover_verify needs helpers itself.
        from .cover_verify import schedule_verification

        schedule_verification(hass, entry, entity_id, float(position), reason)
    except Exception as e:
        _LOGGER.warning("Failed to set %s: %s", entity_id, e)
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if isinstance(data, dict):
            data.setdefault("pending_automation_covers", set()).discard(entity_id)
            recent = data.setdefault("recent_automation_covers", {})
            recent.pop(entity_id, None)


async def _set_cover_tilt(
    hass: HomeAssistant, entity_id: str, tilt_position: float, reason: str
) -> None:
    """Set the slat angle. Covers without tilt support are skipped quietly."""
    state = hass.states.get(entity_id)
    supported = 0
    if state is not None:
        try:
            supported = int(state.attributes.get("supported_features") or 0)
        except (TypeError, ValueError):
            supported = 0
    # CoverEntityFeature.SET_TILT_POSITION == 128
    if supported and not supported & 128:
        _LOGGER.debug("%s does not support tilt – skipping slat angle", entity_id)
        return
    try:
        await hass.services.async_call(
            "cover",
            "set_cover_tilt_position",
            {"entity_id": entity_id, "tilt_position": tilt_position},
            blocking=True,
        )
        _LOGGER.info("%s: %s slats -> %d%%", reason, entity_id, int(tilt_position))
    except Exception as e:  # pragma: no cover - defensive
        _LOGGER.debug("Tilt for %s failed: %s", entity_id, e)
