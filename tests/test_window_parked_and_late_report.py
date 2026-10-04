"""bjoerg (community-smarthome.com/11378/166): zwei Fehler an der Abendfahrt
bei offenem Fenster.

1. Die Abendfahrt parkt den Rollladen bei offenem Fenster auf der
   Lueftungsposition (95 %) und merkt die Vollfahrt vor, startet aber keinen
   Fenstertrigger-Zyklus. „Offen -> gekippt" lief danach ins Leere: die
   Richtungspruefung hielt den Rollladen fuer einen offenen.
2. Der Positions-Mitschreiber hielt eigene Fahrten nur 90 s lang als Automatik
   fest. Eine spaetere Nachmeldung nahe dem gesendeten Ziel (31 statt 30 %)
   wurde als Handfahrt gebucht: Quelle „manual" (blockiert das Hochfahren bei
   manual_override=never) und der Fensterzyklus wurde vergessen."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_WINDOW_VENT_WHILE_OPEN,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import remember_drive_after_close
from custom_components.shutter_pilot.position_store import get_position_store

COVER = "cover.bjoerg_schlafzimmer"
WINDOW = "sensor.bjoerg_fenstergriff"


@pytest.fixture
def calls(hass):
    out: list = []

    async def _handler(call):
        out.append(call.data["position"])
        hass.states.async_set(
            call.data["entity_id"],
            "open",
            {"current_position": call.data["position"], "supported_features": 15},
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return out


async def _setup(hass, start, *, vent_while_open=True):
    hass.states.async_set(
        COVER, "open", {"current_position": start, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "open")
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Schlafzimmer",
        CONF_AREA_UP_ID: "s",
        CONF_AREA_DOWN_ID: "s",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "open",
        CONF_WINDOW_TILTED_STATE: "tilted",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_WHEN_WINDOW_OPEN: 95,
        CONF_POSITION_WHEN_WINDOW_TILTED: 30,
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
        CONF_LOCK_PROTECTION: True,
        CONF_MIN_POSITION_WHEN_OPEN: 95,
        CONF_DRIVE_AFTER_CLOSE: True,
        CONF_WINDOW_VENT_WHILE_OPEN: vent_while_open,
    }
    area = {CONF_AREA_ID: "s", CONF_AREA_NAME: "S", CONF_AREA_MODE: AREA_MODE_NONE}
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [area], CONF_SHUTTERS: [shutter]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id], shutter


def _park(hass, entry, data, shutter):
    remember_drive_after_close(
        hass, entry, data, COVER,
        position=0, tilt=None, reason="Abendfahrt", shutter=shutter,
    )


async def test_parked_at_vent_position_reacts_to_tilted(hass, calls):
    entry, data, shutter = await _setup(hass, 95)
    _park(hass, entry, data, shutter)
    hass.states.async_set(WINDOW, "tilted")
    await hass.async_block_till_done()
    assert calls == [30.0]


async def test_without_vent_while_open_it_stays_put(hass, calls):
    entry, data, shutter = await _setup(hass, 100, vent_while_open=False)
    _park(hass, entry, data, shutter)
    hass.states.async_set(WINDOW, "tilted")
    await hass.async_block_till_done()
    assert calls == []


async def test_open_cover_without_pending_drive_is_not_pulled_down(hass, calls):
    """Tagsueber offen, nichts vorgemerkt: das Fenster zieht ihn nicht herunter."""
    await _setup(hass, 100)
    hass.states.async_set(WINDOW, "tilted")
    await hass.async_block_till_done()
    assert calls == []


async def test_late_report_near_target_stays_automation(hass, calls):
    entry, data, _ = await _setup(hass, 0)
    hass.states.async_set(WINDOW, "closed")
    await hass.async_block_till_done()
    hass.states.async_set(WINDOW, "tilted")
    await hass.async_block_till_done()
    assert calls == [30.0]
    # Karenz laengst vorbei (langsamer Antrieb, Nachmeldung, Reload)
    data["recent_automation_covers"].clear()
    data["pending_automation_covers"].clear()
    hass.states.async_set(
        COVER, "open", {"current_position": 31, "supported_features": 15}
    )
    await hass.async_block_till_done()
    rec = get_position_store(hass, entry.entry_id).get_record(COVER)
    assert rec["source"] == "automation"
    assert data["trigger_actions"].get(COVER) == "triggered"


async def test_real_hand_move_is_still_manual(hass, calls):
    entry, data, _ = await _setup(hass, 0)
    hass.states.async_set(WINDOW, "closed")
    await hass.async_block_till_done()
    hass.states.async_set(WINDOW, "tilted")
    await hass.async_block_till_done()
    data["recent_automation_covers"].clear()
    data["pending_automation_covers"].clear()
    hass.states.async_set(
        COVER, "open", {"current_position": 70, "supported_features": 15}
    )
    await hass.async_block_till_done()
    rec = get_position_store(hass, entry.entry_id).get_record(COVER)
    assert rec["source"] == "manual"
    assert COVER not in data["trigger_actions"]
