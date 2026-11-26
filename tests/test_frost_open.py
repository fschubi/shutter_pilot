"""Frostschutz beim Oeffnen (MartyBr, simon42 #268).

MartyBr faehrt seine bodentiefen Terrassentueren bei Frost abends nur auf
85 % (Frostschutz-Position). Morgens fuhren sie trotzdem ganz in den Kasten -
dort koennen sie bei Schnee festfrieren. Jetzt gibt es das Gegenstueck: dieselbe
Frost-Bedingung des Bereichs, eine eigene Position fuers Hochfahren."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
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
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_CLOSED_FROST,
    CONF_POSITION_OPEN,
    CONF_POSITION_OPEN_FROST,
    CONF_SHUTTERS,
    DOMAIN,
    FROST_CONDITION_SLOT,
    ROLE_OPEN,
    ROLE_OPEN_FROST,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    frost_opening_applies,
    get_position_for_role,
    has_frost_open_position,
    resolve_open_role,
)

TEMP = "sensor.aussen"
COVER = "cover.terrasse"

_entity_key, _on_key, _off_key, _ = sun_condition_keys(FROST_CONDITION_SLOT)
AREA = {
    CONF_AREA_ID: "wohnen",
    CONF_AREA_NAME: "Wohnen",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
    _entity_key: TEMP,
    _on_key: 0,
    _off_key: 2,
}
SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Terrasse",
    CONF_AREA_UP_ID: "wohnen",
    CONF_AREA_DOWN_ID: "wohnen",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
    CONF_POSITION_CLOSED_FROST: 85,
    CONF_POSITION_OPEN_FROST: 85,
}


class TestRole:
    async def test_frost_stops_the_opening_short(self, hass):
        hass.states.async_set(TEMP, "-3")
        assert resolve_open_role(hass, AREA, SHUTTER, {}) == ROLE_OPEN_FROST
        assert get_position_for_role(SHUTTER, ROLE_OPEN_FROST) == 85

    async def test_without_frost_it_opens_fully(self, hass):
        hass.states.async_set(TEMP, "8")
        assert resolve_open_role(hass, AREA, SHUTTER, {}) == ROLE_OPEN

    async def test_without_the_position_frost_changes_nothing(self, hass):
        """Bestandsschutz: wer nur die Abend-Position hat, faehrt morgens ganz auf."""
        hass.states.async_set(TEMP, "-3")
        shutter = {k: v for k, v in SHUTTER.items() if k != CONF_POSITION_OPEN_FROST}
        assert not has_frost_open_position(shutter)
        assert resolve_open_role(hass, AREA, shutter, {}) == ROLE_OPEN

    async def test_an_empty_field_is_no_position(self, hass):
        hass.states.async_set(TEMP, "-3")
        shutter = dict(SHUTTER, **{CONF_POSITION_OPEN_FROST: ""})
        assert resolve_open_role(hass, AREA, shutter, {}) == ROLE_OPEN

    @pytest.mark.parametrize("state", ["unavailable", "unknown"])
    async def test_a_dead_sensor_opens_fully(self, hass, state):
        """Fail closed wie der Frostschutz beim Schliessen."""
        hass.states.async_set(TEMP, state)
        assert resolve_open_role(hass, AREA, SHUTTER, {}) == ROLE_OPEN

    async def test_no_area_opens_fully(self, hass):
        hass.states.async_set(TEMP, "-3")
        assert resolve_open_role(hass, None, SHUTTER, {}) == ROLE_OPEN


async def _setup(hass, shutter=None):
    hass.states.async_set(COVER, "closed", {"current_position": 0, "supported_features": 15})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [shutter or SHUTTER]},
    )
    entry.add_to_hass(hass)
    with patch("custom_components.shutter_pilot._async_register_panel", return_value=None):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _morning(hass, data) -> None:
    when = (dt_util.now() + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    data["_minute_callbacks"]["scheduler"](when)
    await hass.async_block_till_done()


class TestMorningDrive:
    async def test_in_frost_the_schedule_stops_at_85(self, hass):
        calls = async_mock_service(hass, "cover", "set_cover_position")
        hass.states.async_set(TEMP, "-3")
        _, data = await _setup(hass)
        await _morning(hass, data)
        assert [c.data["position"] for c in calls] == [85]

    async def test_without_frost_the_schedule_opens_fully(self, hass):
        calls = async_mock_service(hass, "cover", "set_cover_position")
        hass.states.async_set(TEMP, "6")
        _, data = await _setup(hass)
        await _morning(hass, data)
        assert [c.data["position"] for c in calls] == [100]

    async def test_frost_opening_applies_follows_the_up_area(self, hass):
        hass.states.async_set(TEMP, "-3")
        entry, data = await _setup(hass)
        assert frost_opening_applies(hass, entry, SHUTTER, data) is True
        hass.states.async_set(TEMP, "6")
        assert frost_opening_applies(hass, entry, SHUTTER, {}) is False
