"""Tests for the earliest/latest clock bounds in sun mode.

MartyBr's case from the forum: drive by sun elevation, but not before 07:30
on weekdays and 08:00 at weekends, and never later than 09:00.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

import pytest
from homeassistant.util import dt as dt_util

from custom_components.shutter_pilot.const import (
    AREA_MODE_SUN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_SUN_EARLIEST_DOWN,
    CONF_AREA_SUN_EARLIEST_UP,
    CONF_AREA_SUN_LATEST_DOWN,
    CONF_AREA_SUN_LATEST_UP,
    CONF_AREA_SUN_WE_EARLIEST_UP,
    CONF_AREA_SUNRISE_OFFSET,
    CONF_AREA_SUNSET_OFFSET,
)
from custom_components.shutter_pilot.schedule_times import (
    clamp_to_bounds,
    get_sun_mode_triggers,
)

MONDAY = datetime(2026, 8, 3, 12, 0)
SATURDAY = datetime(2026, 8, 8, 12, 0)


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_MODE: AREA_MODE_SUN,
        CONF_AREA_SUNRISE_OFFSET: 0,
        CONF_AREA_SUNSET_OFFSET: 0,
    }
    area.update(overrides)
    return area


@pytest.fixture(autouse=True)
async def _local_timezone(hass):
    """Run these tests in Berlin.

    The default test timezone is US/Pacific, but MartyBr's and Xerenas' cases
    only read right in local time. More importantly: a zone other than UTC is
    what makes a missing as_local() visible at all.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")


def _set_sun(hass, rising: str, setting: str) -> None:
    """Publish sun times given as local clock time.

    Home Assistant stores these attributes in UTC, so that is what the tests
    have to inject – with local offsets the timezone bug stayed invisible.
    """
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 30.0,
            "azimuth": 180.0,
            "next_rising": dt_util.parse_datetime(rising).astimezone(UTC).isoformat(),
            "next_setting": dt_util.parse_datetime(setting).astimezone(UTC).isoformat(),
        },
    )


def _hm(moment: datetime) -> tuple[int, int]:
    """Compare in local time – a UTC value with the right digits is still wrong."""
    local = dt_util.as_local(moment)
    return local.hour, local.minute


class TestClampHelper:
    def test_before_earliest_is_pulled_up(self):
        moment = datetime(2026, 8, 3, 5, 12)
        out = clamp_to_bounds(moment, time(7, 30), time(9, 0))
        assert out.hour == 7 and out.minute == 30

    def test_after_latest_is_pulled_down(self):
        moment = datetime(2026, 8, 3, 10, 45)
        out = clamp_to_bounds(moment, time(7, 30), time(9, 0))
        assert out.hour == 9 and out.minute == 0

    def test_inside_window_untouched(self):
        moment = datetime(2026, 8, 3, 8, 17)
        assert clamp_to_bounds(moment, time(7, 30), time(9, 0)) == moment

    def test_without_bounds_untouched(self):
        moment = datetime(2026, 8, 3, 4, 3)
        assert clamp_to_bounds(moment, None, None) == moment

    def test_only_earliest(self):
        moment = datetime(2026, 8, 3, 4, 3)
        assert clamp_to_bounds(moment, time(7, 0), None).hour == 7
        assert clamp_to_bounds(datetime(2026, 8, 3, 23, 0), time(7, 0), None).hour == 23

    def test_seconds_are_cleared(self):
        moment = datetime(2026, 8, 3, 5, 12, 44)
        assert clamp_to_bounds(moment, time(7, 30), None).second == 0


