"""Eine vorgemerkte Nachhol-Fahrt (drive_after_close_pending) darf keine
spaetere manuelle Fahrt ueberleben.

bjoerg (community-smarthome.com/11378/139): das Schlafzimmerfenster stand
offen, die abendliche Zufahrt wurde deshalb vorgemerkt (volle Fahrt auf
position_closed, sobald das Fenster schliesst). Nachts fuhr er per Taster von
Hand auf eine Zwischenposition, morgens von Hand wieder ganz auf. Die
Vormerkung von gestern Abend blieb dabei unberuehrt stehen - schliesst das
Fenster spaeter, voellig unabhaengig vom naechtlichen Geschehen, faehrt der
laengst von Hand wieder geoeffnete Rollladen unerwartet auf die alte
Vormerkung zu. cover_tracker.py::_on_cover_state_change erkennt eine fremde
Fahrt bereits fuer die auf/ab-Buchfuehrung (note_manual_position) und fuer
commanded_position (forget_commanded_position) - die Vormerkung fehlte dabei."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
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
    DOMAIN,
)

COVER = "cover.bjoerg_schlafzimmer"
WINDOW = "sensor.bjoerg_fenstergriff"

AREA = {
    CONF_AREA_ID: "bjoerg_sleep",
    CONF_AREA_NAME: "Schlafbereich",
    CONF_AREA_MODE: AREA_MODE_NONE,
}


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Schlafzimmer",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "open",
        CONF_WINDOW_TILTED_STATE: "tilted",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_WHEN_WINDOW_OPEN: 95,
        CONF_POSITION_WHEN_WINDOW_TILTED: 30,
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture(autouse=True)
def _fast_startup(monkeypatch):
    from custom_components.shutter_pilot import cover_tracker

    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def cover_calls(hass):
    calls: list = []

    async def _handler(call):
        calls.append(call)
        position = call.data["position"]
        entity_id = call.data["entity_id"]
        for eid in [entity_id] if isinstance(entity_id, str) else entity_id:
            hass.states.async_set(
                eid,
                "closed" if position <= 0 else "open",
                {"current_position": position, "supported_features": 15},
            )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return calls


def _positions(calls) -> list[int]:
    return [c.data["position"] for c in calls]


async def _setup(hass):
    hass.states.async_set(
        COVER, "open", {"current_position": 95, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "open")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter()]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


class TestStalePendingDriveAfterManualMove:
    async def test_pending_close_does_not_survive_a_later_manual_reopen(
        self, hass, cover_calls
    ):
        entry, data = await _setup(hass)

        # Abendliche automatische Zufahrt wird wegen offenem Fenster vorgemerkt
        # (wie brightness.py::_run_down es fuer drive_after_close macht).
        from custom_components.shutter_pilot.helpers import remember_drive_after_close

        shutter = entry.options[CONF_SHUTTERS][0]
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down (test)", shutter=shutter,
        )
        assert COVER in data["drive_after_close_pending"]

        # Nachts: Taster am Bett, manuelle Teilfahrt auf 35%.
        hass.states.async_set(
            COVER, "open", {"current_position": 35, "supported_features": 15}
        )
        await hass.async_block_till_done()

        # Morgens: er faehrt von Hand wieder ganz hoch (100%), weil die
        # Automatik wegen des Overrides nicht selbst hochgefahren ist.
        hass.states.async_set(
            COVER, "open", {"current_position": 100, "supported_features": 15}
        )
        await hass.async_block_till_done()
        cover_calls.clear()

        # Irgendwann spaeter am Tag, voellig unabhaengig: das Fenster wird
        # tatsaechlich geschlossen (z.B. jemand raeumt auf).
        hass.states.async_set(WINDOW, "closed")
        await hass.async_block_till_done()

        assert _positions(cover_calls) == [], (
            "Der frisch von Hand voll geoeffnete Rollladen darf nicht wegen "
            "einer laengst ueberholten Vormerkung von letzter Nacht auf 0% "
            f"zufahren: {_positions(cover_calls)}"
        )
