"""Geloeschte Bereiche und Rollladen lassen ihre Entitaeten stehen.

bjoerg im Forum (Spook-Meldung): fuenf Shutter-Pilot-Entitaeten, die "nie
aufgetaucht sind und daher nicht mehr existieren" – darunter zweimal dieselbe
mit `_2` am Ende. Das ist die Folge, nicht die Ursache: Home Assistant behaelt
den Registereintrag, wenn eine Entitaet einmal existiert hat. Wer eine Markise
loescht und neu anlegt, bekommt deshalb `..._2`, waehrend die Konfiguration
weiter die alte entity_id traegt.

`delete_area` raeumte bis 2.18.0 nur den Automatik-Schalter auf,
`delete_shutter` gar nichts.

Bewusst ohne echtes Setup: der WebSocket-Befehl braucht nur den Entry, ein
hingestelltes Laufzeit-Dict und das Register.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import (
    _area_registry_uids,
    _shutter_registry_uids,
    _ws_delete_area,
    _ws_delete_shutter,
)
from custom_components.shutter_pilot.const import (
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
)

AREA_ID = "balkon"
COVER = "cover.markise_balkon"


class _User:
    def __init__(self, is_admin: bool = True) -> None:
        self.is_admin = is_admin
        self.permissions = None


class _Connection:
    """Nimmt entgegen, was der Befehl zurueckmeldet.

    `user` braucht es, weil beide Befehle `@websocket_api.require_admin`
    tragen – der Dekorator liest ihn, bevor die Funktion ueberhaupt laeuft.
    """

    def __init__(self, is_admin: bool = True) -> None:
        self.user = _User(is_admin)
        self.result = None
        self.error = None

    def send_result(self, _id, payload=None):
        self.result = payload

    def send_error(self, _id, code, message):
        self.error = (code, message)


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_AREAS: [{CONF_AREA_ID: AREA_ID, CONF_AREA_NAME: "Balkon"}],
            CONF_SHUTTERS: [{CONF_COVER_ENTITY_ID: COVER, CONF_NAME: "Markise Balkon"}],
        },
    )
    entry.add_to_hass(hass)
    # `_find_entry_data` erkennt den Entry am Schluessel "shutters".
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"shutters": []}
    return entry


def _register(hass, uids) -> list[str]:
    registry = er.async_get(hass)
    return [
        registry.async_get_or_create(domain, DOMAIN, uid).entity_id
        for domain, uid in uids
    ]


async def _run(hass, handler, msg, is_admin: bool = True):
    """Den Befehl so aufrufen, wie die WebSocket-API es tut.

    `@websocket_api.async_response` macht aus der Coroutine einen *synchronen*
    Handler, der die eigentliche Arbeit als Hintergrundtask einreiht – ein
    `await handler(...)` bekaeme deshalb None zurueck. Also aufrufen und dann
    die Schleife leerlaufen lassen.

    Der Reload braucht ein echtes Setup und ist hier nicht die Frage;
    AsyncMock, weil sein Rueckgabewert direkt in `hass.async_create_task()`
    wandert und awaitbar sein muss.
    """
    connection = _Connection(is_admin)
    with patch(
        "custom_components.shutter_pilot._reload_entry_delayed",
        new_callable=AsyncMock,
    ):
        handler(hass, connection, {"id": 1, **msg})
        await hass.async_block_till_done()
    return connection


class TestDeleteArea:
    async def test_every_entity_of_the_area_goes(self, hass, entry):
        ids = _register(hass, _area_registry_uids(entry, AREA_ID))
        assert len(ids) == 4
        registry = er.async_get(hass)

        conn = await _run(hass, _ws_delete_area, {"area_id": AREA_ID})
        assert conn.error is None

        left = [eid for eid in ids if registry.async_get(eid) is not None]
        assert left == [], f"stehen geblieben: {left}"

    async def test_a_foreign_entity_is_left_alone(self, hass, entry):
        registry = er.async_get(hass)
        other = registry.async_get_or_create(
            "switch", DOMAIN, f"{entry.entry_id}_auto_area_wohnzimmer"
        ).entity_id

        await _run(hass, _ws_delete_area, {"area_id": AREA_ID})
        assert registry.async_get(other) is not None


class TestDeleteShutter:
    async def test_switch_and_guard_sensor_go(self, hass, entry):
        ids = _register(hass, _shutter_registry_uids(entry, COVER))
        assert len(ids) == 2
        registry = er.async_get(hass)

        conn = await _run(hass, _ws_delete_shutter, {"index": 0})
        assert conn.error is None

        left = [eid for eid in ids if registry.async_get(eid) is not None]
        assert left == [], f"stehen geblieben: {left}"

    async def test_a_shutter_without_a_guard_sensor_is_fine(self, hass, entry):
        """Ein Rollladen hat keinen Sperre-Binaersensor – kein Fehler."""
        registry = er.async_get(hass)
        switch_id = registry.async_get_or_create(
            "switch", DOMAIN, _shutter_registry_uids(entry, COVER)[0][1]
        ).entity_id

        conn = await _run(hass, _ws_delete_shutter, {"index": 0})
        assert conn.error is None
        assert registry.async_get(switch_id) is None

    async def test_an_index_out_of_range_removes_nothing(self, hass, entry):
        ids = _register(hass, _shutter_registry_uids(entry, COVER))
        registry = er.async_get(hass)

        conn = await _run(hass, _ws_delete_shutter, {"index": 7})
        assert conn.error is None

        left = [eid for eid in ids if registry.async_get(eid) is not None]
        assert len(left) == 2, "ein fehlgegriffener Index darf nichts entfernen"


class TestPermissions:
    """Beide Befehle sind schreibend und muessen Admin verlangen."""

    async def test_a_non_admin_cannot_delete_a_shutter(self, hass, entry):
        ids = _register(hass, _shutter_registry_uids(entry, COVER))
        registry = er.async_get(hass)

        # `require_admin` wirft im Hintergrundtask; die Ausnahme kommt beim
        # Leerlaufen der Schleife heraus.
        from homeassistant.exceptions import Unauthorized

        with pytest.raises(Unauthorized):
            await _run(hass, _ws_delete_shutter, {"index": 0}, is_admin=False)

        left = [eid for eid in ids if registry.async_get(eid) is not None]
        assert len(left) == 2, "ohne Adminrechte darf nichts entfernt werden"
