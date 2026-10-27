"""My-Position bei einem Antrieb ohne Rueckmeldung, der trotzdem Positionen kann
(Reinhard-M, GitHub #21).

Jarolift-Controller bieten `set_cover_position` und zusaetzlich den
"Shade"-Knopf an, melden aber keine Position zurueck. Die My-Position wurde
bisher nur benutzt, wo der Antrieb gar keine Positionsfahrt kennt - hier wurde
sie nie gedrueckt, der Rollladen fuhr ueber die zeitbasierte Schaetzung des
Controllers. Mit gesetztem "Antrieb meldet keine Position" gewinnt jetzt der
Knopf; ohne den Haken bleibt die Zahl die genauere Anweisung."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot.const import (
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_BLIND_DRIVE,
    CONF_COVER_ENTITY_ID,
    CONF_MY_POSITION_ENTITY,
    CONF_MY_POSITION_PCT,
    CONF_NAME,
    CONF_POSITION_OPEN,
    CONF_SHUTTERS,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import set_cover_position

COVER = "cover.jarolift_wohnzimmer"
SHADE = "button.jarolift_wohnzimmer_shade"
# SET_POSITION | OPEN | CLOSE | STOP
CAN_POSITION = 15


@pytest.fixture
def calls(hass):
    return {
        "position": async_mock_service(hass, "cover", "set_cover_position"),
        "open": async_mock_service(hass, "cover", "open_cover"),
        "close": async_mock_service(hass, "cover", "close_cover"),
        "press": async_mock_service(hass, "button", "press"),
    }


async def _drive(hass, position: float, **shutter_extra):
    hass.states.async_set(COVER, "open", {"supported_features": CAN_POSITION})
    hass.states.async_set(SHADE, "unknown")
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Wohnzimmer",
        CONF_POSITION_OPEN: 100,
        CONF_MY_POSITION_ENTITY: SHADE,
        CONF_MY_POSITION_PCT: 29,
    }
    shutter.update(shutter_extra)
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_AREAS: [{CONF_AREA_ID: "living", CONF_AREA_NAME: "Wohnen"}],
            CONF_SHUTTERS: [shutter],
        },
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    await set_cover_position(hass, entry, COVER, position, "Test")
    await hass.async_block_till_done()


async def test_the_shade_button_is_pressed_for_a_blind_drive(hass, calls):
    await _drive(hass, 29, **{CONF_BLIND_DRIVE: True})
    assert len(calls["press"]) == 1
    assert calls["position"] == []


async def test_a_target_within_the_tolerance_still_presses_it(hass, calls):
    await _drive(hass, 35, **{CONF_BLIND_DRIVE: True})
    assert len(calls["press"]) == 1


async def test_a_target_far_from_my_is_driven_by_position(hass, calls):
    await _drive(hass, 80, **{CONF_BLIND_DRIVE: True})
    assert calls["press"] == []
    assert [c.data["position"] for c in calls["position"]] == [80]


async def test_without_the_blind_drive_hook_the_number_wins(hass, calls):
    """Bestandsschutz: ein Antrieb mit Rueckmeldung bleibt bei der Zahl."""
    await _drive(hass, 29)
    assert calls["press"] == []
    assert [c.data["position"] for c in calls["position"]] == [29]


async def test_without_a_my_entity_nothing_changes(hass, calls):
    await _drive(
        hass, 29, **{CONF_BLIND_DRIVE: True, CONF_MY_POSITION_ENTITY: ""}
    )
    assert calls["press"] == []
    assert [c.data["position"] for c in calls["position"]] == [29]
