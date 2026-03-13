"""Brightness sensor logic - React to lux levels for shutters."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_GROUP_UP,
    CONF_GROUP_DOWN,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_BRIGHTNESS_TRIGGER,
    CONF_BRIGHTNESS_ENTITY_ID,
    CONF_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_BRIGHTNESS_UP_THRESHOLD,
    CONF_BRIGHTNESS_DOWN_TIME,
    CONF_BRIGHTNESS_UP_TIME,
    CONF_BRIGHTNESS_IGNORE_TIME,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_AUTO_LIVING,
    CONF_AUTO_SLEEP,
    CONF_AUTO_CHILDREN,
    CONF_DRIVE_DELAY,
    DEFAULT_DRIVE_DELAY,
    BRIGHTNESS_OFF,
    BRIGHTNESS_UP,
    BRIGHTNESS_DOWN,
    BRIGHTNESS_BOTH,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action
from .scheduler import is_within_group_up_schedule_window

_LOGGER = logging.getLogger(__name__)


def _parse_time(tstr: str | None) -> time:
    """Parse HH:MM string to time, robust gegen ungültige Werte."""
    try:
        parts = str(tstr or "16:00").strip().split(":")
        if len(parts) >= 2:
            return time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError, TypeError):
        pass
    return time(16, 0)  # default 16:00


def _current_time_in_range(
    now: datetime,
    up_time: time,
    down_time: time,
) -> tuple[bool, bool]:
    """Return (is_up_window, is_down_window).
    is_up_window: true if we're in the "up" time window (morning to afternoon)
    is_down_window: true if we're in the "down" time window (afternoon onwards)
    """
    now_t = now.time()
    if up_time <= down_time:
        is_up = up_time <= now_t < down_time
        is_down = now_t >= down_time or now_t < up_time
    else:
        is_up = now_t >= up_time or now_t < down_time
        is_down = down_time <= now_t < up_time
    return is_up, is_down


def _is_auto_enabled(hass: HomeAssistant, opts: dict, group: str) -> bool:
    """True if automation is enabled for this group."""
    key = {GROUP_LIVING: CONF_AUTO_LIVING, GROUP_SLEEP: CONF_AUTO_SLEEP, GROUP_CHILDREN: CONF_AUTO_CHILDREN}.get(group)
    if not key:
        return True
    entity_id = str(opts.get(key) or "").strip()
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if not state:
        return True
    return str(state.state).lower() in ("on", "true", "1")


async def setup_brightness_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up brightness sensor listener."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    # Gemeinsame Verzögerung zwischen Rollläden (Sekunden),
    # konsistent mit Scheduler/Services.
    raw_delay = entry.options.get(
        CONF_DRIVE_DELAY,
        data.get("drive_delay", DEFAULT_DRIVE_DELAY),
    )
    try:
        drive_delay = max(0, int(raw_delay))
    except (TypeError, ValueError):
        drive_delay = DEFAULT_DRIVE_DELAY

    # Clean up previous listeners
    for unsub in data.get("_brightness_unsubs", []):
        unsub()
    data["_brightness_unsubs"] = []
    # Gemeinsame Sperren mit Scheduler/Elevation: Rollladen in dieser Phase schon automatisch bewegt.
    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())
    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    pending_up = data.setdefault("_pending_up", {})

    raw_brightness_entity = entry.options.get(CONF_BRIGHTNESS_ENTITY_ID, "")
    brightness_entity = str(raw_brightness_entity or "").strip()
    if not brightness_entity:
        _LOGGER.debug("No brightness entity configured, skipping")
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in brightness listener: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    opts = entry.options

    raw_down = entry.options.get(CONF_BRIGHTNESS_DOWN_THRESHOLD, 400)
    raw_up = entry.options.get(CONF_BRIGHTNESS_UP_THRESHOLD, 500)
    try:
        down_threshold = int(raw_down)
    except (TypeError, ValueError):
        _LOGGER.warning(
            "Invalid brightness down threshold %r, falling back to 400", raw_down
        )
        down_threshold = 400
    try:
        up_threshold = int(raw_up)
    except (TypeError, ValueError):
        _LOGGER.warning(
            "Invalid brightness up threshold %r, falling back to 500", raw_up
        )
        up_threshold = 500

    down_time_str = entry.options.get(CONF_BRIGHTNESS_DOWN_TIME, "16:00") or "16:00"
    up_time_str = entry.options.get(CONF_BRIGHTNESS_UP_TIME, "05:00") or "05:00"
    down_time = _parse_time(down_time_str)
    up_time = _parse_time(up_time_str)
    ignore_time = bool(entry.options.get(CONF_BRIGHTNESS_IGNORE_TIME, True))

    shutters_down = [s for s in shutters if s.get(CONF_BRIGHTNESS_TRIGGER) in (BRIGHTNESS_DOWN, BRIGHTNESS_BOTH)]
    shutters_up = [s for s in shutters if s.get(CONF_BRIGHTNESS_TRIGGER) in (BRIGHTNESS_UP, BRIGHTNESS_BOTH)]

    async def _set_cover_position_with_delay(
        hass: HomeAssistant,
        entity_id: str,
        position: float,
        reason: str,
        delay: int,
        index: int,
    ) -> None:
        if delay > 0 and index > 0:
            await asyncio.sleep(delay * index)
        await _set_cover_position(hass, entity_id, position, reason)

    @callback
    def _on_brightness_change(entity_id: str, old_state: Any, new_state: Any) -> None:
        if new_state is None or new_state.state in (None, "unknown", "unavailable"):
            return

        try:
            lux = float(new_state.state)
        except (TypeError, ValueError):
            return

        now = datetime.now()
        if ignore_time:
            is_up_window, is_down_window = True, True
        else:
            is_up_window, is_down_window = _current_time_in_range(now, up_time, down_time)

        handled_groups_down: set[str] = set()
        handled_groups_up: set[str] = set()

        # Down-Logik: lux <= down_threshold (z. B. „abends zu“).
        # Wichtig: Bei überlappenden Schwellen (Hoch 10 / Runter 25) würde sonst
        # morgens bei 12–25 Lux ständig „Runter“ gewinnen und Oszillation erzeugen.
        # Daher: Wenn „Zeitfenster ignorieren“ aktiv ist, nur nach der globalen
        # Runter-Zeit (Abends) schließen – morgens nie per Lux „runter“ fahren.
        now_t = now.time()
        evening_only_down = ignore_time and now_t < down_time
        if evening_only_down:
            # Vor Runter-Zeit: keine Abwärts-Fahrt per Helligkeit (nur Hoch möglich).
            pass
        elif is_down_window and lux <= down_threshold and shutters_down:
            data["brightness_down"] = True
            idx = 0
            for shutter in shutters_down:
                grp = shutter.get(CONF_GROUP_DOWN, GROUP_LIVING)
                if not _is_auto_enabled(hass, opts, grp):
                    continue
                cover_entity = shutter[CONF_COVER_ENTITY_ID]
                if cover_entity in covers_driven_down:
                    # In dieser Dunkel-Phase schon automatisch runter gefahren (oder Scheduler/Elevation).
                    continue
                pos = shutter.get(CONF_POSITION_CLOSED, 0)
                drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
                if drive_after and is_window_open_or_tilted(hass, shutter):
                    data.setdefault("drive_after_close_pending", {})[cover_entity] = {
                        "position": pos,
                        "reason": "Brightness down",
                        "shutter": shutter,
                    }
                    _LOGGER.info("Brightness down: %s Fenster offen – drive_after_close", cover_entity)
                    continue
                pos = get_effective_close_position(hass, shutter, pos)
                hass.async_create_task(
                    _set_cover_position_with_delay(
                        hass,
                        cover_entity,
                        pos,
                        "Brightness down",
                        drive_delay,
                        idx,
                    )
                )
                idx += 1
                covers_driven_down.add(cover_entity)
                covers_driven_up.discard(cover_entity)
                if grp not in handled_groups_down:
                    handled_groups_down.add(grp)
                    hass.async_create_task(
                        run_group_light_action(hass, entry, grp, "down")
                    )

        # Hoch-Logik: lux > up_threshold. Pro Rollladen zusätzlich prüfen, ob der
        # zugeordnete Bereich (group_up) laut Zeitplan gerade im Hoch-Fenster ist.
        elif is_up_window and lux > up_threshold and shutters_up:
            data["brightness_down"] = False
            idx = 0
            for shutter in shutters_up:
                grp = shutter.get(CONF_GROUP_UP, GROUP_LIVING)
                if not _is_auto_enabled(hass, opts, grp):
                    continue
                # Zeitplan pro Bereich: z. B. Schlafzimmer erst ab 07:00 hoch –
                # vorher kein Hochfahren per Helligkeit, sonst nur Scheduler/ manuell.
                today = now.date()
                is_pending = pending_up.get(grp) == today
                if not is_pending and not is_within_group_up_schedule_window(opts, grp, now):
                    continue
                cover_entity = shutter[CONF_COVER_ENTITY_ID]
                if cover_entity in covers_driven_up:
                    # In dieser Hell-Phase schon automatisch hoch gefahren (z. B. Scheduler oder Helligkeit).
                    continue
                pos = shutter.get(CONF_POSITION_OPEN, 100)
                hass.async_create_task(
                    _set_cover_position_with_delay(
                        hass,
                        cover_entity,
                        pos,
                        "Brightness up",
                        drive_delay,
                        idx,
                    )
                )
                idx += 1
                covers_driven_up.add(cover_entity)
                covers_driven_down.discard(cover_entity)
                if grp not in handled_groups_up:
                    handled_groups_up.add(grp)
                    hass.async_create_task(
                        run_group_light_action(hass, entry, grp, "up")
                    )
                    # Pending erfüllt – nach erstem erfolgreichen Hochfahren für Gruppe löschen.
                    if is_pending:
                        pending_up.pop(grp, None)

    unsub = async_track_state_change(
        hass, brightness_entity, _on_brightness_change
    )
    if unsub:
        data["_brightness_unsubs"].append(unsub)
    _LOGGER.info(
        "Brightness listener: %s (down<=%d, up>%d)",
        brightness_entity, down_threshold, up_threshold,
    )


async def _set_cover_position(
    hass: HomeAssistant, entity_id: str, position: float, reason: str
) -> None:
    try:
        await hass.services.async_call(
            "cover", "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )
        _LOGGER.debug("%s: Set %s to %d%%", reason, entity_id, int(position))
    except Exception as e:
        _LOGGER.warning("Failed to set %s: %s", entity_id, e)
