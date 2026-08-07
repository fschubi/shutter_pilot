"""Sonnenrelative Grenzen im Helligkeitsmodus.

Der Fall aus dem Forum: Ein Gewitter am Nachmittag drückt die Helligkeit unter
die Schwelle, und die Rollläden schließen am helllichten Tag. Die Uhrzeitfenster
können „frühestens ab Sonnenuntergang minus 60 Minuten" nicht ausdrücken, weil
der Sonnenuntergang durchs Jahr wandert.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest
from homeassistant.util import dt as dt_util
from zoneinfo import ZoneInfo

from custom_components.shutter_pilot.brightness import _area_window, _sun_bound_ok
from custom_components.shutter_pilot.const import (
    CONF_AREA_B_DOWN_AFTER_SUNSET,
    CONF_AREA_B_UP_BEFORE_SUNRISE,
    CONF_AREA_ID,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
)

BERLIN = ZoneInfo("Europe/Berlin")
# Montag, 3. August 2026. Sonnenaufgang 06:07, Sonnenuntergang 21:10 Ortszeit.
SUNRISE = datetime(2026, 8, 3, 6, 7, tzinfo=BERLIN)
SUNSET = datetime(2026, 8, 3, 21, 10, tzinfo=BERLIN)


@pytest.fixture(autouse=True)
async def _berlin(hass):
    await hass.config.async_set_time_zone("Europe/Berlin")


def _set_sun(hass) -> None:
    """Wie das echte Home Assistant: in UTC."""
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 30.0,
            "azimuth": 180.0,
            "next_rising": SUNRISE.astimezone(UTC).isoformat(),
            "next_setting": SUNSET.astimezone(UTC).isoformat(),
        },
    )


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 3, hour, minute, tzinfo=BERLIN)


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_W_UP_FROM: "05:00",
        CONF_AREA_W_UP_TO: "09:00",
        CONF_AREA_W_DOWN_FROM: "16:00",
        CONF_AREA_W_DOWN_TO: "23:59",
    }
    area.update(overrides)
    return area


class TestDownBound:
    """„Runter frühestens ab Sonnenuntergang minus 60 Minuten" (21:10 → 20:10)."""

    async def test_thunderstorm_at_noon_does_not_close(self, hass):
        _set_sun(hass)
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: 60})
        assert _area_window(area, _at(17, 0), "down", hass) is False

    async def test_evening_is_allowed(self, hass):
        _set_sun(hass)
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: 60})
        assert _area_window(area, _at(20, 30), "down", hass) is True

    async def test_exactly_on_the_bound(self, hass):
        _set_sun(hass)
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: 60})
        assert _area_window(area, _at(20, 10), "down", hass) is True
        assert _area_window(area, _at(20, 9), "down", hass) is False

    async def test_offset_zero_means_sunset_itself(self, hass):
        _set_sun(hass)
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: 0})
        assert _area_window(area, _at(21, 0), "down", hass) is False
        assert _area_window(area, _at(21, 15), "down", hass) is True

    async def test_the_clock_window_still_applies(self, hass):
        """Die Sonnengrenze kommt *zusätzlich*, sie ersetzt nichts."""
        _set_sun(hass)
        area = _area(
            **{CONF_AREA_B_DOWN_AFTER_SUNSET: 60, CONF_AREA_W_DOWN_TO: "20:30"}
        )
        assert _area_window(area, _at(20, 20), "down", hass) is True
        assert _area_window(area, _at(20, 45), "down", hass) is False, "Fenster zu"


class TestUpBound:
    async def test_up_is_blocked_before_the_bound(self, hass):
        _set_sun(hass)
        area = _area(**{CONF_AREA_B_UP_BEFORE_SUNRISE: 30})  # 05:37
        assert _area_window(area, _at(5, 20), "up", hass) is False
        assert _area_window(area, _at(5, 45), "up", hass) is True


class TestNotConfigured:
    """Ohne Eintrag muss sich nichts ändern."""

    @pytest.mark.parametrize("value", [None, "", "abc"])
    async def test_unset_never_blocks(self, hass, value):
        _set_sun(hass)
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: value})
        assert _area_window(area, _at(17, 0), "down", hass) is True

    async def test_missing_key(self, hass):
        _set_sun(hass)
        assert _area_window(_area(), _at(17, 0), "down", hass) is True

    async def test_without_sun_entity_it_fails_open(self, hass):
        """Kein sun.sun: nie blockieren – wie überall sonst."""
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: 60})
        assert _sun_bound_ok(hass, area, _at(17, 0), "down") is True

    async def test_without_hass_it_fails_open(self):
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: 60})
        assert _sun_bound_ok(None, area, _at(17, 0), "down") is True


class TestTimezone:
    async def test_bound_is_computed_in_local_time(self, hass):
        """Die Sonnenzeiten kommen in UTC – 20:10 muss Ortszeit sein."""
        _set_sun(hass)
        area = _area(**{CONF_AREA_B_DOWN_AFTER_SUNSET: 60})
        # 19:00 Ortszeit ist 17:00 UTC. Würde in UTC gerechnet, wäre die
        # Schranke schon überschritten und der Rollladen führe zu früh.
        assert _area_window(area, _at(19, 0), "down", hass) is False
