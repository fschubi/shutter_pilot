"""Die Reihenfolge der Rollllaeden im Bereich festlegen (DerTomm, GitHub #17).

Die Fahrten laufen in der Reihenfolge der gespeicherten Liste und werden um
die Bereichsverzoegerung gestaffelt. Bisher war das die Reihenfolge, in der
die Rollllaeden angelegt wurden - ohne Weg, sie zu aendern. Der Befehl
`reorder_shutters` speichert eine neue Reihenfolge; im Dashboard schiebt man
die Rollllaeden mit Pfeilen."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import (
    _reordered_shutters,
    _ws_reorder_shutters,
)
from custom_components.shutter_pilot.const import (
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
)


def _s(cover: str) -> dict:
    return {CONF_COVER_ENTITY_ID: cover, CONF_NAME: cover}


def _covers(shutters: list) -> list[str]:
    return [s[CONF_COVER_ENTITY_ID] for s in shutters]


class _User:
    is_admin = True
    permissions = None


class _Connection:
    def __init__(self, is_admin: bool = True) -> None:
        self.user = _User()
        self.user.is_admin = is_admin
        self.result = None
        self.error = None

    def send_result(self, _id, payload=None):
        self.result = payload

    def send_error(self, _id, code, message):
        self.error = (code, message)


class TestTheOrderingFunction:
    def test_named_covers_come_first_in_that_order(self):
        shutters = [_s("cover.a"), _s("cover.b"), _s("cover.c")]
        out = _reordered_shutters(shutters, ["cover.c", "cover.a", "cover.b"])
        assert _covers(out) == ["cover.c", "cover.a", "cover.b"]

    def test_a_partial_request_never_drops_a_shutter(self):
        shutters = [_s("cover.a"), _s("cover.b"), _s("cover.c"), _s("cover.d")]
        out = _reordered_shutters(shutters, ["cover.c"])
        assert _covers(out) == ["cover.c", "cover.a", "cover.b", "cover.d"]

    def test_unknown_and_repeated_names_are_ignored(self):
        shutters = [_s("cover.a"), _s("cover.b")]
        out = _reordered_shutters(shutters, ["cover.zzz", "cover.b", "cover.b"])
        assert _covers(out) == ["cover.b", "cover.a"]

    def test_the_entries_themselves_are_untouched(self):
        shutters = [{**_s("cover.a"), "tilt_enabled": True}, _s("cover.b")]
        out = _reordered_shutters(shutters, ["cover.b", "cover.a"])
        assert out[1] is shutters[0]

    def test_a_legacy_duplicate_is_kept(self):
        shutters = [_s("cover.a"), _s("cover.a"), _s("cover.b")]
        out = _reordered_shutters(shutters, ["cover.b", "cover.a"])
        assert _covers(out) == ["cover.b", "cover.a", "cover.a"]


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_AREAS: [],
            CONF_SHUTTERS: [_s("cover.a"), _s("cover.b"), _s("cover.c")],
        },
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"shutters": []}
    return entry


async def _run(hass, msg, is_admin: bool = True):
    connection = _Connection(is_admin)
    with patch(
        "custom_components.shutter_pilot._reload_entry_delayed",
        new_callable=AsyncMock,
    ) as reload_mock:
        _ws_reorder_shutters(hass, connection, {"id": 1, **msg})
        await hass.async_block_till_done()
    return connection, reload_mock


class TestTheCommand:
    async def test_it_stores_the_new_order_and_reloads(self, hass, entry):
        conn, reload_mock = await _run(
            hass, {"order": ["cover.c", "cover.a", "cover.b"]}
        )
        assert conn.error is None and conn.result["changed"] is True
        assert _covers(entry.options[CONF_SHUTTERS]) == [
            "cover.c", "cover.a", "cover.b",
        ]
        reload_mock.assert_awaited_once()

    async def test_an_unchanged_order_does_not_reload(self, hass, entry):
        """Ein Neuladen setzt die Merker zurueck - ohne Grund nicht."""
        conn, reload_mock = await _run(
            hass, {"order": ["cover.a", "cover.b", "cover.c"]}
        )
        assert conn.result == {"ok": True, "changed": False}
        reload_mock.assert_not_awaited()

    async def test_a_non_admin_is_refused(self, hass, entry):
        """Der Dekorator wirft Unauthorized, die WebSocket-Schicht macht daraus
        den Fehler fuer den Aufrufer - und es wird nichts gespeichert."""
        from homeassistant.exceptions import Unauthorized

        with pytest.raises(Unauthorized):
            await _run(
                hass, {"order": ["cover.c", "cover.a", "cover.b"]}, is_admin=False
            )
        assert _covers(entry.options[CONF_SHUTTERS]) == [
            "cover.a", "cover.b", "cover.c",
        ]
