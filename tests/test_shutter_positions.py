"""Tests for per-shutter positions, slats and lock protection."""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_TILT_CLOSED,
    CONF_TILT_ENABLED,
    CONF_TILT_OPEN,
    CONF_TILT_SUN_PROTECT,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    ROLE_CLOSED,
    ROLE_OPEN,
    ROLE_SUN_PROTECT,
)
from custom_components.shutter_pilot.helpers import (
    get_position_for_role,
    get_tilt_for_role,
)
from custom_components.shutter_pilot.window_helper import (
    get_effective_close_position,
    get_window_state,
)


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_POSITION_OPEN: 90,
        CONF_POSITION_CLOSED: 10,
        CONF_POSITION_SUN_PROTECT: 40,
    }
    shutter.update(overrides)
    return shutter


class TestRolePositions:
    """The group services used to hard-code 100/0 and ignore these values."""

    @pytest.mark.parametrize(
        ("role", "expected"),
        [(ROLE_OPEN, 90), (ROLE_CLOSED, 10), (ROLE_SUN_PROTECT, 40)],
    )
    def test_configured_values_win(self, role, expected):
        assert get_position_for_role(_shutter(), role) == expected

    def test_defaults_when_unset(self):
        assert get_position_for_role({}, ROLE_OPEN) == 100
        assert get_position_for_role({}, ROLE_CLOSED) == 0
        assert get_position_for_role({}, ROLE_SUN_PROTECT) == 50

    def test_invalid_value_falls_back(self):
        assert get_position_for_role({CONF_POSITION_OPEN: "abc"}, ROLE_OPEN) == 100


class TestTilt:
    def test_disabled_returns_none(self):
        assert get_tilt_for_role(_shutter(), ROLE_OPEN) is None

    def test_enabled_returns_configured_angles(self):
        shutter = _shutter(
            **{
                CONF_TILT_ENABLED: True,
                CONF_TILT_OPEN: 100,
                CONF_TILT_CLOSED: 0,
                CONF_TILT_SUN_PROTECT: 25,
            }
        )
        assert get_tilt_for_role(shutter, ROLE_OPEN) == 100
        assert get_tilt_for_role(shutter, ROLE_CLOSED) == 0
        assert get_tilt_for_role(shutter, ROLE_SUN_PROTECT) == 25

    def test_values_are_clamped(self):
        shutter = _shutter(**{CONF_TILT_ENABLED: True, CONF_TILT_OPEN: 500})
        assert get_tilt_for_role(shutter, ROLE_OPEN) == 100
        shutter = _shutter(**{CONF_TILT_ENABLED: True, CONF_TILT_OPEN: -20})
        assert get_tilt_for_role(shutter, ROLE_OPEN) == 0


class TestLockProtection:
    async def test_no_protection_returns_target(self, hass):
        shutter = _shutter()
        assert get_effective_close_position(hass, shutter, 0) == 0

    async def test_open_door_caps_position(self, hass):
        hass.states.async_set("binary_sensor.door", "on")
        shutter = _shutter(
            **{
                CONF_LOCK_PROTECTION: True,
                CONF_MIN_POSITION_WHEN_OPEN: 25,
                CONF_WINDOW_ENTITY_ID: "binary_sensor.door",
                CONF_WINDOW_OPEN_STATE: "on",
            }
        )
        assert get_effective_close_position(hass, shutter, 0) == 25

    async def test_closed_door_allows_full_close(self, hass):
        hass.states.async_set("binary_sensor.door", "off")
        shutter = _shutter(
            **{
                CONF_LOCK_PROTECTION: True,
                CONF_MIN_POSITION_WHEN_OPEN: 25,
                CONF_WINDOW_ENTITY_ID: "binary_sensor.door",
                CONF_WINDOW_OPEN_STATE: "on",
            }
        )
        assert get_effective_close_position(hass, shutter, 0) == 0

    async def test_target_above_minimum_is_untouched(self, hass):
        hass.states.async_set("binary_sensor.door", "on")
        shutter = _shutter(
            **{
                CONF_LOCK_PROTECTION: True,
                CONF_MIN_POSITION_WHEN_OPEN: 25,
                CONF_WINDOW_ENTITY_ID: "binary_sensor.door",
                CONF_WINDOW_OPEN_STATE: "on",
            }
        )
        assert get_effective_close_position(hass, shutter, 60) == 60


class TestWindowState:
    async def test_no_sensor_is_closed(self, hass):
        assert get_window_state(hass, _shutter()) == "closed"

    async def test_two_state_contact(self, hass):
        hass.states.async_set("binary_sensor.win", "on")
        shutter = _shutter(
            **{
                CONF_WINDOW_ENTITY_ID: "binary_sensor.win",
                CONF_WINDOW_OPEN_STATE: "on",
                CONF_WINDOW_TILTED_STATE: "none",
            }
        )
        assert get_window_state(hass, shutter) == "open"

    async def test_three_state_contact_tilted(self, hass):
        hass.states.async_set("binary_sensor.win", "tilted")
        shutter = _shutter(
            **{
                CONF_WINDOW_ENTITY_ID: "binary_sensor.win",
                CONF_WINDOW_OPEN_STATE: "on",
                CONF_WINDOW_TILTED_STATE: "tilted",
            }
        )
        assert get_window_state(hass, shutter) == "tilted"

    async def test_sensor_domain_german_states(self, hass):
        hass.states.async_set("sensor.win", "gekippt")
        shutter = _shutter(**{CONF_WINDOW_ENTITY_ID: "sensor.win"})
        assert get_window_state(hass, shutter) == "tilted"
