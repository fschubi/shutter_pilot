"""Tests for window state detection, including a separate tilt contact.

Forum feedback (JayJayX): some windows expose "open" and "tilted" as two
different entities instead of one entity with three states.
"""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_ENTITY_ID,
    CONF_WINDOW_TILTED_ENTITY_STATE,
    CONF_WINDOW_TILTED_STATE,
)
from custom_components.shutter_pilot.window_helper import (
    get_tilt_entity_id,
    get_window_state,
    has_separate_tilt_entity,
    is_window_open_or_tilted,
)


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_WINDOW_ENTITY_ID: "binary_sensor.win",
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "none",
    }
    shutter.update(overrides)
    return shutter


class TestSingleContactUnchanged:
    """The existing single-contact behaviour must not shift at all."""

    async def test_closed(self, hass):
        hass.states.async_set("binary_sensor.win", "off")
        assert get_window_state(hass, _shutter()) == "closed"

    async def test_open(self, hass):
        hass.states.async_set("binary_sensor.win", "on")
        assert get_window_state(hass, _shutter()) == "open"

    async def test_three_state_contact_tilted(self, hass):
        hass.states.async_set("binary_sensor.win", "tilted")
        assert (
            get_window_state(hass, _shutter(**{CONF_WINDOW_TILTED_STATE: "tilted"}))
            == "tilted"
        )

    async def test_no_sensor_is_closed(self, hass):
        assert get_window_state(hass, {}) == "closed"


class TestSeparateTiltEntity:
    def _two_sensor_shutter(self, **overrides) -> dict:
        return _shutter(
            **{CONF_WINDOW_TILTED_ENTITY_ID: "binary_sensor.win_tilt", **overrides}
        )

    async def test_tilt_wins_over_open(self, hass):
        """While tilted, many contacts also read 'open' – tilt must win."""
        hass.states.async_set("binary_sensor.win", "on")
        hass.states.async_set("binary_sensor.win_tilt", "on")
        assert get_window_state(hass, self._two_sensor_shutter()) == "tilted"

    async def test_open_when_tilt_inactive(self, hass):
        hass.states.async_set("binary_sensor.win", "on")
        hass.states.async_set("binary_sensor.win_tilt", "off")
        assert get_window_state(hass, self._two_sensor_shutter()) == "open"

    async def test_closed_when_both_off(self, hass):
        hass.states.async_set("binary_sensor.win", "off")
        hass.states.async_set("binary_sensor.win_tilt", "off")
        assert get_window_state(hass, self._two_sensor_shutter()) == "closed"

    async def test_tilt_only_without_main_contact(self, hass):
        hass.states.async_set("binary_sensor.win_tilt", "on")
        shutter = {CONF_WINDOW_TILTED_ENTITY_ID: "binary_sensor.win_tilt"}
        assert get_window_state(hass, shutter) == "tilted"

    async def test_tilt_only_inactive_is_closed(self, hass):
        hass.states.async_set("binary_sensor.win_tilt", "off")
        shutter = {CONF_WINDOW_TILTED_ENTITY_ID: "binary_sensor.win_tilt"}
        assert get_window_state(hass, shutter) == "closed"

    async def test_custom_active_state(self, hass):
        hass.states.async_set("binary_sensor.win", "off")
        hass.states.async_set("binary_sensor.win_tilt", "gekippt")
        shutter = self._two_sensor_shutter(
            **{CONF_WINDOW_TILTED_ENTITY_STATE: "gekippt"}
        )
        assert get_window_state(hass, shutter) == "tilted"

    async def test_missing_tilt_entity_falls_back(self, hass):
        """A configured but absent tilt entity must not break detection."""
        hass.states.async_set("binary_sensor.win", "on")
        assert get_window_state(hass, self._two_sensor_shutter()) == "open"

    async def test_counts_as_open_or_tilted(self, hass):
        hass.states.async_set("binary_sensor.win", "off")
        hass.states.async_set("binary_sensor.win_tilt", "on")
        assert is_window_open_or_tilted(hass, self._two_sensor_shutter()) is True


class TestHelpers:
    def test_detects_separate_entity(self):
        assert has_separate_tilt_entity({}) is False
        assert has_separate_tilt_entity({CONF_WINDOW_TILTED_ENTITY_ID: ""}) is False
        assert (
            has_separate_tilt_entity({CONF_WINDOW_TILTED_ENTITY_ID: "binary_sensor.x"})
            is True
        )

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("binary_sensor.x", "binary_sensor.x"),
            (["binary_sensor.x"], "binary_sensor.x"),
            ([], ""),
            (None, ""),
            ("  binary_sensor.x  ", "binary_sensor.x"),
        ],
    )
    def test_entity_id_normalisation(self, value, expected):
        assert get_tilt_entity_id({CONF_WINDOW_TILTED_ENTITY_ID: value}) == expected
