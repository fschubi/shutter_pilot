"""Tests for per-shutter conditions falling back to the area.

Forum discussion: MartyBr wants a brightness sensor per window and an indoor
temperature per room. bjoerg wants to configure things once and assign them.
Both are the same feature: the default lives in the area, the exception on
the window.
"""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_AREA_ID,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_COVER_ENTITY_ID,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    condition_memory,
    resolve_shading_config,
    sun_extra_conditions_met,
)

A_ENTITY, A_ON, A_OFF, A_STATES = sun_condition_keys("a")
B_ENTITY, B_ON, B_OFF, B_STATES = sun_condition_keys("b")


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        A_ENTITY: "sensor.area_lux",
        A_ON: 30000,
        B_ENTITY: "binary_sensor.weather_ok",
    }
    area.update(overrides)
    return area


def _shutter(cover: str = "cover.south", **overrides) -> dict:
    shutter = {CONF_COVER_ENTITY_ID: cover}
    shutter.update(overrides)
    return shutter


@pytest.fixture
def data() -> dict:
    return {}


class TestFallback:
    def test_empty_shutter_inherits_everything(self):
        area = _area()
        merged = resolve_shading_config(area, _shutter())
        assert merged[A_ENTITY] == "sensor.area_lux"
        assert merged[B_ENTITY] == "binary_sensor.weather_ok"

    def test_no_shutter_returns_area(self):
        area = _area()
        assert resolve_shading_config(area, None) is area

    def test_shutter_slot_replaces_only_that_slot(self):
        """The point of the whole design: brightness per window, weather once."""
        area = _area()
        shutter = _shutter(**{A_ENTITY: "sensor.south_lux", A_ON: 45000})
        merged = resolve_shading_config(area, shutter)
        assert merged[A_ENTITY] == "sensor.south_lux"
        assert merged[A_ON] == 45000
        # Slot B still comes from the area.
        assert merged[B_ENTITY] == "binary_sensor.weather_ok"

    def test_override_clears_unset_keys_of_that_slot(self):
        """A slot is taken as a whole, so a stale area threshold cannot leak."""
        area = _area()
        shutter = _shutter(**{A_ENTITY: "binary_sensor.south_sun"})
        merged = resolve_shading_config(area, shutter)
        assert merged[A_ENTITY] == "binary_sensor.south_sun"
        assert merged[A_ON] is None

    def test_area_is_not_mutated(self):
        area = _area()
        resolve_shading_config(area, _shutter(**{A_ENTITY: "sensor.other"}))
        assert area[A_ENTITY] == "sensor.area_lux"

    def test_blank_entity_does_not_override(self):
        area = _area()
        merged = resolve_shading_config(area, _shutter(**{A_ENTITY: "   "}))
        assert merged[A_ENTITY] == "sensor.area_lux"


class TestSeparateHysteresis:
    """Two windows watching different sensors must not share a memory."""

    def test_memory_keys_differ_per_cover(self, data):
        area_only = condition_memory(data, "living")
        south = condition_memory(data, "living", "cover.south")
        west = condition_memory(data, "living", "cover.west")
        south["a"] = True
        assert west == {}
        assert area_only == {}
        assert set(data["sun_cond_state"]) == {
            "living",
            "living|cover.south",
            "living|cover.west",
        }

    async def test_two_windows_hold_independently(self, hass, data):
        """South is in its dead band and holds; west never engaged."""
        area = _area(**{A_ON: 30000, A_OFF: 20000, B_ENTITY: ""})
        south = _shutter("cover.south", **{A_ENTITY: "sensor.south_lux", A_ON: 30000, A_OFF: 20000})
        west = _shutter("cover.west", **{A_ENTITY: "sensor.west_lux", A_ON: 30000, A_OFF: 20000})

        hass.states.async_set("sensor.south_lux", "35000")
        hass.states.async_set("sensor.west_lux", "5000")

        south_cfg = resolve_shading_config(area, south)
        west_cfg = resolve_shading_config(area, west)

        assert sun_extra_conditions_met(hass, south_cfg, data, "cover.south") is True
        assert sun_extra_conditions_met(hass, west_cfg, data, "cover.west") is False

        # South dips into the dead band – it must hold, west stays off.
        hass.states.async_set("sensor.south_lux", "25000")
        assert sun_extra_conditions_met(hass, south_cfg, data, "cover.south") is True
        assert sun_extra_conditions_met(hass, west_cfg, data, "cover.west") is False

    async def test_without_cover_id_uses_area_memory(self, hass, data):
        area = _area(**{A_ON: 30000, A_OFF: 20000, B_ENTITY: ""})
        hass.states.async_set("sensor.area_lux", "35000")
        assert sun_extra_conditions_met(hass, area, data) is True
        assert "living" in data["sun_cond_state"]


class TestCombined:
    async def test_window_sensor_beats_area_sensor(self, hass, data):
        area = _area(**{B_ENTITY: ""})
        hass.states.async_set("sensor.area_lux", "50000")
        hass.states.async_set("sensor.south_lux", "1000")

        shutter = _shutter("cover.south", **{A_ENTITY: "sensor.south_lux", A_ON: 30000})
        merged = resolve_shading_config(area, shutter)
        # The window is in the shade even though the area sensor is bright.
        assert sun_extra_conditions_met(hass, merged, data, "cover.south") is False
