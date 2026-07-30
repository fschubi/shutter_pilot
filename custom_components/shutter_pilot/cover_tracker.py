"""Track cover positions and restore after Home Assistant restart."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, CONF_SHUTTERS, CONF_COVER_ENTITY_ID
from .helpers import (
    apply_covers_driven_from_persisted,
    get_cover_current_position,
    is_recent_automation,
    positions_differ_significantly,
    set_cover_position,
)
from .position_store import (
    SOURCE_AUTOMATION,
    SOURCE_MANUAL,
    get_position_store,
)

_LOGGER = logging.getLogger(__name__)

STARTUP_RESTORE_DELAY_SEC = 5
STARTUP_RESTORE_RETRY_SEC = 3
STARTUP_RESTORE_MAX_RETRIES = 3
POSITION_TOLERANCE_PCT = 8.0


def _collect_cover_entity_ids(shutters: list) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for shutter in shutters:
        if not isinstance(shutter, dict):
            continue
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
        if cover and cover not in seen:
            seen.add(cover)
            out.append(cover)
    return out


async def setup_cover_position_tracker(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Listen to cover state changes and persist positions."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_cover_tracker_unsubs", []):
        unsub()
    data["_cover_tracker_unsubs"] = []

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []

    cover_ids = _collect_cover_entity_ids(shutters)
    if not cover_ids:
        return

    store = get_position_store(hass, entry.entry_id)
    last_positions: dict[str, float] = data["last_positions"]
    pending: set[str] = data.setdefault("pending_automation_covers", set())

    @callback
    def _on_cover_state_change(event) -> None:
        new_state = event.data.get("new_state")
        entity_id = str(event.data.get("entity_id") or "")
        if new_state is None or not entity_id:
            return
        if new_state.state in ("unavailable", "unknown"):
            return
        attrs = new_state.attributes or {}
        cur = attrs.get("current_position")
        if cur is None:
            return
        try:
            position = float(cur)
        except (TypeError, ValueError):
            return

        last_positions[entity_id] = position

        if entity_id in pending or is_recent_automation(data, entity_id):
            source = SOURCE_AUTOMATION
            pending.discard(entity_id)
        else:
            source = SOURCE_MANUAL

        hass.async_create_task(
            store.async_set_position(entity_id, position, source)
        )
        _LOGGER.debug(
            "Position saved (%s): %s -> %.0f%%",
            source,
            entity_id,
            position,
        )

    for cover_id in cover_ids:
        unsub = async_track_state_change_event(hass, cover_id, _on_cover_state_change)
        if unsub:
            data["_cover_tracker_unsubs"].append(unsub)

    _LOGGER.debug("Cover position tracker: %d entities", len(cover_ids))


async def async_restore_positions_on_startup(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """After HA start, restore persisted positions if cover integration restored wrong state."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []

    store = get_position_store(hass, entry.entry_id)
    await store.async_load()
    apply_covers_driven_from_persisted(hass, entry, shutters, store)

    covers = await store.async_load()
    if not covers:
        _LOGGER.debug("Startup restore: no persisted positions")
        return

    await asyncio.sleep(STARTUP_RESTORE_DELAY_SEC)

    shutter_by_cover: dict[str, dict] = {}
    for shutter in shutters:
        if not isinstance(shutter, dict):
            continue
        cid = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
        if cid:
            shutter_by_cover[cid] = shutter

    for attempt in range(STARTUP_RESTORE_MAX_RETRIES + 1):
        restored_any = False
        for cover_id, record in covers.items():
            if cover_id not in shutter_by_cover:
                continue
            try:
                stored_pos = float(record.get("position", 0))
            except (TypeError, ValueError):
                continue

            st = hass.states.get(cover_id)
            if st is None or st.state in ("unavailable", "unknown"):
                restored_any = True
                continue

            current = get_cover_current_position(hass, cover_id)
            if current is None:
                continue

            if not positions_differ_significantly(
                current, stored_pos, POSITION_TOLERANCE_PCT
            ):
                continue

            source = str(record.get("source") or SOURCE_MANUAL)
            _LOGGER.info(
                "Startup restore: %s HA=%.0f%% -> persisted %.0f%% (source=%s)",
                cover_id,
                current,
                stored_pos,
                source,
            )
            await set_cover_position(
                hass,
                entry,
                cover_id,
                stored_pos,
                "Startup restore",
                source=SOURCE_AUTOMATION,
            )
            restored_any = True

        if not restored_any:
            break
        if attempt < STARTUP_RESTORE_MAX_RETRIES:
            await asyncio.sleep(STARTUP_RESTORE_RETRY_SEC)

    apply_covers_driven_from_persisted(hass, entry, shutters, store)
    _LOGGER.info("Startup restore finished")