class TestSunModeWithBounds:
    async def test_early_sunrise_is_held_back(self, hass):
        """Midsummer: the sun is up at 05:10, the shutters wait until 07:30."""
        _set_sun(hass, "2026-08-03T05:10:00+02:00", "2026-08-03T21:30:00+02:00")
        area = _area(**{CONF_AREA_SUN_EARLIEST_UP: "07:30"})
        up, _ = get_sun_mode_triggers(hass, area, MONDAY)
        assert _hm(up) == (7, 30)

    async def test_late_sunrise_is_capped(self, hass):
        """Midwinter: sunrise at 08:40 would be too late, so 09:00 caps it."""
        _set_sun(hass, "2026-08-03T10:40:00+02:00", "2026-08-03T16:30:00+02:00")
        area = _area(**{CONF_AREA_SUN_EARLIEST_UP: "07:30", CONF_AREA_SUN_LATEST_UP: "09:00"})
        up, _ = get_sun_mode_triggers(hass, area, MONDAY)
        assert _hm(up) == (9, 0)

    async def test_inside_window_keeps_sun_time(self, hass):
        _set_sun(hass, "2026-08-03T08:15:00+02:00", "2026-08-03T20:00:00+02:00")
        area = _area(**{CONF_AREA_SUN_EARLIEST_UP: "07:30", CONF_AREA_SUN_LATEST_UP: "09:00"})
        up, _ = get_sun_mode_triggers(hass, area, MONDAY)
        assert _hm(up) == (8, 15)

    async def test_without_bounds_unchanged(self, hass):
        """Existing setups must not shift at all."""
        _set_sun(hass, "2026-08-03T05:10:00+02:00", "2026-08-03T21:30:00+02:00")
        up, _ = get_sun_mode_triggers(hass, _area(), MONDAY)
        assert _hm(up) == (5, 10)

    async def test_evening_bounds(self, hass):
        _set_sun(hass, "2026-08-03T05:10:00+02:00", "2026-08-03T16:05:00+02:00")
        area = _area(**{CONF_AREA_SUN_EARLIEST_DOWN: "17:00", CONF_AREA_SUN_LATEST_DOWN: "22:30"})
        _, down = get_sun_mode_triggers(hass, area, MONDAY)
        assert _hm(down) == (17, 0)

    async def test_offset_is_applied_before_clamping(self, hass):
        _set_sun(hass, "2026-08-03T07:00:00+02:00", "2026-08-03T21:00:00+02:00")
        area = _area(**{CONF_AREA_SUNRISE_OFFSET: 60, CONF_AREA_SUN_LATEST_UP: "07:30"})
        up, _ = get_sun_mode_triggers(hass, area, MONDAY)
        # 07:00 + 60 min = 08:00, capped to 07:30
        assert _hm(up) == (7, 30)


class TestWeekend:
    async def test_weekend_value_wins_on_saturday(self, hass):
        _set_sun(hass, "2026-08-08T05:10:00+02:00", "2026-08-08T21:30:00+02:00")
        area = _area(
            **{CONF_AREA_SUN_EARLIEST_UP: "07:30", CONF_AREA_SUN_WE_EARLIEST_UP: "08:00"}
        )
        up, _ = get_sun_mode_triggers(hass, area, SATURDAY)
        assert _hm(up) == (8, 0)

    async def test_weekday_value_used_on_monday(self, hass):
        _set_sun(hass, "2026-08-03T05:10:00+02:00", "2026-08-03T21:30:00+02:00")
        area = _area(
            **{CONF_AREA_SUN_EARLIEST_UP: "07:30", CONF_AREA_SUN_WE_EARLIEST_UP: "08:00"}
        )
        up, _ = get_sun_mode_triggers(hass, area, MONDAY)
        assert _hm(up) == (7, 30)

    async def test_empty_weekend_falls_back_to_weekday(self, hass):
        """Same fallback the weekday/weekend times already use."""
        _set_sun(hass, "2026-08-08T05:10:00+02:00", "2026-08-08T21:30:00+02:00")
        area = _area(**{CONF_AREA_SUN_EARLIEST_UP: "07:30", CONF_AREA_SUN_WE_EARLIEST_UP: ""})
        up, _ = get_sun_mode_triggers(hass, area, SATURDAY)
        assert _hm(up) == (7, 30)


