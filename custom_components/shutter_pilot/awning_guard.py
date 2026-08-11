"""Wind, rain and ice protection for awnings.

The one part of awning support that is not comfort. An awning left out in a
gust is a repair bill, so this module has priority over everything else in the
integration – including the master switch and both automation switches.

That is a deliberate break with the order that governs the rest of Shutter
Pilot (master -> area -> shutter). A protection that can be switched off by
accident is not a protection, and there is a way to switch this one off on
purpose: remove the sensor. It is documented in the panel, the README and the
changelog, because the first person whose awning comes in while the system is
"off" will otherwise report it as a bug.

Two states, not one, and keeping them apart is the whole design:

  barred      – must not extend. Applies from the first second, including
                while a sensor is unreadable.
  retracting  – must come in now. A threshold does this at once; an unreadable
                sensor only after the grace period, so a sensor blinking out
                during a restart does not yank every awning in the house.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    AWNING_GUARD_SLOTS,
    CONF_AWNING_SENSOR_GRACE,
    CONF_COVER_ENTITY_ID,
    CONF_SHUTTERS,
    DEFAULT_AWNING_LOCKOUT,
    DEFAULT_AWNING_SENSOR_GRACE,
    DOMAIN,
    EVENT_AWNING_RETRACTED,
    GUARD_REASON_UNAVAILABLE,
    MAX_AWNING_LOCKOUT,
    MAX_AWNING_SENSOR_GRACE,
    ROLE_OPEN,
    ROLE_SUN_PROTECT,
    awning_lockout_key,
    sun_condition_keys,
)
from .helpers import (
    get_position_for_role,
    guard_slot_danger,
    only_awnings,
    register_minute_callback,
    set_cover_position,
    set_cover_sun_protected,
)

_LOGGER = logging.getLogger(__name__)

# Runtime state per cover: when the last danger was seen, and what it was.
STATE_KEY = "_awning_guard"
# When a guard sensor first became unreadable, per cover and slot.
DEAD_SINCE_KEY = "_awning_guard_dead_since"


def resolve_guard_config(
    options: dict[str, Any], shutter: dict[str, Any]
) -> dict[str, Any]:
    """Merge the global protection settings with this awning's overrides.

    Most installations have exactly one wind sensor, so it lives in the
    settings and applies to every awning. An awning may name its own – a
    balcony behind the house sees a different wind than the terrace – and may
    override the thresholds on their own, because a small folding arm awning
    has to come in earlier than a cassette one on the same sensor.

    As in resolve_sun_geometry(), the key list below *is* the contract between
    the form and the logic. A field the form offers but that is missing here is
    stored, displayed and silently ignored.
    """
    merged: dict[str, Any] = {}
    for slot in AWNING_GUARD_SLOTS:
        keys = (*sun_condition_keys(slot), awning_lockout_key(slot))
        for key in keys:
            value = options.get(key)
            if value is not None and str(value).strip() != "":
                merged[key] = value
        for key in keys:
            value = shutter.get(key)
            if value is not None and str(value).strip() != "":
                merged[key] = value
    return merged


def _lockout_seconds(config: dict[str, Any], slot: str) -> float:
    try:
        minutes = float(
            config.get(awning_lockout_key(slot), DEFAULT_AWNING_LOCKOUT[slot])
        )
    except (TypeError, ValueError):
        minutes = DEFAULT_AWNING_LOCKOUT[slot]
    return max(0.0, min(minutes, MAX_AWNING_LOCKOUT)) * 60.0


def _grace_seconds(options: dict[str, Any]) -> float:
    try:
        minutes = float(
            options.get(CONF_AWNING_SENSOR_GRACE, DEFAULT_AWNING_SENSOR_GRACE)
        )
    except (TypeError, ValueError):
        minutes = DEFAULT_AWNING_SENSOR_GRACE
    return max(0.0, min(minutes, MAX_AWNING_SENSOR_GRACE)) * 60.0


def evaluate_guard(
    hass: HomeAssistant,
    entry: ConfigEntry,
    data: dict[str, Any],
    shutter: dict[str, Any],
    *,
    now: float | None = None,
) -> dict[str, Any]:
    """Decide whether this awning may be out, and say why not.

    Writes the lockout bookkeeping, so the export must not call it – there is
    guard_status() for a read-only view, the same split _memory_copy() makes
    for the shading conditions.
    """
    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
    options = dict(entry.options or {})
    config = resolve_guard_config(options, shutter)
    now = time.monotonic() if now is None else now

    states: dict[str, dict[str, Any]] = data.setdefault(STATE_KEY, {})
    entry_state = states.setdefault(cover, {})
    dead_since: dict[str, float] = data.setdefault(DEAD_SINCE_KEY, {})

    barred = False
    retract = False
    reasons: list[str] = []
    release_at: float | None = None

    for slot in AWNING_GUARD_SLOTS:
        danger, why = guard_slot_danger(hass, config, data, slot, cover)
        dead_key = f"{cover}|{slot}"

        if why == GUARD_REASON_UNAVAILABLE:
            # Barred immediately, pulled in only once the grace has run out.
            first = dead_since.setdefault(dead_key, now)
            barred = True
            reasons.append(f"{slot}:{GUARD_REASON_UNAVAILABLE}")
            grace = _grace_seconds(options)
            if now - first >= grace:
                retract = True
            else:
                release_at = max(release_at or 0.0, first + grace)
            entry_state.pop(f"{slot}_calm_since", None)
            continue

        dead_since.pop(dead_key, None)

        calm_key = f"{slot}_calm_since"
        danger_key = f"{slot}_danger"

        if danger:
            barred = True
            retract = True
            reasons.append(slot)
            # The lockout runs from the *last* exceedance, not the first: a
            # gust front is a series of them, and each one restarts the wait.
            entry_state[danger_key] = True
            entry_state.pop(calm_key, None)
            continue

        # Below the threshold again. The clock starts on the transition alone –
        # a sensor that has been quiet all along never had an exceedance, so
        # there is nothing to wait out. Getting this from the transition rather
        # than lazily on first sight is what keeps a fresh start from barring
        # every awning for twenty minutes.
        if entry_state.pop(danger_key, None):
            entry_state[calm_key] = now

        calm_since = entry_state.get(calm_key)
        if calm_since is None:
            continue
        lockout = _lockout_seconds(config, slot)
        if lockout <= 0:
            entry_state.pop(calm_key, None)
            continue
        if now - calm_since < lockout:
            barred = True
            reasons.append(f"{slot}:lockout")
            release_at = max(release_at or 0.0, calm_since + lockout)
        else:
            entry_state.pop(calm_key, None)

    entry_state["barred"] = barred
    entry_state["retract"] = retract
    entry_state["reasons"] = reasons
    entry_state["release_at"] = release_at
    entry_state["checked_at"] = now
    return entry_state


def guard_status(data: dict[str, Any], cover_entity_id: str) -> dict[str, Any]:
    """Read the last decision without touching it.

    Deliberately does not evaluate: evaluate_guard() writes hysteresis and
    lockout timers, and a report that moved the state it documents would be
    measuring something the measurement itself produced. Same rule as
    _memory_copy() in the export.
    """
    states = data.get(STATE_KEY)
    if not isinstance(states, dict):
        return {}
    return dict(states.get(cover_entity_id) or {})


def is_barred(data: dict[str, Any], cover_entity_id: str) -> bool:
    """True while this awning must not extend."""
    return bool(guard_status(data, cover_entity_id).get("barred"))


def extends_upward(shutter: dict[str, Any]) -> bool:
    """True when a higher cover position means "further out" for this awning.

    Almost always true – 100 is extended, 0 is in. It is asked rather than
    assumed because the direction is what the clamp below depends on, and an
    actuator wired the other way round would otherwise be barred from coming
    in instead of from going out.
    """
    return get_position_for_role(shutter, ROLE_SUN_PROTECT) >= get_position_for_role(
        shutter, ROLE_OPEN
    )


def clamp_to_rest(shutter: dict[str, Any], position: float) -> float:
    """Cap a target so it never sits further out than the rest position.

    Deliberately expressed against the *configured* rest position rather than
    against 0: the roles are what tell an awning apart from a shutter, so they
    have to be what the protection reads too.
    """
    rest = get_position_for_role(shutter, ROLE_OPEN)
    if extends_upward(shutter):
        return min(position, rest)
    return max(position, rest)


def describe_reasons(reasons: list[str] | None) -> str:
    """One short line for the log and the export."""
    return ", ".join(reasons or []) or "-"


async def async_retract_awning(
    hass: HomeAssistant,
    entry: ConfigEntry,
    data: dict[str, Any],
    shutter: dict[str, Any],
    reasons: list[str],
) -> bool:
    """Pull one awning in, bypassing the drive gap and the area stagger."""
    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
    if not cover:
        return False
    rest = get_position_for_role(shutter, ROLE_OPEN)
    reason_text = describe_reasons(reasons)
    ok = await set_cover_position(
        hass,
        entry,
        cover,
        rest,
        f"Awning protection ({reason_text})",
        urgent=True,
    )
    if not ok:
        _LOGGER.warning("[awning] %s: retraction failed – retrying next tick", cover)
        return False

    # Shading must let go as well. Left standing, the flag would keep the
    # awning counted as shaded, and the next evaluation would see "already
    # out" and never drive it again once the wind dies down.
    set_cover_sun_protected(data, cover, False)
    hass.bus.async_fire(
        EVENT_AWNING_RETRACTED,
        {"entity_id": cover, "reasons": list(reasons), "reason": reason_text},
    )
    _LOGGER.warning("[awning] %s: retracted – %s", cover, reason_text)
    return True


async def async_enforce_guard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Evaluate every awning and pull in the ones that must not be out."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        return
    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        return

    for shutter in only_awnings(shutters):
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
        if not cover:
            continue
        state = evaluate_guard(hass, entry, data, shutter)
        if not state.get("retract"):
            # Danger over – arm again, so the next storm drives afresh.
            state.pop("retracted", None)
            continue
        # Drive once per danger, not every minute: repeating would fight a
        # manual correction and flood the log through a stormy afternoon.
        # The marker is set by the drive, never by the intention to drive –
        # a failed retraction has to be tried again, and that distinction is
        # exactly what let a failed shading drive count as done before 2.8.0.
        if state.get("retracted"):
            continue
        if await async_retract_awning(
            hass, entry, data, shutter, state.get("reasons", [])
        ):
            state["retracted"] = True


async def setup_awning_guard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Watch the guard sensors and hold the minute tick as a safety net."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_awning_guard_unsubs", []):
        try:
            unsub()
        except Exception:  # pragma: no cover - defensive
            pass
    data["_awning_guard_unsubs"] = []

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    awnings = only_awnings(shutters)
    if not awnings:
        register_minute_callback(data, "awning_guard", None)
        return

    options = dict(entry.options or {})
    watched: set[str] = set()
    for shutter in awnings:
        config = resolve_guard_config(options, shutter)
        for slot in AWNING_GUARD_SLOTS:
            entity_id = str(config.get(sun_condition_keys(slot)[0]) or "").strip()
            if entity_id:
                watched.add(entity_id)

    @callback
    def _sensor_changed(_event) -> None:
        hass.async_create_task(async_enforce_guard(hass, entry))

    if watched:
        # The minute tick alone is too slow for a storm. Sixty seconds of gust
        # is exactly the interval this is meant to prevent.
        data["_awning_guard_unsubs"].append(
            async_track_state_change_event(hass, sorted(watched), _sensor_changed)
        )

    def _tick(_now) -> None:
        hass.async_create_task(async_enforce_guard(hass, entry))

    register_minute_callback(data, "awning_guard", _tick)
    hass.async_create_task(async_enforce_guard(hass, entry))
    _LOGGER.info(
        "Awning protection: %d awnings, %d sensor(s) watched", len(awnings), len(watched)
    )
