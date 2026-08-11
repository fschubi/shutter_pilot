"""Denselben Rollladen zweimal anlegen – der Riegel und der Hinweis.

Forum, Viktor: er hatte sich verklickt und ein Rollo zweimal angelegt, in
verschiedenen Bereichen. Jeder Eintrag entscheidet fuer sich, die beiden
widersprechen sich, und der Rollladen fuhr im Minutentakt hin und her.
Aufgefallen ist es ihm erst im Export.

Der Riegel liegt auf dem Server: das Panel prueft zwar auch, aber die Grenze
ist der WebSocket-Befehl. Bestehende Konfigurationen tragen den Doppeleintrag
weiter – die benennt der Export.
"""

from __future__ import annotations

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
)
from custom_components.shutter_pilot.export import async_build_export

COVER = "cover.wohnzimmer"

AREA_A = {
    CONF_AREA_ID: "wohnen",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_DRIVE_DELAY: 0,
}
AREA_B = {
    CONF_AREA_ID: "schlafen",
    CONF_AREA_NAME: "Schlafbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_DRIVE_DELAY: 0,
}


def _shutter(area_id: str, name: str, cover: str = COVER) -> dict:
    return {
        CONF_COVER_ENTITY_ID: cover,
        CONF_NAME: name,
        CONF_AREA_UP_ID: area_id,
        CONF_AREA_DOWN_ID: area_id,
    }


async def _setup(hass, shutters: list) -> MockConfigEntry:
    hass.states.async_set(
        COVER, "open", {"current_position": 100, "supported_features": 15}
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA_A, AREA_B], CONF_SHUTTERS: shutters},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def _save(client, shutter: dict, index=None) -> dict:
    msg: dict = {"id": 1, "type": "shutter_pilot/save_shutter", "shutter": shutter}
    if index is not None:
        msg["index"] = index
    await client.send_json(msg)
    return await client.receive_json()


class TestSaveShutterRejectsDuplicates:
    async def test_second_entry_for_the_same_cover_is_refused(
        self, hass, hass_ws_client
    ):
        entry = await _setup(hass, [_shutter("wohnen", "Wohnzimmer")])
        client = await hass_ws_client(hass)

        response = await _save(client, _shutter("schlafen", "Schlafzimmer"))
        assert response["success"] is False
        assert response["error"]["code"] == "duplicate_cover"
        # Der Name des bestehenden Eintrags gehoert hinein: sonst sucht man
        # in einer langen Liste, welcher der beiden gemeint ist.
        assert "Wohnzimmer" in response["error"]["message"]
        assert len(entry.options[CONF_SHUTTERS]) == 1

    async def test_editing_the_existing_entry_still_works(self, hass, hass_ws_client):
        """Beim Bearbeiten ist der eigene Eintrag natuerlich derselbe Rollladen."""
        entry = await _setup(hass, [_shutter("wohnen", "Wohnzimmer")])
        client = await hass_ws_client(hass)

        changed = _shutter("schlafen", "Wohnzimmer neu")
        response = await _save(client, changed, index=0)
        assert response["success"] is True
        assert entry.options[CONF_SHUTTERS][0][CONF_NAME] == "Wohnzimmer neu"

    async def test_a_different_cover_is_added_normally(self, hass, hass_ws_client):
        entry = await _setup(hass, [_shutter("wohnen", "Wohnzimmer")])
        client = await hass_ws_client(hass)

        response = await _save(
            client, _shutter("schlafen", "Schlafzimmer", cover="cover.schlafzimmer")
        )
        assert response["success"] is True
        assert len(entry.options[CONF_SHUTTERS]) == 2

    async def test_a_shutter_without_a_cover_is_not_a_duplicate(
        self, hass, hass_ws_client
    ):
        """Zwei leere Felder sind kein Doppeleintrag, sondern ein halbes Formular."""
        entry = await _setup(hass, [{CONF_NAME: "Ohne Entitaet"}])
        client = await hass_ws_client(hass)

        response = await _save(client, {CONF_NAME: "Auch ohne"})
        assert response["success"] is True
        assert len(entry.options[CONF_SHUTTERS]) == 2


class TestExportNamesExistingDuplicates:
    async def test_the_report_says_it_twice_over(self, hass):
        entry = await _setup(
            hass,
            [_shutter("wohnen", "Wohnzimmer"), _shutter("schlafen", "Wohnzimmer 2")],
        )
        text = (await async_build_export(hass, entry))["markdown"]
        assert text.count("ist **2-mal** angelegt") == 2
        assert "Minutentakt" in text

    async def test_a_clean_configuration_gets_no_such_note(self, hass):
        entry = await _setup(
            hass,
            [
                _shutter("wohnen", "Wohnzimmer"),
                _shutter("schlafen", "Schlafzimmer", cover="cover.schlafzimmer"),
            ],
        )
        text = (await async_build_export(hass, entry))["markdown"]
        assert "angelegt" not in text
