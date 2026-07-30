"""Tests for the brightness time windows.

The CHANGELOG shows two separate regressions in this area (1.4.42 and 2.0.40),
so the window logic is pinned down here.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from custom_components.shutter_pilot.brightness import _area_window
from custom_components.shutter_pilot.const import (
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_DOWN_TO,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WE_UP_TO,
    CONF_AREA_WORKDAY_SENSOR,
)


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_W_UP_FROM: "05:00",
        CONF_AREA_W_UP_TO: "09:00",
        CONF_AREA_W_DOWN_FROM: "16:00",
        CONF_AREA_W_DOWN_TO: "23:59",
        CONF_AREA_WE_UP_FROM: "07:00",
        CONF_AREA_WE_UP_TO: "10:00",
        CONF_AREA_WE_DOWN_FROM: "16:00",
        CONF_AREA_WE_DOWN_TO: "23:59",
    }
    area.update(overrides)
    return area


def _monday(hour: int, minute: int = 0) -> datetime:
    return datetime(2025, 7, 7, hour, minute)


def _saturday(hour: int, minute: int = 0) -> datetime:
    return datetime(2025, 7, 12, hour, minute)


class TestUpWindow:
    @pytest.mark.parametrize(
        ("hour", "expected"),
        [(4, False), (5, True), (7, True), (9, True), (10, False)],
    )
    def test_weekday(self, hour, expected):
        assert _area_window(_area(), _monday(hour), "up") is expected

    @pytest.mark.parametrize(
        ("hour", "expected"),
        [(6, False), (7, True), (10, True), (11, False)],
    )
    def test_weekend(self, hour, expected):
        assert _area_window(_area(), _saturday(hour), "up") is expected


class TestDownWindow:
    @pytest.mark.parametrize(
        ("hour", "expected"),
        [(8, False), (15, False), (16, True), (23, True)],
    )
    def test_weekday(self, hour, expected):
        assert _area_window(_area(), _monday(hour), "down") is expected

    def test_morning_lux_does_not_close(self):
        """Regression 1.4.42: a dark morning must not trigger the down logic."""
        assert _area_window(_area(), _monday(6), "down") is False


class TestWrappingWindow:
    def test_window_across_midnight(self):
        area = _area(**{CONF_AREA_W_DOWN_FROM: "22:00", CONF_AREA_W_DOWN_TO: "02:00"})
        assert _area_window(area, _monday(23), "down") is True
        assert _area_window(area, _monday(1), "down") is True
        assert _area_window(area, _monday(12), "down") is False


class TestWorkdaySensorIntegration:
    async def test_holiday_uses_weekend_window(self, hass):
        """On a holiday Monday, 06:00 must not yet be inside the up window."""
        hass.states.async_set("binary_sensor.workday", "off")
        area = _area(**{CONF_AREA_WORKDAY_SENSOR: "binary_sensor.workday"})
        assert _area_window(area, _monday(6), "up", hass) is False
        assert _area_window(area, _monday(8), "up", hass) is True

    async def test_without_hass_uses_calendar(self, hass):
        area = _area(**{CONF_AREA_WORKDAY_SENSOR: "binary_sensor.workday"})
        assert _area_window(area, _monday(6), "up") is True
