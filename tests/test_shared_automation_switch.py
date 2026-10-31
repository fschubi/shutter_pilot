"""Rollladen und Dachfenster teilten sich einen Automatik-Schalter
(Fatmax, community.simon42.com/90112/205 und /218).

Sein Export zeigt es: beide Eintraege tragen `shutter_auto_entity_id:
switch.shutter_pilot_rollladen_obergeschoss_schlafzimmer_dff`, obwohl das
Dachfenster ein eigenes Cover hat. Der Schluessel wird nur vom Schalter selbst
gesetzt und nur, wenn er leer ist; er konnte aber an einem Eintrag haengen
bleiben, dessen Cover-Entitaet spaeter getauscht wurde (oder der als Dachfenster
uebernommen wurde). Das Panel liest den Schalter ueber diesen Schluessel, und
das Umschalten ruft den Dienst auf genau diese Entitaet - also schalteten beide
Eintraege zusammen. Jetzt heilt der Schalter den Schluessel beim Start, das
Speichern setzt ihn aus der Registry, und das Umschalten fragt die Registry."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import (
    _own_automation_switch,
    _ws_save_shutter,
    _ws_set_shutter_automation,
)
from custom_components.shutter_pilot.const import (
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTER_AUTO_ENTITY_ID,
    CONF_SHUTTERS,
    DOMAIN,
)

COVER = "cover.velux_external_cover_roller_shutter_3"
WINDOW = "cover.velux_window_roof_window_3"


async def _setup(hass, shutters: list[dict]):
    for c in (COVER, WINDOW):
        hass.states.async_set(c, "open", {"current_position": 100, "supported_features": 15})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [{CONF_AREA_ID: "sleep", CONF_AREA_NAME: "Schlafen"}],
            CONF_SHUTTERS: shutters,
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def _keys(entry) -> dict[str, str]:
    return {
        s[CONF_COVER_ENTITY_ID]: s.get(CONF_SHUTTER_AUTO_ENTITY_ID, "")
        for s in entry.options[CONF_SHUTTERS]
    }


class TestTheStoredKeyHeals:
    async def test_two_entries_pointing_at_one_switch_each_get_their_own(self, hass):
        stale = "switch.shutter_pilot_rollladen_obergeschoss_schlafzimmer_dff"
        entry = await _setup(
            hass,
            [
                {CONF_COVER_ENTITY_ID: COVER, CONF_NAME: "Obergeschoss DFF Rollladen",
                 CONF_SHUTTER_AUTO_ENTITY_ID: stale},
                {CONF_COVER_ENTITY_ID: WINDOW, CONF_NAME: "Obergeschoss DFF Fenster",
                 "device_kind": "window", CONF_SHUTTER_AUTO_ENTITY_ID: stale},
            ],
        )
        keys = _keys(entry)
        assert keys[COVER] != keys[WINDOW]
        assert keys[COVER] == _own_automation_switch(hass, entry, COVER)
        assert keys[WINDOW] == _own_automation_switch(hass, entry, WINDOW)
        assert hass.states.get(keys[COVER]) is not None
        assert hass.states.get(keys[WINDOW]) is not None

    async def test_a_correct_key_is_left_alone(self, hass):
        entry = await _setup(
            hass,
            [{CONF_COVER_ENTITY_ID: COVER, CONF_NAME: "Rollladen"}],
        )
        first = _keys(entry)[COVER]
        assert first  # der Schalter hat ihn beim ersten Start gesetzt

        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        assert _keys(entry)[COVER] == first


class _User:
    is_admin = True
    permissions = None


class _Connection:
    def __init__(self):
        self.user = _User()
        self.result = None
        self.error = None

    def send_result(self, _id, payload=None):
        self.result = payload

    def send_error(self, _id, code, message):
        self.error = (code, message)


async def _run(hass, handler, msg):
    conn = _Connection()
    with patch(
        "custom_components.shutter_pilot._reload_entry_delayed",
        new_callable=AsyncMock,
    ):
        handler(hass, conn, {"id": 1, **msg})
        await hass.async_block_till_done()
    return conn


class TestToggleAndSaveUseTheOwnSwitch:
    async def test_toggling_one_does_not_touch_the_other(self, hass):
        stale = "switch.shutter_pilot_rollladen_obergeschoss_schlafzimmer_dff"
        entry = await _setup(
            hass,
            [
                {CONF_COVER_ENTITY_ID: COVER, CONF_NAME: "Obergeschoss DFF Rollladen",
                 CONF_SHUTTER_AUTO_ENTITY_ID: stale},
                {CONF_COVER_ENTITY_ID: WINDOW, CONF_NAME: "Obergeschoss DFF Fenster",
                 "device_kind": "window", CONF_SHUTTER_AUTO_ENTITY_ID: stale},
            ],
        )
        own_cover = _own_automation_switch(hass, entry, COVER)
        own_window = _own_automation_switch(hass, entry, WINDOW)
        assert hass.states.get(own_cover).state == "on"
        assert hass.states.get(own_window).state == "on"

        conn = await _run(
            hass, _ws_set_shutter_automation,
            {"cover_entity_id": WINDOW, "enabled": False},
        )

        assert conn.error is None
        assert hass.states.get(own_window).state == "off"
        assert hass.states.get(own_cover).state == "on", (
            "das Dachfenster hat den Schalter des Rollladens mitgenommen"
        )

    async def test_saving_with_another_cover_drops_the_old_switch(self, hass):
        entry = await _setup(
            hass,
            [{CONF_COVER_ENTITY_ID: COVER, CONF_NAME: "Rollladen"}],
        )
        old_switch = _keys(entry)[COVER]
        stored = dict(entry.options[CONF_SHUTTERS][0])
        assert stored[CONF_SHUTTER_AUTO_ENTITY_ID] == old_switch

        # Im Panel: den Eintrag auf das Dachfenster umgestellt, Rest unveraendert.
        edited = {**stored, CONF_COVER_ENTITY_ID: WINDOW, "device_kind": "window"}
        conn = await _run(
            hass, _ws_save_shutter, {"shutter": edited, "index": 0}
        )

        assert conn.error is None
        saved = entry.options[CONF_SHUTTERS][0]
        assert saved[CONF_COVER_ENTITY_ID] == WINDOW
        assert saved.get(CONF_SHUTTER_AUTO_ENTITY_ID, "") != old_switch, (
            "der neue Eintrag traegt weiter den Schalter des alten Covers"
        )

    async def test_saving_the_same_cover_keeps_its_switch(self, hass):
        entry = await _setup(
            hass,
            [{CONF_COVER_ENTITY_ID: COVER, CONF_NAME: "Rollladen"}],
        )
        own = _keys(entry)[COVER]
        edited = {**entry.options[CONF_SHUTTERS][0], "position_open": 90}

        await _run(hass, _ws_save_shutter, {"shutter": edited, "index": 0})

        assert entry.options[CONF_SHUTTERS][0][CONF_SHUTTER_AUTO_ENTITY_ID] == own
