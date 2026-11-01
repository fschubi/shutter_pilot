"""Track cover positions and restore after Home Assistant restart."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_COVER_ENTITY_ID, CONF_SHUTTERS, CONF_TILT_HAND_DETECT, DOMAIN
from .helpers import (
    apply_covers_driven_from_persisted,
    get_cover_current_position,
    commanded_position,
    commanded_tilt,
    forget_commanded_position,
    forget_drive_after_close,
    forget_window_cycle,
    is_recent_automation,
    note_manual_position,
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
_TARGET_NEAR_PCT = 3.0
# Winkel: ein KNX-Aktor meldet nach einer Fahrt 2 % statt 0 % und kurz Lamellen 0.
# Deshalb weite Toleranz zum befohlenen Winkel und eine Wartezeit nach jeder
# Hoehenaenderung, bevor ein anderer Winkel als Handverstellung gilt.
TILT_HAND_TOLERANCE_PCT = 8.0
TILT_SETTLE_SEC = 15.0


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
    shutter_by_cover = {
        str(s.get(CONF_COVER_ENTITY_ID) or "").strip(): s
        for s in shutters
        if isinstance(s, dict) and str(s.get(CONF_COVER_ENTITY_ID) or "").strip()
    }

    store = get_position_store(hass, entry.entry_id)
    last_positions: dict[str, float] = data["last_positions"]
    pending: set[str] = data.setdefault("pending_automation_covers", set())

    def _reported_position(state) -> float | None:
        if state is None or state.state in ("unavailable", "unknown"):
            return None
        cur = (state.attributes or {}).get("current_position")
        if cur is None:
            return None
        try:
            return float(cur)
        except (TypeError, ValueError):
            return None

    def _reported_tilt(state) -> float | None:
        if state is None or state.state in ("unavailable", "unknown"):
            return None
        cur = (state.attributes or {}).get("current_tilt_position")
        try:
            return None if cur is None else float(cur)
        except (TypeError, ValueError):
            return None

    def _note_hand_tilt(event, entity_id: str, position: float) -> bool:
        """Book a slat angle somebody changed by hand. True = this event is handled.

        Only for shutters that opted in (`tilt_hand_detect`), and only for an
        event where the height stayed put: the tracker's early return for an
        unchanged position is what kept slat-only changes invisible so far.
        """
        shutter = shutter_by_cover.get(entity_id)
        if shutter is None or not shutter.get(CONF_TILT_HAND_DETECT, False):
            return False
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        old_position = _reported_position(old_state)
        now = time.monotonic()
        changed_at = data.setdefault("_height_changed_at", {})
        if old_position is None or old_position != position:
            changed_at[entity_id] = now
            return False
        new_tilt, old_tilt = _reported_tilt(new_state), _reported_tilt(old_state)
        if new_tilt is None or old_tilt is None or new_tilt == old_tilt:
            return False
        if new_state.state in ("opening", "closing"):
            return True
        if now - changed_at.get(entity_id, float("-inf")) < TILT_SETTLE_SEC:
            return True
        if entity_id in pending or is_recent_automation(data, entity_id):
            return True
        target = commanded_tilt(data, entity_id)
        if target is not None and abs(new_tilt - target) <= TILT_HAND_TOLERANCE_PCT:
            return True
        data.get("commanded_tilts", {}).pop(entity_id, None)
        data.setdefault("_hand_moved_at", {})[entity_id] = now
        forget_drive_after_close(hass, entry, data, entity_id)
        forget_window_cycle(data, entity_id)
        hass.async_create_task(
            store.async_set_position(entity_id, position, SOURCE_MANUAL)
        )
        _LOGGER.debug(
            "Slat angle changed by hand: %s -> %.0f%% (was %.0f%%)",
            entity_id, new_tilt, old_tilt,
        )
        return True

    @callback
    def _on_cover_state_change(event) -> None:
        new_state = event.data.get("new_state")
        entity_id = str(event.data.get("entity_id") or "")
        if new_state is None or not entity_id:
            return
        position = _reported_position(new_state)
        if position is None:
            return
        if _note_hand_tilt(event, entity_id, position):
            return

        last_positions[entity_id] = position

        target = commanded_position(data, entity_id)
        if entity_id in pending or is_recent_automation(data, entity_id):
            source = SOURCE_AUTOMATION
            pending.discard(entity_id)
        elif target is not None and abs(position - target) <= _TARGET_NEAR_PCT:
            # Die Karenz von 90 s kennt keine langsamen Antriebe, Nachmeldungen
            # und Reloads. Meldet er eine Position, die dem zuletzt gesendeten
            # Ziel entspricht (30 statt 31 %), war das unsere Fahrt – als
            # Handfahrt gebucht blockierte sie morgens das Hochfahren und
            # loeschte den Fensterzyklus (bjoerg).
            source = SOURCE_AUTOMATION
        else:
            # Der Bus meldet jede Aenderung am Zustandsobjekt, nicht nur eine
            # Fahrt: ein Funkpegel, ein Batteriewert, ein Fahrzustand ohne
            # neue Position. Steht der Rollladen noch genau da, wo er vorher
            # stand, hat ihn niemand bewegt - dann gibt es hier auch keine
            # Handfahrt zu verbuchen, keine Vormerkung aufzuheben und keine
            # Quelle im Speicher auf "manual" umzuschreiben (was die naechste
            # automatische Fahrt als Uebersteuerung gelesen haette).
            old_position = _reported_position(event.data.get("old_state"))
            if old_position is not None and old_position == position:
                return
            source = SOURCE_MANUAL
            # Unser zuletzt gesendetes Ziel sagt ab jetzt nichts mehr darueber,
            # wo dieser Rollladen steht.
            forget_commanded_position(data, entity_id)
            # A shutter somebody closed or opened by hand is down or up, and
            # the schedule has to see that. Without it one blocked direction
            # freezes the other: the evening close is skipped because the
            # shutter still counts as "driven down" from a morning that never
            # came.
            shutter = shutter_by_cover.get(entity_id)
            if shutter is not None:
                note_manual_position(data, shutter, position)
            # A drive that was only waiting for the window to close is a
            # decision from whenever it was queued - a hand move on this
            # exact cover since then is a newer, more direct decision and
            # supersedes it. Without this an old evening close could fire
            # hours later, against a shutter somebody had since driven
            # somewhere else entirely by hand.
            forget_drive_after_close(hass, entry, data, entity_id)
            # Same reasoning for the window trigger's restore marker: the
            # height it noted when the window opened describes a cover nobody
            # had touched since. After a hand move it describes nothing, and
            # acting on it when the window closes drove a shutter opened by
            # hand in the morning back down to its night position (c.radi).
            forget_window_cycle(data, entity_id)

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

    await store.async_load()
    # Der Stand von der Platte, nicht der laufende: `async_load()` gibt dasselbe
    # Dict zurueck, das der Tracker beschreibt. Meldet ein Cover nach dem Start
    # zuerst eine Standardposition (100 %), steht sie dort schon als "manual"
    # drin, und der Vergleich unten sieht 100 gegen 100 - die Wiederherstellung
    # war damit genau in dem Fall wirkungslos, fuer den es sie gibt.
    covers = store.get_loaded_snapshot()
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
            # Die falsche Startmeldung wurde vom Tracker als Handfahrt
            # verbucht (100 % = "oben"). Ohne diese Korrektur gilt der
            # Rollladen danach als hochgefahren, und der naechste Morgen
            # ueberspringt ihn.
            note_manual_position(data, shutter_by_cover[cover_id], stored_pos)
            restored_any = True

        if not restored_any:
            break
        if attempt < STARTUP_RESTORE_MAX_RETRIES:
            await asyncio.sleep(STARTUP_RESTORE_RETRY_SEC)

    apply_covers_driven_from_persisted(hass, entry, shutters, store)
    _LOGGER.info("Startup restore finished")
