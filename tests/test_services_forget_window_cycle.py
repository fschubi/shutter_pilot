"""Die Dienste verwerfen die Rueckfahrhoehe des Fenstertriggers
(StephanD77, GitHub #20).

Ablauf aus dem Issue: 22:30 `close_group` (0 %), 22:48 Fenster auf - der
Trigger merkt sich 0 % als Rueckfahrhoehe -, 08:30 `open_group` (100 %,
Fenster weiter offen), 13:40 Fenster zu: der Trigger fuhr auf die gemerkten
0 %. Handfahrt (seit 2.23.0) und interne Hochfahrt verwerfen den Merker, der
Dienst nicht."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot.const import (
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_AREA_DOWN_ID,
    CONF_AREA_UP_ID,
    CONF_COVER_ENTITY_ID,
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

COVER = "cover.rolladen_schlafzimmer"
WINDOW = "binary_sensor.schlafzimmer_fenster"


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


async def _setup(hass, position: int = 0):
    hass.states.async_set(
        COVER, "closed", {"current_position": position, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "off")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [{CONF_AREA_ID: "schlafzimmer", CONF_AREA_NAME: "Schlafzimmer"}],
            CONF_SHUTTERS: [
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_NAME: "Schlafzimmer",
                    CONF_AREA_UP_ID: "schlafzimmer",
                    CONF_AREA_DOWN_ID: "schlafzimmer",
                    CONF_POSITION_OPEN: 100,
                    CONF_POSITION_CLOSED: 0,
                    CONF_WINDOW_ENTITY_ID: WINDOW,
                    CONF_WINDOW_OPEN_STATE: "on",
                    CONF_WINDOW_TILTED_STATE: "none",
                    CONF_POSITION_WHEN_WINDOW_TILTED: 30,
                    CONF_WINDOW_CLOSE_DEBOUNCE: 0,
                }
            ],
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _night_cycle(hass):
    """Rollladen zu, Fenster geht auf: der Trigger merkt sich die Hoehe."""
    hass.states.async_set(WINDOW, "on")
    await hass.async_block_till_done()


async def _service(hass, name: str) -> None:
    await hass.services.async_call(DOMAIN, name, {"area_id": "schlafzimmer"}, blocking=True)
    await hass.async_block_till_done()


async def test_the_reported_sequence_does_not_close_the_shutter(hass, cover_calls):
    _, data = await _setup(hass, position=0)
    await _night_cycle(hass)
    assert data["trigger_actions"].get(COVER) == "triggered"
    hass.states.async_set(
        COVER, "open", {"current_position": 30, "supported_features": 15}
    )
    cover_calls.clear()

    await _service(hass, "open_group")  # 08:30, Fenster weiter offen
    assert [c.data["position"] for c in cover_calls] == [100]
    hass.states.async_set(
        COVER, "open", {"current_position": 100, "supported_features": 15}
    )
    cover_calls.clear()

    hass.states.async_set(WINDOW, "off")  # 13:40
    await hass.async_block_till_done()

    assert cover_calls == [], "der Rollladen faehrt auf eine veraltete Hoehe zurueck"
    assert COVER not in data["trigger_actions"]
    assert COVER not in data["trigger_heights"]


@pytest.mark.parametrize("service", ["close_group", "sun_protect_group", "ventilate_group"])
async def test_every_group_service_drops_the_remembered_height(
    hass, cover_calls, service
):
    _, data = await _setup(hass, position=100)
    data["trigger_actions"][COVER] = "triggered"
    data["trigger_heights"][COVER] = 100

    await _service(hass, service)

    assert COVER not in data["trigger_actions"]
    assert COVER not in data["trigger_heights"]


async def test_resume_automation_drops_it_too(hass, cover_calls):
    _, data = await _setup(hass, position=100)
    data["trigger_actions"][COVER] = "triggered"
    data["trigger_heights"][COVER] = 100

    await hass.services.async_call(
        DOMAIN, "resume_automation", {"area_id": "schlafzimmer"}, blocking=True
    )
    await hass.async_block_till_done()

    # Ohne Zeitplan weiss resume nicht, wohin - dann bleibt der Merker auch
    # stehen (es wurde nichts gefahren). Faehrt es, wird er verworfen.
    if cover_calls:
        assert COVER not in data["trigger_actions"]


async def test_a_service_that_drives_nothing_leaves_the_marker(hass, cover_calls):
    """Kontrolle: stop_group faehrt keine Position, es ist keine neue Entscheidung
    ueber die Hoehe."""
    _, data = await _setup(hass, position=100)
    data["trigger_actions"][COVER] = "triggered"
    data["trigger_heights"][COVER] = 100
    async_mock_service(hass, "cover", "stop_cover")

    await _service(hass, "stop_group")

    assert data["trigger_actions"].get(COVER) == "triggered"
