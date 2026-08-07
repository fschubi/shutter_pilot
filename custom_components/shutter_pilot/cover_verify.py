"""Check that a cover actually reached the requested position.

Radio-driven shutters lose commands now and then. Without this check the
integration stores the requested position as fact and keeps making decisions
on a value the cover never reached – for instance skipping an automated open
because it believes the shutter is already up.

On mismatch the command is repeated a configurable number of times. If it
still fails, the stored position is corrected to what the cover actually
reports and `shutter_pilot_cover_failed` is fired so users can react.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_VERIFY_AFTER,
    CONF_VERIFY_ENABLED,
    CONF_VERIFY_RETRIES,
    CONF_VERIFY_TOLERANCE,
    DEFAULT_VERIFY_AFTER,
    DEFAULT_VERIFY_RETRIES,
    DEFAULT_VERIFY_TOLERANCE,
    DOMAIN,
    EVENT_COVER_FAILED,
)

_LOGGER = logging.getLogger(__name__)


def _opt_int(entry: ConfigEntry, key: str, default: int, low: int, high: int) -> int:
    try:
        return max(low, min(high, int(entry.options.get(key, default))))
    except (TypeError, ValueError):
        return default


def is_enabled(entry: ConfigEntry) -> bool:
    return bool(entry.options.get(CONF_VERIFY_ENABLED, False))


def _current_position(hass: HomeAssistant, entity_id: str) -> float | None:
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unavailable", "unknown"):
        return None
    try:
        value = (state.attributes or {}).get("current_position")
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def supports_position_feedback(hass: HomeAssistant, entity_id: str) -> bool:
    """False for covers that only report open/closed.

    Verifying those would fail every single time, so they are left alone.
    """
    return _current_position(hass, entity_id) is not None


def cancel_verification(data: dict[str, Any], entity_id: str) -> None:
    """Drop a pending check, e.g. because a newer drive was issued."""
    tasks = data.get("_verify_tasks")
    if not isinstance(tasks, dict):
        return
    task = tasks.pop(entity_id, None)
    if task is not None and not task.done():
        task.cancel()


def cancel_all(data: dict[str, Any]) -> None:
    """Drop every pending check, used when unloading the entry."""
    tasks = data.get("_verify_tasks")
    if not isinstance(tasks, dict):
        return
    for task in list(tasks.values()):
        if not task.done():
            task.cancel()
    tasks.clear()


def schedule_verification(
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_id: str,
    target: float,
    reason: str,
) -> None:
    """Start a check for one cover, replacing any check still running."""
    if not is_enabled(entry):
        return
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not isinstance(data, dict):
        return
    if not supports_position_feedback(hass, entity_id):
        _LOGGER.debug("%s reports no position – skipping verification", entity_id)
        return

    cancel_verification(data, entity_id)
    tasks = data.setdefault("_verify_tasks", {})
    tasks[entity_id] = hass.async_create_task(
        _verify(hass, entry, entity_id, target, reason)
    )


async def _verify(
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_id: str,
    target: float,
    reason: str,
) -> None:
    # Imported here: helpers imports this module for set_cover_position.
    from .helpers import mark_automation_pending
    from .position_store import SOURCE_AUTOMATION, get_position_store

    wait = _opt_int(entry, CONF_VERIFY_AFTER, DEFAULT_VERIFY_AFTER, 5, 600)
    tolerance = _opt_int(entry, CONF_VERIFY_TOLERANCE, DEFAULT_VERIFY_TOLERANCE, 1, 50)
    retries = _opt_int(entry, CONF_VERIFY_RETRIES, DEFAULT_VERIFY_RETRIES, 0, 5)

    try:
        for attempt in range(retries + 1):
            await asyncio.sleep(wait)

            actual = _current_position(hass, entity_id)
            if actual is None:
                _LOGGER.debug("%s unavailable during verification", entity_id)
                return
            if abs(actual - target) <= tolerance:
                if attempt:
                    _LOGGER.info(
                        "%s reached %d%% after %d retr%s",
                        entity_id, int(target), attempt,
                        "y" if attempt == 1 else "ies",
                    )
                return

            if attempt < retries:
                _LOGGER.warning(
                    "%s is at %d%% instead of %d%% (%s) – repeating command",
                    entity_id, int(actual), int(target), reason,
                )
                # Mark again, otherwise the position tracker would file the
                # repeated drive as a manual change.
                mark_automation_pending(hass, entry, entity_id)
                await hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": target},
                    blocking=True,
                )
                continue

            _LOGGER.warning(
                "%s did not reach %d%% (still %d%%, %s) – giving up",
                entity_id, int(target), int(actual), reason,
            )
            # Correct the stored value, otherwise later decisions keep using a
            # position the cover never reached.
            store = get_position_store(hass, entry.entry_id)
            await store.async_set_position(entity_id, actual, SOURCE_AUTOMATION)
            data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
            if isinstance(data, dict):
                data.setdefault("last_positions", {})[entity_id] = actual
            hass.bus.async_fire(
                EVENT_COVER_FAILED,
                {
                    "entity_id": entity_id,
                    "requested": float(target),
                    "actual": actual,
                    "reason": reason,
                    "attempts": retries + 1,
                },
            )
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001 - a failed check must not break anything
        _LOGGER.exception("Verification for %s failed unexpectedly", entity_id)
    finally:
        tasks = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("_verify_tasks")
        # Only drop our own entry. A cancelled task runs this on a later loop
        # pass, by which time a newer drive may already have registered its
        # check – popping blindly would hide that one from cancel_all().
        if isinstance(tasks, dict) and tasks.get(entity_id) is asyncio.current_task():
            tasks.pop(entity_id, None)
