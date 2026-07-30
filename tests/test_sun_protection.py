"""Tests for elevation + azimuth based sun protection."""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ELEVATION_THRESHOLD,
)
from custom_components.shutter_pilot.helpers import (
    azimuth_in_sun_protect_range,
    elevation_in_sun_protect_range,
    get_azimuth_bounds,
    get_elevation_bounds,
    sun_protect_conditions_met,
)


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ELEVATION_MIN: 0.0,
        CONF_AREA_ELEVATION_MAX: 15.0,
    }
    area.update(overrides)
    return area


class TestElevationBounds:
    def test_explicit_range(self):
        assert get_elevation_bounds(_area()) == (0.0, 15.0)

    def test_legacy_threshold_maps_to_max(self):
        area = {CONF_AREA_ELEVATION_THRESHOLD: 10.0}
        e_min, e_max = get_elevation_bounds(area)
        assert e_max == 10.0
        assert e_min == 7.0

    def test_swapped_bounds_are_normalised(self):
        area = _area(**{CONF_AREA_ELEVATION_MIN: 20.0, CONF_AREA_ELEVATION_MAX: 5.0})
        assert get_elevation_bounds(area) == (5.0, 20.0)

    @pytest.mark.parametrize(
        ("elev", "expected"),
        [(-1.0, False), (0.0, True), (7.5, True), (15.0, True), (15.1, False)],
    )
    def test_in_range(self, elev, expected):
        assert elevation_in_sun_protect_range(elev, _area()) is expected


class TestAzimuthRange:
    def test_disabled_always_true(self):
        """Legacy behaviour: without the azimuth check nothing is blocked."""
        area = _area()
        assert azimuth_in_sun_protect_range(0.0, area) is True
        assert azimuth_in_sun_protect_range(359.0, area) is True

    def test_missing_reading_fails_open(self):
        area = _area(**{CONF_AREA_AZIMUTH_ENABLED: True})
        assert azimuth_in_sun_protect_range(None, area) is True

    @pytest.mark.parametrize(
        ("azimuth", "expected"),
        [(134.0, False), (135.0, True), (180.0, True), (225.0, True), (226.0, False)],
    )
    def test_south_facing(self, azimuth, expected):
        area = _area(
            **{
                CONF_AREA_AZIMUTH_ENABLED: True,
                CONF_AREA_AZIMUTH_MIN: 135.0,
                CONF_AREA_AZIMUTH_MAX: 225.0,
            }
        )
        assert azimuth_in_sun_protect_range(azimuth, area) is expected

    @pytest.mark.parametrize(
        ("azimuth", "expected"),
        [(314.0, False), (315.0, True), (350.0, True), (0.0, True), (45.0, True), (46.0, False)],
    )
    def test_north_facing_wraps_around_zero(self, azimuth, expected):
        """A north-facing room spans 315°–45°, crossing the 0° boundary."""
        area = _area(
            **{
                CONF_AREA_AZIMUTH_ENABLED: True,
                CONF_AREA_AZIMUTH_MIN: 315.0,
                CONF_AREA_AZIMUTH_MAX: 45.0,
            }
        )
        assert azimuth_in_sun_protect_range(azimuth, area) is expected

    def test_values_are_normalised(self):
        area = _area(
            **{
                CONF_AREA_AZIMUTH_ENABLED: True,
                CONF_AREA_AZIMUTH_MIN: 135.0,
                CONF_AREA_AZIMUTH_MAX: 225.0,
            }
        )
        assert azimuth_in_sun_protect_range(180.0 + 360.0, area) is True
        assert get_azimuth_bounds({CONF_AREA_AZIMUTH_MIN: 400, CONF_AREA_AZIMUTH_MAX: 720}) == (40.0, 0.0)


class TestCombinedConditions:
    def test_west_room_not_shaded_at_sunrise(self):
        """The bug azimuth support fixes: 0–15° elevation is hit twice a day."""
        area = _area(
            **{
                CONF_AREA_AZIMUTH_ENABLED: True,
                CONF_AREA_AZIMUTH_MIN: 225.0,
                CONF_AREA_AZIMUTH_MAX: 315.0,
            }
        )
        # Morning: sun low in the east - must NOT shade a west-facing room.
        assert sun_protect_conditions_met(8.0, 85.0, area) is False
        # Evening: sun low in the west - must shade.
        assert sun_protect_conditions_met(8.0, 265.0, area) is True

    def test_without_azimuth_both_times_shade(self):
        area = _area()
        assert sun_protect_conditions_met(8.0, 85.0, area) is True
        assert sun_protect_conditions_met(8.0, 265.0, area) is True

    def test_elevation_outside_range_never_shades(self):
        area = _area(
            **{
                CONF_AREA_AZIMUTH_ENABLED: True,
                CONF_AREA_AZIMUTH_MIN: 135.0,
                CONF_AREA_AZIMUTH_MAX: 225.0,
            }
        )
        assert sun_protect_conditions_met(40.0, 180.0, area) is False

    def test_missing_elevation_never_shades(self):
        assert sun_protect_conditions_met(None, 180.0, _area()) is False