class TestMartyBrScenario:
    """The exact setup described in the forum."""

    @pytest.mark.parametrize(
        ("day", "sunrise", "expected"),
        [
            (MONDAY, "2026-08-03T05:10:00+02:00", (7, 30)),   # summer, held back
            (SATURDAY, "2026-08-08T05:10:00+02:00", (8, 0)),  # summer weekend
            (MONDAY, "2026-08-03T08:00:00+02:00", (8, 0)),    # spring, sun decides
            (MONDAY, "2026-08-03T09:40:00+02:00", (9, 0)),    # winter, capped
        ],
    )
    async def test_earliest_730_weekday_800_weekend_latest_900(
        self, hass, day, sunrise, expected
    ):
        _set_sun(hass, sunrise, "2026-08-03T20:00:00+02:00")
        area = _area(
            **{
                CONF_AREA_SUN_EARLIEST_UP: "07:30",
                CONF_AREA_SUN_WE_EARLIEST_UP: "08:00",
                CONF_AREA_SUN_LATEST_UP: "09:00",
            }
        )
        up, _ = get_sun_mode_triggers(hass, area, day)
        assert _hm(up) == expected


class TestXerenasScenario:
    """Sun times arrive in UTC – the bounds are meant in local time.

    Xerenas reported a drive at 23:00 for a sunset of 21:10 with "not before
    21:00". The bound was applied to the UTC wall clock, so 21:00 became
    21:00 UTC = 23:00 in Berlin.
    """

    async def test_utc_attribute_is_read_as_local(self, hass):
        # Written out in UTC on purpose: no helper in between that could
        # paper over a missing conversion.
        hass.states.async_set(
            "sun.sun",
            "above_horizon",
            {
                "elevation": 30.0,
                "azimuth": 180.0,
                "next_rising": "2026-08-03T04:07:00+00:00",
                "next_setting": "2026-08-03T19:10:00+00:00",
            },
        )
        area = _area(**{CONF_AREA_SUN_EARLIEST_DOWN: "21:00"})
        _, down = get_sun_mode_triggers(hass, area, MONDAY)
        # Sunset is 21:10 local, so the 21:00 bound must not move it at all.
        assert _hm(down) == (21, 10)
        assert down.utcoffset() == timedelta(hours=2)

    async def test_morning_bound_is_local(self, hass):
        """Xerenas' first report: sunrise 06:07, "up no earlier than 07:30"."""
        hass.states.async_set(
            "sun.sun",
            "above_horizon",
            {
                "elevation": 30.0,
                "azimuth": 180.0,
                "next_rising": "2026-08-03T04:07:00+00:00",
                "next_setting": "2026-08-03T19:10:00+00:00",
            },
        )
        area = _area(**{CONF_AREA_SUN_EARLIEST_UP: "07:30"})
        up, _ = get_sun_mode_triggers(hass, area, MONDAY)
        assert _hm(up) == (7, 30)


class TestDateRollover:
    async def test_evening_trigger_keeps_the_local_date(self, hass):
        """A sunset that is already tomorrow in UTC still belongs to today.

        The scheduler only drives when trigger_down.date() equals today's local
        date – with a UTC value the evening drive silently never ran.
        """
        await hass.config.async_set_time_zone("America/New_York")
        hass.states.async_set(
            "sun.sun",
            "above_horizon",
            {
                "elevation": 30.0,
                "azimuth": 180.0,
                "next_rising": "2026-08-03T10:00:00+00:00",
                "next_setting": "2026-08-04T00:10:00+00:00",  # 3 Aug 20:10 local
            },
        )
        _, down = get_sun_mode_triggers(hass, _area(), datetime(2026, 8, 3, 12, 0))
        assert down.date() == date(2026, 8, 3)
        assert _hm(down) == (20, 10)
