"""Tests for the extra shading conditions.

Forum feedback (Nicknol): shading should only run when there is real sunshine
and when the day actually gets warm — in spring and autumn the passive solar
heating is wanted.
"""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    sun_extra_conditions_met,
    sun_protect_conditions_met,
)

A_ENTITY, A_ON, A_OFF = sun_condition_keys("a")
B_ENTITY, B_ON, B_OFF = sun_condition_keys("b")


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_ELEVATION_MIN: 0.0,
        CONF_AREA_ELEVATION_MAX: 15.0,
    }
    area.update(overrides)
    return area


@pytest.fixture
def data() -> dict:
    return {}


class TestNoConditions:
    async def test_unconfigured_never_blocks(self, hass, data):
        assert sun_extra_conditions_met(hass, _area(), data) is True

    async def test_empty_string_never_blocks(self, hass, data):
        assert sun_extra_conditions_met(hass, _area(**{A_ENTITY: "  "}), data) is True


class TestBinarySensor:
    async def test_on_allows_shading(self, hass, data):
        hass.states.async_set("binary_sensor.sun_high", "on")
        area = _area(**{A_ENTITY: "binary_sensor.sun_high"})
        assert sun_extra_conditions_met(hass, area, data) is True

    async def test_off_blocks_shading(self, hass, data):
        hass.states.async_set("binary_sensor.sun_high", "off")
        area = _area(**{A_ENTITY: "binary_sensor.sun_high"})
        assert sun_extra_conditions_met(hass, area, data) is False

    async def test_unavailable_never_blocks(self, hass, data):
        """A broken sensor must not disable shading permanently."""
        hass.states.async_set("binary_sensor.sun_high", "unavailable")
        area = _area(**{A_ENTITY: "binary_sensor.sun_high"})
        assert sun_extra_conditions_met(hass, area, data) is True

    async def test_missing_entity_never_blocks(self, hass, data):
        area = _area(**{A_ENTITY: "binary_sensor.does_not_exist"})
        assert sun_extra_conditions_met(hass, area, data) is True


class TestNumericSensor:
    async def test_above_threshold_allows(self, hass, data):
        hass.states.async_set("sensor.lux", "40000")
        area = _area(**{A_ENTITY: "sensor.lux", A_ON: 30000})
        assert sun_extra_conditions_met(hass, area, data) is True

    async def test_below_threshold_blocks(self, hass, data):
        hass.states.async_set("sensor.lux", "12000")
        area = _area(**{A_ENTITY: "sensor.lux", A_ON: 30000})
        assert sun_extra_conditions_met(hass, area, data) is False

    async def test_exactly_at_threshold_allows(self, hass, data):
        hass.states.async_set("sensor.lux", "30000")
        area = _area(**{A_ENTITY: "sensor.lux", A_ON: 30000})
        assert sun_extra_conditions_met(hass, area, data) is True

    async def test_without_threshold_never_blocks(self, hass, data):
        """A sensor alone cannot decide anything without a threshold."""
        hass.states.async_set("sensor.lux", "5")
        area = _area(**{A_ENTITY: "sensor.lux"})
        assert sun_extra_conditions_met(hass, area, data) is True

    async def test_non_numeric_state_never_blocks(self, hass, data):
        hass.states.async_set("sensor.lux", "sonnig")
        area = _area(**{A_ENTITY: "sensor.lux", A_ON: 30000})
        assert sun_extra_conditions_met(hass, area, data) is True


class TestHysteresis:
    """A passing cloud must not make the shutters bounce."""

    async def test_stays_on_between_thresholds(self, hass, data):
        area = _area(**{A_ENTITY: "sensor.lux", A_ON: 30000, A_OFF: 20000})

        hass.states.async_set("sensor.lux", "35000")
        assert sun_extra_conditions_met(hass, area, data) is True

        # Dip into the dead band – shading must hold.
        hass.states.async_set("sensor.lux", "25000")
        assert sun_extra_conditions_met(hass, area, data) is True

        # Below the release threshold – now it lets go.
        hass.states.async_set("sensor.lux", "19000")
        assert sun_extra_conditions_met(hass, area, data) is False

        # Back into the dead band – must NOT re-engage before on_above.
        hass.states.async_set("sensor.lux", "25000")
        assert sun_extra_conditions_met(hass, area, data) is False

        hass.states.async_set("sensor.lux", "31000")
        assert sun_extra_conditions_met(hass, area, data) is True

    async def test_without_off_below_uses_on_above(self, hass, data):
        area = _area(**{A_ENTITY: "sensor.lux", A_ON: 30000})
        hass.states.async_set("sensor.lux", "35000")
        assert sun_extra_conditions_met(hass, area, data) is True
        hass.states.async_set("sensor.lux", "29999")
        assert sun_extra_conditions_met(hass, area, data) is False

    async def test_off_above_on_is_clamped(self, hass, data):
        """A nonsensical configuration must not create a trap."""
        area = _area(**{A_ENTITY: "sensor.lux", A_ON: 20000, A_OFF: 40000})
        hass.states.async_set("sensor.lux", "25000")
        assert sun_extra_conditions_met(hass, area, data) is True
        hass.states.async_set("sensor.lux", "21000")
        assert sun_extra_conditions_met(hass, area, data) is True


class TestTwoConditions:
    """Nicknol's case: real sunshine AND a warm day."""

    async def test_both_must_hold(self, hass, data):
        area = _area(
            **{
                A_ENTITY: "binary_sensor.sun_high",
                B_ENTITY: "sensor.outside_temp",
                B_ON: 22,
            }
        )
        hass.states.async_set("binary_sensor.sun_high", "on")
        hass.states.async_set("sensor.outside_temp", "26")
        assert sun_extra_conditions_met(hass, area, data) is True

        # Sunny but cold spring day – let the warmth in.
        hass.states.async_set("sensor.outside_temp", "14")
        assert sun_extra_conditions_met(hass, area, data) is False

        # Warm but overcast.
        hass.states.async_set("sensor.outside_temp", "26")
        hass.states.async_set("binary_sensor.sun_high", "off")
        assert sun_extra_conditions_met(hass, area, data) is False

    async def test_areas_keep_separate_memory(self, hass, data):
        living = _area(**{A_ENTITY: "sensor.lux", A_ON: 30000, A_OFF: 20000})
        sleep = _area(
            **{CONF_AREA_ID: "sleep", A_ENTITY: "sensor.lux", A_ON: 50000, A_OFF: 40000}
        )
        hass.states.async_set("sensor.lux", "35000")
        assert sun_extra_conditions_met(hass, living, data) is True
        assert sun_extra_conditions_met(hass, sleep, data) is False
        assert set(data["sun_cond_state"]) == {"living", "sleep"}


class TestGeometryStillApplies:
    async def test_conditions_are_independent_of_geometry(self, hass, data):
        """Extra conditions gate shading; they never widen the sun window."""
        area = _area(**{A_ENTITY: "binary_sensor.sun_high"})
        hass.states.async_set("binary_sensor.sun_high", "on")
        assert sun_extra_conditions_met(hass, area, data) is True
        # Sun far too high – geometry alone already says no.
        assert sun_protect_conditions_met(40.0, 180.0, area) is False
