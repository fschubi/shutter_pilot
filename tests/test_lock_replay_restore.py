"""Rueckfahrt nach der Tuer, wenn die Sperre sie zurueckgehalten hat.

Claus (simon42 #222): Sein KNX-Aktor sperrt sich bei offener Tuer selbst
(Aussperrschutz in der ETS), und dieses Sperrobjekt ist seine Sperr-Entitaet.
Schliesst die Tuer, solange die Sperre noch steht, wird das Schliessen
verworfen - und nichts holt die gemerkte Hoehe je wieder. Jetzt faehrt der
Rollladen zurueck, sobald die Sperre endet und das Fenster zu ist.
`lock_replay_restore` (Vorgabe an) schaltet das ab."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_AUTOMATION_LOCK_ENTITY,
    CONF_COVER_ENTITY_ID,
    CONF_LOCK_REPLAY,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)

COVER = "cover.raff_diele"
DOOR = "binary_sensor.diele_tuer"
LOCK = "binary_sensor.raff_diele_gesperrt"

AREA = {
    CONF_AREA_ID: "living",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
}


def _blind(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Diele",
        CONF_AREA_UP_ID: "living",
        CONF_AREA_DOWN_ID: "living",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 70,
        CONF_POSITION_WHEN_WINDOW_TILTED: 100,
        CONF_WINDOW_ENTITY_ID: DOOR,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "none",
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
        CONF_AUTOMATION_LOCK_ENTITY: LOCK,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture
def calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


async def _setup(hass, shutter: dict):
    hass.states.async_set(
        COVER, "open", {"current_position": 70, "supported_features": 255}
    )
    hass.states.async_set(DOOR, "off")
    hass.states.async_set(LOCK, "off")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [shutter]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return hass.data[DOMAIN][entry.entry_id]


async def _set(hass, entity: str, state: str) -> None:
    hass.states.async_set(entity, state)
    await hass.async_block_till_done()


async def _door_cycle_under_lock(hass, calls) -> None:
    """Tuer auf (faehrt hoch), Aktor sperrt sich, Tuer zu - die Sperre steht noch."""
    await _set(hass, DOOR, "on")
    assert [c.data["position"] for c in calls] == [100]
    # Der Rollladen steht jetzt oben; das ist die Hoehe, die der Aktor meldet.
    hass.states.async_set(
        COVER, "open", {"current_position": 100, "supported_features": 255}
    )
    await _set(hass, LOCK, "on")
    await _set(hass, DOOR, "off")
    calls.clear()


async def test_the_restore_runs_when_the_lock_ends(hass, calls):
    await _setup(hass, _blind())
    await _door_cycle_under_lock(hass, calls)
    assert calls == []  # solange die Sperre steht: nichts

    await _set(hass, LOCK, "off")

    assert [c.data["position"] for c in calls] == [70]


async def test_the_hook_off_leaves_it_where_it_is(hass, calls):
    """Wer die Sperre als Handsperre nutzt, schaltet das Nachholen ab."""
    await _setup(hass, _blind(**{CONF_LOCK_REPLAY: False}))
    await _door_cycle_under_lock(hass, calls)

    await _set(hass, LOCK, "off")

    assert calls == []


async def test_nothing_runs_while_the_door_is_still_open(hass, calls):
    await _setup(hass, _blind())
    await _set(hass, DOOR, "on")
    hass.states.async_set(
        COVER, "open", {"current_position": 100, "supported_features": 255}
    )
    await _set(hass, LOCK, "on")
    calls.clear()

    await _set(hass, LOCK, "off")

    assert calls == []


async def test_it_runs_only_once(hass, calls):
    await _setup(hass, _blind())
    await _door_cycle_under_lock(hass, calls)
    await _set(hass, LOCK, "off")
    assert [c.data["position"] for c in calls] == [70]
    calls.clear()

    await _set(hass, LOCK, "on")
    await _set(hass, LOCK, "off")

    assert calls == []


async def test_a_lock_without_a_door_cycle_moves_nothing(hass, calls):
    """Bestandsschutz: eine Sperre allein fuehrt zu keiner Fahrt."""
    await _setup(hass, _blind())

    await _set(hass, LOCK, "on")
    await _set(hass, LOCK, "off")

    assert calls == []


async def test_without_a_lock_entity_the_normal_restore_is_unchanged(hass, calls):
    await _setup(hass, _blind(**{CONF_AUTOMATION_LOCK_ENTITY: ""}))
    await _set(hass, DOOR, "on")
    calls.clear()

    await _set(hass, DOOR, "off")

    assert [c.data["position"] for c in calls] == [70]
