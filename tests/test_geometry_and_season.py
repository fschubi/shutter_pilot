"""Tests for per-shutter shading geometry, season window and partial close.

Forum feedback:
- Linos has rooms whose windows face different directions, so elevation and
  azimuth must be settable per shutter, not just per area.
- Schlumperdix uses a season helper: 60000 lux means shading in summer, but
  welcome warmth in winter.
- Linos wants certain covers to only close part way on hot evenings.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from custom_components.shutter_pilot.const import (
    CLOSE_CONDITION_SLOT,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_SEASON_FROM,
    CONF_AREA_SEASON_TO,
    CONF_POSITION_CLOSED_ALT,
    CONF_SUN_GEOMETRY_OVERRIDE,
    ROLE_CLOSED,
    ROLE_CLOSED_ALT,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    close_condition_met,
    get_azimuth_bounds,
    get_elevation_bounds,
    get_position_for_role,
    has_alt_close_position,
    resolve_sun_geometry,
    season_allows_shading,
    sun_protect_conditions_met,
)

SOUTH = {CONF_AREA_AZIMUTH_ENABLED: True, CONF_AREA_AZIMUTH_MIN: 135.0, CONF_AREA_AZIMUTH_MAX: 225.0}
WEST = {CONF_AREA_AZIMUTH_ENABLED: True, CONF_AREA_AZIMUTH_MIN: 225.0, CONF_AREA_AZIMUTH_MAX: 315.0}


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_ELEVATION_MIN: 0.0,
        CONF_AREA_ELEVATION_MAX: 60.0,
        **SOUTH,
    }
    area.update(overrides)
    return area


class TestResolveSunGeometry:
    def test_without_override_returns_area(self):
        area = _area()
        assert resolve_sun_geometry(area, {}) is area
        assert resolve_sun_geometry(area, None) is area

    def test_override_switch_off_returns_area(self):
        area = _area()
        shutter = {CONF_SUN_GEOMETRY_OVERRIDE: False, **WEST}
        assert resolve_sun_geometry(area, shutter) is area

    def test_shutter_wins_when_enabled(self):
        area = _area()
        shutter = {CONF_SUN_GEOMETRY_OVERRIDE: True, **WEST}
        merged = resolve_sun_geometry(area, shutter)
        assert get_azimuth_bounds(merged) == (225.0, 315.0)
        # Untouched keys still come from the area.
        assert merged[CONF_AREA_ID] == "living"

    def test_partial_override_keeps_area_values(self):
        area = _area()
        shutter = {CONF_SUN_GEOMETRY_OVERRIDE: True, CONF_AREA_ELEVATION_MAX: 20.0}
        merged = resolve_sun_geometry(area, shutter)
        assert get_elevation_bounds(merged) == (0.0, 20.0)
        assert get_azimuth_bounds(merged) == (135.0, 225.0)

    def test_area_is_not_mutated(self):
        area = _area()
        resolve_sun_geometry(area, {CONF_SUN_GEOMETRY_OVERRIDE: True, **WEST})
        assert get_azimuth_bounds(area) == (135.0, 225.0)


class TestWindowsFacingDifferentWays:
    """The case Linos described: one room, south and west windows."""

    def test_south_and_west_trigger_at_different_times(self):
        area = _area()
        south = {}
        west = {CONF_SUN_GEOMETRY_OVERRIDE: True, **WEST}

        # Late morning, sun in the south-east.
        elev, azim = 40.0, 150.0
        assert sun_protect_conditions_met(elev, azim, resolve_sun_geometry(area, south)) is True
        assert sun_protect_conditions_met(elev, azim, resolve_sun_geometry(area, west)) is False

        # Afternoon, sun in the west.
        elev, azim = 25.0, 265.0
        assert sun_protect_conditions_met(elev, azim, resolve_sun_geometry(area, south)) is False
        assert sun_protect_conditions_met(elev, azim, resolve_sun_geometry(area, west)) is True


class TestSeason:
    def test_unset_means_all_year(self):
        for month in range(1, 13):
            assert season_allows_shading({}, datetime(2026, month, 15)) is True

    @pytest.mark.parametrize(
        ("month", "expected"),
        [(3, False), (4, True), (7, True), (9, True), (10, False)],
    )
    def test_summer_range(self, month, expected):
        area = {CONF_AREA_SEASON_FROM: 4, CONF_AREA_SEASON_TO: 9}
        assert season_allows_shading(area, datetime(2026, month, 15)) is expected

    @pytest.mark.parametrize(
        ("month", "expected"),
        [(9, False), (10, True), (12, True), (1, True), (3, True), (4, False)],
    )
    def test_range_wrapping_new_year(self, month, expected):
        """October to March must wrap, like the azimuth range does."""
        area = {CONF_AREA_SEASON_FROM: 10, CONF_AREA_SEASON_TO: 3}
        assert season_allows_shading(area, datetime(2026, month, 15)) is expected

    def test_single_month(self):
        area = {CONF_AREA_SEASON_FROM: 7, CONF_AREA_SEASON_TO: 7}
        assert season_allows_shading(area, datetime(2026, 7, 1)) is True
        assert season_allows_shading(area, datetime(2026, 8, 1)) is False

    @pytest.mark.parametrize("bad", [0, 13, -1, "sommer", None])
    def test_invalid_values_never_block(self, bad):
        area = {CONF_AREA_SEASON_FROM: bad, CONF_AREA_SEASON_TO: 9}
        assert season_allows_shading(area, datetime(2026, 1, 15)) is True


class TestAlternativeClosePosition:
    def test_detects_configured_value(self):
        assert has_alt_close_position({}) is False
        assert has_alt_close_position({CONF_POSITION_CLOSED_ALT: ""}) is False
        assert has_alt_close_position({CONF_POSITION_CLOSED_ALT: None}) is False
        assert has_alt_close_position({CONF_POSITION_CLOSED_ALT: "abc"}) is False
        assert has_alt_close_position({CONF_POSITION_CLOSED_ALT: 50}) is True
        assert has_alt_close_position({CONF_POSITION_CLOSED_ALT: 0}) is True

    def test_role_reads_the_value(self):
        shutter = {CONF_POSITION_CLOSED_ALT: 50, "position_closed": 0}
        assert get_position_for_role(shutter, ROLE_CLOSED_ALT) == 50
        assert get_position_for_role(shutter, ROLE_CLOSED) == 0

    async def test_condition_off_when_unconfigured(self, hass):
        """Unlike shading conditions, an unset close condition means "no"."""
        assert close_condition_met(hass, {CONF_AREA_ID: "living"}, {}) is False

    async def test_condition_follows_sensor(self, hass):
        entity_key = sun_condition_keys(CLOSE_CONDITION_SLOT)[0]
        area = {CONF_AREA_ID: "living", entity_key: "binary_sensor.hot_and_home"}
        data: dict = {}

        hass.states.async_set("binary_sensor.hot_and_home", "on")
        assert close_condition_met(hass, area, data) is True

        hass.states.async_set("binary_sensor.hot_and_home", "off")
        assert close_condition_met(hass, area, data) is False


class TestSecondCloseCondition:
    """Zwei Bedingungen fürs abweichende Schliessen (Forum, Linos).

    „Der Tag war warm" allein ist selten die ganze Regel – „und jemand ist zu
    Hause" ist die andere Hälfte. Beide müssen zutreffen, wie beim Lüften.
    """

    def _area(self, **overrides) -> dict:
        from custom_components.shutter_pilot.const import CLOSE_CONDITION_SLOTS

        a, b = (sun_condition_keys(s)[0] for s in CLOSE_CONDITION_SLOTS)
        area = {CONF_AREA_ID: "living", a: "binary_sensor.warm", b: "binary_sensor.home"}
        area.update(overrides)
        return area

    async def test_both_have_to_hold(self, hass):
        hass.states.async_set("binary_sensor.warm", "on")
        hass.states.async_set("binary_sensor.home", "on")
        assert close_condition_met(hass, self._area(), {}) is True

        hass.states.async_set("binary_sensor.home", "off")
        assert close_condition_met(hass, self._area(), {}) is False

    async def test_the_first_alone_still_decides(self, hass):
        """Bestandsanlagen haben nur die erste – die muss unverändert wirken."""
        from custom_components.shutter_pilot.const import CLOSE_CONDITION_SLOT

        entity_key = sun_condition_keys(CLOSE_CONDITION_SLOT)[0]
        area = {CONF_AREA_ID: "living", entity_key: "binary_sensor.warm"}

        hass.states.async_set("binary_sensor.warm", "on")
        assert close_condition_met(hass, area, {}) is True
        hass.states.async_set("binary_sensor.warm", "off")
        assert close_condition_met(hass, area, {}) is False

    async def test_the_second_alone_works_too(self, hass):
        hass.states.async_set("binary_sensor.home", "on")
        area = self._area()
        del area[sun_condition_keys("close")[0]]
        assert close_condition_met(hass, area, {}) is True

    async def test_dead_sensor_keeps_the_shutters_closing(self, hass):
        """Fail closed: ein toter Sensor darf nicht alles halb offen lassen."""
        hass.states.async_set("binary_sensor.warm", "on")
        hass.states.async_set("binary_sensor.home", "unavailable")
        assert close_condition_met(hass, self._area(), {}) is False
