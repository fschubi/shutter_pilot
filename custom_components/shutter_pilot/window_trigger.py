"""Window trigger logic - React to window open/close for shutters."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_POSITION_CLOSED,
    DEFAULT_WINDOW_CLOSE_DEBOUNCE,
    MAX_WINDOW_CLOSE_DEBOUNCE,
)
from .helpers import (
    forget_drive_after_close,
    get_tracked_position,
    is_cover_sun_protected,
    is_shutter_automation_enabled,
    is_system_enabled,
    only_shutters,
    set_cover_position,
)
from .window_helper import (
    get_effective_close_position,
    get_tilt_entity_id,
    get_window_state,
    has_tilt_state,
)

_LOGGER = logging.getLogger(__name__)

_CLOSED_TOLERANCE_PCT = 8.0


def _is_cover_effectively_closed(shutter: dict, current_position: float) -> bool:
    """True if cover is close enough to its configured closed position."""
    try:
        pos_closed = float(shutter.get(CONF_POSITION_CLOSED, 0))
    except (TypeError, ValueError):
        pos_closed = 0.0
    return current_position <= (pos_closed + _CLOSED_TOLERANCE_PCT)


def _debounce_seconds(shutter: dict) -> int:
    """How long "closed" has to hold before we act on it."""
    try:
        value = int(shutter.get(CONF_WINDOW_CLOSE_DEBOUNCE, DEFAULT_WINDOW_CLOSE_DEBOUNCE))
    except (TypeError, ValueError):
        return DEFAULT_WINDOW_CLOSE_DEBOUNCE
    return max(0, min(MAX_WINDOW_CLOSE_DEBOUNCE, value))


def cancel_window_close(data: dict[str, Any], entity_id: str) -> None:
    """Drop a pending close reaction, e.g. because the window opened again."""
    tasks = data.get("_window_close_tasks")
    if not isinstance(tasks, dict):
        return
    task = tasks.pop(entity_id, None)
    if task is not None and not task.done():
        task.cancel()


def cancel_all_window_close(data: dict[str, Any]) -> None:
    """Drop every pending close reaction, for unload and reload."""
    tasks = data.get("_window_close_tasks")
    if not isinstance(tasks, dict):
        return
    for task in list(tasks.values()):
        if not task.done():
            task.cancel()
    tasks.clear()


# Liegt in window_helper, seit der Export dieselbe Frage stellt.
_has_tilt_state = has_tilt_state


def _get_target_position_for_window_state(
    shutter: dict, state_str: str
) -> float | None:
    """Return target position for window state. None = restore."""
    if state_str == "closed":
        return None
    if state_str == "tilted":
        return shutter.get(CONF_POSITION_WHEN_WINDOW_TILTED, 50)
    if state_str == "open":
        if not _has_tilt_state(shutter):
            # 2-state contact: open and tilt are indistinguishable -> ventilation position
            return shutter.get(CONF_POSITION_WHEN_WINDOW_TILTED, 50)
        return shutter.get(CONF_POSITION_WHEN_WINDOW_OPEN, 100)
    return None


async def setup_window_triggers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up state listeners for window entities that trigger shutter changes."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    # Cancel previous listeners. Pending close reactions have to go too: this
    # runs on every save in the panel, and a surviving timer would drive with
    # the shutter configuration it captured before the change.
    for unsub in data.get("_window_unsubs", []):
        unsub()
    data["_window_unsubs"] = []
    cancel_all_window_close(data)

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

    # Collect every watched entity and the shutters it belongs to. A shutter
    # may register under two entities: the main contact and an optional
    # separate tilt contact.
    window_to_shutters: dict[str, list[dict]] = {}

    def _watch(entity_id: str, shutter: dict) -> None:
        if not entity_id:
            return
        bucket = window_to_shutters.setdefault(entity_id, [])
        if shutter not in bucket:
            bucket.append(shutter)

    # An awning has no window contact – the form does not offer one, and
    # converting a shutter deletes the keys. Filtering anyway costs nothing
    # and keeps a stray leftover value from registering a listener that would
    # then drive an awning to a tilted-window position it does not have.
    for shutter in only_shutters(shutters):
        window_id = shutter.get(CONF_WINDOW_ENTITY_ID)
        if isinstance(window_id, list):
            window_id = window_id[0] if window_id else ""
        _watch(str(window_id or "").strip(), shutter)
        _watch(get_tilt_entity_id(shutter), shutter)

    @callback
    def _apply_window_closed(shutter: dict, cover_entity: str, pos_closed: Any) -> None:
        """React to a window that stayed closed: catch up, or restore."""
        pending_entry = forget_drive_after_close(hass, entry, data, cover_entity)
        if pending_entry is not None:
            target_pos = pending_entry.get("position", pos_closed)
            reason = pending_entry.get("reason", "Drive after close")
            hass.async_create_task(
                set_cover_position(
                    hass,
                    entry,
                    cover_entity,
                    target_pos,
                    reason,
                    tilt_position=pending_entry.get("tilt"),
                )
            )
            _LOGGER.info(
                "Fenster geschlossen – Drive-after-close: %s -> %d%%",
                cover_entity, int(target_pos),
            )
            return

        # Restore only if this window cycle actually triggered a movement.
        if trigger_actions.get(cover_entity) == "triggered":
            restore_pos = trigger_heights.get(cover_entity)
            if restore_pos is None:
                restore_pos = last_positions.get(cover_entity, pos_closed)
            hass.async_create_task(
                set_cover_position(
                    hass,
                    entry,
                    cover_entity,
                    restore_pos,
                    "Window closed – restore",
                )
            )
        trigger_actions.pop(cover_entity, None)
        trigger_heights.pop(cover_entity, None)

    async def _delayed_close(
        shutter: dict, cover_entity: str, pos_closed: Any, delay: int
    ) -> None:
        """Wait out a short "closed" blip before reacting to it."""
        try:
            await asyncio.sleep(delay)
            # Re-read instead of trusting the cancel: cancelling only takes
            # effect on the next loop pass, and a state can change without an
            # event ever reaching us.
            if get_window_state(hass, shutter) != "closed":
                return
            if not is_system_enabled(hass, entry):
                return
            if not is_shutter_automation_enabled(hass, entry, shutter):
                return
            _apply_window_closed(shutter, cover_entity, pos_closed)
        except asyncio.CancelledError:
            raise
        except Exception:  # pragma: no cover - one window must not break others
            _LOGGER.exception("Delayed window close failed for %s", cover_entity)
        finally:
            tasks = data.get("_window_close_tasks")
            # Only drop our own entry – a newer task may already have replaced
            # us in the dict while this one was being cancelled.
            if isinstance(tasks, dict) and tasks.get(cover_entity) is asyncio.current_task():
                tasks.pop(cover_entity, None)

    @callback
    def _on_window_state_change(event) -> None:
        if not is_system_enabled(hass, entry):
            return
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        entity_id = event.data.get("entity_id", "")

        try:
            new_val = new_state.state
        except AttributeError:
            new_val = getattr(new_state, "state", None)

        for shutter in window_to_shutters.get(entity_id, []):
            cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover_entity:
                continue
            # Automation off at this shutter: do not react to the window at
            # all. Also drop a pending catch-up drive, otherwise it would fire
            # the moment the automation is switched back on.
            if not is_shutter_automation_enabled(hass, entry, shutter):
                cancel_window_close(data, cover_entity)
                forget_drive_after_close(hass, entry, data, cover_entity)
                trigger_actions.pop(cover_entity, None)
                trigger_heights.pop(cover_entity, None)
                continue
            pos_closed = shutter.get(CONF_POSITION_CLOSED, 0)

            # Use window_helper for consistent binary_sensor + sensor support
            window_state = get_window_state(hass, shutter)

            if window_state != "closed":
                # The handle passes through "closed" on its way from tilted to
                # open. Drop the planned drive back before anything else can
                # act on it.
                cancel_window_close(data, cover_entity)

            target_pos = _get_target_position_for_window_state(shutter, window_state)

            if window_state in ("open", "tilted") and target_pos is not None:
                # Window open or tilted -> only drive to target if the cover is (nearly) closed.
                # Rationale: During daytime (cover already opened by automation), opening a window/door
                # must NOT force the cover into a "ventilation" position.
                cycle_active = trigger_actions.get(cover_entity) == "triggered"
                current_pos = get_tracked_position(hass, shutter, cover_entity)
                if current_pos is None:
                    # Fail-safe: if we can't read current position, do nothing.
                    trigger_actions.pop(cover_entity, None)
                    trigger_heights.pop(cover_entity, None)
                    continue
                # Shading counts as a reason to react, whatever the position.
                # The order is window contact > shading > ventilation, but the
                # contact could not reach a shaded shutter at all: shading
                # parks it at, say, 25 %, which is neither closed nor open, so
                # the check below sent it away. Opening the terrace door in the
                # afternoon then left the shutter hanging in front of it.
                shaded = is_cover_sun_protected(data, cover_entity)
                if not cycle_active and not shaded and not _is_cover_effectively_closed(
                    shutter, current_pos
                ):
                    # Not in "closed" state -> no window-trigger cycle active.
                    # Clear stale cycle markers so a later "closed" event cannot restore/close.
                    trigger_actions.pop(cover_entity, None)
                    trigger_heights.pop(cover_entity, None)
                    continue

                if not cycle_active:
                    # Remember the height only when the cycle starts. Going
                    # from tilted to open would otherwise make the ventilation
                    # position the height we restore to later.
                    trigger_heights[cover_entity] = current_pos
                trigger_actions[cover_entity] = "triggered"
                if window_state == "tilted":
                    reason = "Window tilted"
                elif not _has_tilt_state(shutter):
                    reason = "Window opened (2-state ventilation)"
                else:
                    reason = "Window opened"
                # Der Aussperrschutz galt an jedem automatisierten Fahrweg –
                # ausser an diesem, dem einzigen, der ausschliesslich bei
                # offenem Fenster faehrt. Eine Kipp-Position unterhalb der
                # Mindesthoehe schloss den Rollladen damit vor der offenen
                # Terrassentuer, genau was die Einstellung verhindern soll.
                target_pos = get_effective_close_position(hass, shutter, target_pos)
                hass.async_create_task(
                    set_cover_position(hass, entry, cover_entity, target_pos, reason)
                )
            elif window_state == "closed":
                # Window closed -> restore saved position OR execute drive_after_close,
                # but only once "closed" has held for the configured time.
                delay = _debounce_seconds(shutter)
                if delay <= 0:
                    # No task, no await: exactly the order of events we had
                    # before the debounce existed.
                    _apply_window_closed(shutter, cover_entity, pos_closed)
                else:
                    cancel_window_close(data, cover_entity)
                    data.setdefault("_window_close_tasks", {})[cover_entity] = (
                        hass.async_create_task(
                            _delayed_close(shutter, cover_entity, pos_closed, delay)
                        )
                    )

    for window_id in window_to_shutters:
        unsub = async_track_state_change_event(
            hass, window_id, _on_window_state_change
        )
        if unsub:
            data["_window_unsubs"].append(unsub)
        _LOGGER.debug("Tracking window %s for shutter trigger", window_id)
