"""Tests for the schedule maths: weekday detection, jitter, trigger times."""

from __future__ import annotations

from datetime import date, datetime, time

import pytest

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_RANDOM_OFFSET,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_TIME_WE_DOWN,
    CONF_AREA_TIME_WE_UP,
    CONF_AREA_WORKDAY_SENSOR,
)
from custom_components.shutter_pilot.schedule_times import (
    get_random_offset,
    get_time_mode_triggers,
    is_weekend_schedule,
    parse_time,
)

MONDAY = datetime(2025, 7, 7, 12, 0)  # a Monday
SATURDAY = datetime(2025, 7, 12, 12, 0)  # a Saturday


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_TIME_WE_UP: "09:00",
        CONF_AREA_TIME_WE_DOWN: "21:00",
    }
    area.update(overrides)
    return area


class TestParseTime:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("07:30", time(7, 30)),
            ("00:00", time(0, 0)),
            ("23:59", time(23, 59)),
            ("7:5", time(7, 5)),
        ],
    )
    def test_valid(self, raw, expected):
        assert parse_time(raw) == expected

    @pytest.mark.parametrize("raw", ["", None, "abc", "25:00", "12:99", "12"])
    def test_invalid_uses_fallback(self, raw):
        assert parse_time(raw, time(8, 15)) == time(8, 15)


class TestWeekendDetection:
    def test_calendar_weekday(self):
        assert is_weekend_schedule(None, _area(), MONDAY) is False

    def test_calendar_weekend(self):
        assert is_weekend_schedule(None, _area(), SATURDAY) is True

    async def test_workday_sensor_off_forces_weekend(self, hass):
        """A public holiday on a Monday must use the weekend schedule."""
        hass.states.async_set("binary_sensor.workday", "off")
        area = _area(**{CONF_AREA_WORKDAY_SENSOR: "binary_sensor.workday"})
        assert is_weekend_schedule(hass, area, MONDAY) is True

    async def test_workday_sensor_on_forces_weekday(self, hass):
        """Shift work: a Saturday that is a working day uses the weekday plan."""
        hass.states.async_set("binary_sensor.workday", "on")
        area = _area(**{CONF_AREA_WORKDAY_SENSOR: "binary_sensor.workday"})
        assert is_weekend_schedule(hass, area, SATURDAY) is False

    async def test_unavailable_sensor_falls_back_to_calendar(self, hass):
        hass.states.async_set("binary_sensor.workday", "unavailable")
        area = _area(**{CONF_AREA_WORKDAY_SENSOR: "binary_sensor.workday"})
        assert is_weekend_schedule(hass, area, SATURDAY) is True
        assert is_weekend_schedule(hass, area, MONDAY) is False

    async def test_missing_sensor_falls_back_to_calendar(self, hass):
        area = _area(**{CONF_AREA_WORKDAY_SENSOR: "binary_sensor.does_not_exist"})
        assert is_weekend_schedule(hass, area, MONDAY) is False


class TestRandomOffset:
    def test_disabled_by_default(self):
        assert get_random_offset(_area(), date(2025, 7, 7), "up") == 0

    def test_zero_means_off(self):
        area = _area(**{CONF_AREA_RANDOM_OFFSET: 0})
        assert get_random_offset(area, date(2025, 7, 7), "up") == 0

    def test_deterministic_for_same_day(self):
        """Scheduler and sensor must agree, so repeated calls must match."""
        area = _area(**{CONF_AREA_RANDOM_OFFSET: 15})
        day = date(2025, 7, 7)
        first = get_random_offset(area, day, "up")
        assert all(get_random_offset(area, day, "up") == first for _ in range(20))

    def test_within_configured_span(self):
        area = _area(**{CONF_AREA_RANDOM_OFFSET: 15})
        for day_num in range(1, 29):
            value = get_random_offset(area, date(2025, 7, day_num), "up")
            assert -15 <= value <= 15

    def test_differs_across_days(self):
        area = _area(**{CONF_AREA_RANDOM_OFFSET: 30})
        values = {get_random_offset(area, date(2025, 7, d), "up") for d in range(1, 29)}
        assert len(values) > 1

    def test_up_and_down_are_independent(self):
        area = _area(**{CONF_AREA_RANDOM_OFFSET: 30})
        day = date(2025, 7, 7)
        ups = get_random_offset(area, day, "up")
        downs = get_random_offset(area, day, "down")
        # Not a strict requirement per day, but they must not be hard-wired equal.
        differing = [
            get_random_offset(area, date(2025, 7, d), "up")
            != get_random_offset(area, date(2025, 7, d), "down")
            for d in range(1, 29)
        ]
        assert any(differing)
        assert isinstance(ups, int) and isinstance(downs, int)

    def test_span_is_capped(self):
        area = _area(**{CONF_AREA_RANDOM_OFFSET: 9999})
        assert -120 <= get_random_offset(area, date(2025, 7, 7), "up") <= 120

    def test_invalid_value_is_ignored(self):
        area = _area(**{CONF_AREA_RANDOM_OFFSET: "nonsense"})
        assert get_random_offset(area, date(2025, 7, 7), "up") == 0


class TestTimeModeTriggers:
    def test_weekday_times(self):
        up, down = get_time_mode_triggers(None, _area(), MONDAY)
        assert (up, down) == (time(7, 0), time(19, 0))

    def test_weekend_times(self):
        up, down = get_time_mode_triggers(None, _area(), SATURDAY)
        assert (up, down) == (time(9, 0), time(21, 0))

    def test_weekend_falls_back_to_weekday_when_unset(self):
        area = _area(**{CONF_AREA_TIME_WE_UP: "", CONF_AREA_TIME_WE_DOWN: ""})
        up, down = get_time_mode_triggers(None, area, SATURDAY)
        assert (up, down) == (time(7, 0), time(19, 0))

    def test_jitter_shifts_but_stays_in_day(self):
        area = _area(**{CONF_AREA_TIME_UP: "00:05", CONF_AREA_RANDOM_OFFSET: 60})
        up, _ = get_time_mode_triggers(None, area, MONDAY)
        assert time(0, 0) <= up <= time(1, 5)
