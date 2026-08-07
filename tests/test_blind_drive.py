"""Rollläden ohne Positionsrückmeldung (Wunsch von Viktor, ESP Somfy RTS).

Einseitiger Funk antwortet nicht. Jede Prüfung, die eine Position braucht, gab
deshalb auf – womit Fenstertrigger und automatisches Lüften für solche Antriebe
stillschweigend abgeschaltet waren.

Im Blind-Modus rechnet Shutter Pilot stattdessen mit der Position, die es selbst
zuletzt geschickt hat. Das ist so nah an der Wahrheit, wie es bei solchen
Antrieben überhaupt geht.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    CONF_BLIND_DRIVE,
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_CLOSED,
    CONF_SHUTTERS,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import get_tracked_position
from custom_components.shutter_pilot.position_store import (
    SOURCE_AUTOMATION,
    get_position_store,
)

BLIND = "cover.somfy_rts"
NORMAL = "cover.knx"


@pytest.fixture
async def entry(hass):
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="SP",
        options={
            CONF_SHUTTERS: [
                {CONF_COVER_ENTITY_ID: BLIND, CONF_BLIND_DRIVE: True},
                {CONF_COVER_ENTITY_ID: NORMAL},
            ]
        },
    )
    config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {}
    get_position_store(hass, config_entry.entry_id)
    return config_entry


def _blind() -> dict:
    return {CONF_COVER_ENTITY_ID: BLIND, CONF_BLIND_DRIVE: True, CONF_POSITION_CLOSED: 0}


def _normal() -> dict:
    return {CONF_COVER_ENTITY_ID: NORMAL, CONF_POSITION_CLOSED: 0}


class TestWithoutFeedback:
    """Der Antrieb meldet keine Position – nur `state`, kein current_position."""

    async def test_blind_mode_uses_the_last_commanded_position(self, hass, entry):
        hass.states.async_set(BLIND, "open", {"supported_features": 15})
        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(BLIND, 40, SOURCE_AUTOMATION)

        assert get_tracked_position(hass, _blind(), BLIND) == 40

    async def test_without_blind_mode_it_stays_unknown(self, hass, entry):
        """Bisheriges Verhalten für alle anderen Rollläden."""
        hass.states.async_set(NORMAL, "open", {"supported_features": 15})
        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(NORMAL, 40, SOURCE_AUTOMATION)

        assert get_tracked_position(hass, _normal(), NORMAL) is None

    async def test_blind_mode_without_history_is_still_unknown(self, hass, entry):
        """Vor der ersten Fahrt weiss auch die Buchführung nichts."""
        hass.states.async_set(BLIND, "open", {"supported_features": 15})
        assert get_tracked_position(hass, _blind(), BLIND) is None


class TestWithFeedback:
    """Meldet der Antrieb eine Position, gilt sie – auch im Blind-Modus."""

    async def test_live_position_wins(self, hass, entry):
        hass.states.async_set(
            BLIND, "open", {"current_position": 75, "supported_features": 15}
        )
        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(BLIND, 40, SOURCE_AUTOMATION)

        assert get_tracked_position(hass, _blind(), BLIND) == 75

    async def test_normal_cover_unchanged(self, hass, entry):
        hass.states.async_set(
            NORMAL, "open", {"current_position": 75, "supported_features": 15}
        )
        assert get_tracked_position(hass, _normal(), NORMAL) == 75


class TestFlagParsing:
    @pytest.mark.parametrize("value", [False, None, "", 0])
    async def test_values_that_mean_off(self, hass, entry, value):
        hass.states.async_set(BLIND, "open", {"supported_features": 15})
        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(BLIND, 40, SOURCE_AUTOMATION)

        shutter = {CONF_COVER_ENTITY_ID: BLIND, CONF_BLIND_DRIVE: value}
        assert get_tracked_position(hass, shutter, BLIND) is None

    async def test_missing_key_is_off(self, hass, entry):
        hass.states.async_set(BLIND, "open", {"supported_features": 15})
        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(BLIND, 40, SOURCE_AUTOMATION)

        assert get_tracked_position(hass, {CONF_COVER_ENTITY_ID: BLIND}, BLIND) is None
