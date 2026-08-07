"""Beschattung bei getrennten Hoch- und Runter-Bereichen (GitHub #4).

Gemeldet als „Rollo fährt alle 60 Sekunden zwischen offen und
Sonnenschutzposition". Ursache: Die Beschattung wurde vom Runter-Bereich
gesetzt, aber vom Hoch-Bereich freigegeben. Widersprachen sich deren
Konfigurationen, hoben sich beide im Minutentakt gegenseitig auf.

Getrennte Bereiche für Hoch und Runter sind ein Kernfeature – morgens
raumweise, abends gemeinsam –, deshalb ist der Fall alles andere als exotisch.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import cover_tracker, elevation
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    CONF_SUN_GEOMETRY_OVERRIDE,
    DOMAIN,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    is_cover_sun_protected,
    is_sun_protect_active,
)

COVER = "cover.west"
RADIATION = "sensor.strahlung"


@pytest.fixture(autouse=True)
def _fast_startup_restore(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


def _area(area_id: str, **overrides) -> dict:
    """Bereich mit vitals5' Zahlen: Elevation 0–90, Fensterrichtung Süd."""
    area = {
        CONF_AREA_ID: area_id,
        CONF_AREA_NAME: area_id,
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_MIN: 0,
        CONF_AREA_ELEVATION_MAX: 90,
        CONF_AREA_AZIMUTH_ENABLED: True,
        CONF_AREA_AZIMUTH_MIN: 100,
        CONF_AREA_AZIMUTH_MAX: 275,
    }
    area.update(overrides)
    return area


def _shutter(up_id: str, down_id: str, **overrides) -> dict:
    """Rollladen mit eigener Ausrichtung nach Westen (225–315)."""
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "West",
        CONF_AREA_UP_ID: up_id,
        CONF_AREA_DOWN_ID: down_id,
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_SUN_PROTECT: 50,
        CONF_SUN_GEOMETRY_OVERRIDE: True,
        CONF_AREA_ELEVATION_MIN: 0,
        CONF_AREA_ELEVATION_MAX: 90,
        CONF_AREA_AZIMUTH_ENABLED: True,
        CONF_AREA_AZIMUTH_MIN: 225,
        CONF_AREA_AZIMUTH_MAX: 315,
    }
    shutter.update(overrides)
    return shutter


def _with_condition(area: dict, on_above: float) -> dict:
    entity_key, on_key, _off, _s = sun_condition_keys("a")
    area = dict(area)
    area[entity_key] = RADIATION
    area[on_key] = on_above
    return area


@pytest.fixture
def cover_calls(hass):
    calls: list = []

    async def _handler(call):
        calls.append(call)
        position = call.data["position"]
        entity_id = call.data["entity_id"]
        for eid in [entity_id] if isinstance(entity_id, str) else entity_id:
            hass.states.async_set(
                eid,
                "closed" if position <= 0 else "open",
                {"current_position": position, "supported_features": 15},
            )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return calls


def _positions(calls) -> list[int]:
    return [call.data["position"] for call in calls]


async def _setup(hass, areas: list[dict], shutters: list[dict]):
    hass.states.async_set(
        COVER, "open", {"current_position": 100, "supported_features": 15}
    )
    # Sonne im Westen: 284° – innerhalb der Rollladen-Ausrichtung (225–315),
    # ausserhalb der des Bereichs (100–275).
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 10.3,
            "azimuth": 284.0,
            "next_rising": "2026-08-04T04:00:00+00:00",
            "next_setting": "2026-08-03T19:00:00+00:00",
        },
    )
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: areas, CONF_SHUTTERS: shutters},
    )
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry, hass.data[DOMAIN][config_entry.entry_id]


async def _ticks(hass, data, count: int = 3) -> None:
    """Den gemeinsamen Minutentakt so auslösen, wie Home Assistant es tut."""
    from homeassistant.util import dt as dt_util

    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()


class TestSplitAreas:
    async def test_no_oscillation_when_areas_disagree(self, hass, cover_calls):
        """Der gemeldete Fall: Hoch- und Runter-Bereich widersprechen sich.

        Der Hoch-Bereich verlangt eine Bedingung, die nicht erfüllt ist. Früher
        beschattete der Runter-Bereich und der Hoch-Bereich gab sofort wieder
        frei – 50, 100, 50, 100 im Minutentakt.
        """
        hass.states.async_set(RADIATION, 100)  # unter der Schwelle
        areas = [_area("abends"), _with_condition(_area("morgens"), 500)]
        _entry, data = await _setup(
            hass, areas, [_shutter(up_id="morgens", down_id="abends")]
        )
        await _ticks(hass, data)

        assert _positions(cover_calls) == [50], "einmal beschatten, dann Ruhe"
        assert is_cover_sun_protected(data, COVER)

    async def test_down_area_decides_the_release(self, hass, cover_calls):
        """Fällt die Bedingung des *Runter*-Bereichs weg, wird freigegeben."""
        hass.states.async_set(RADIATION, 800)  # über der Schwelle
        areas = [_with_condition(_area("abends"), 500), _area("morgens")]
        _entry, data = await _setup(
            hass, areas, [_shutter(up_id="morgens", down_id="abends")]
        )
        await _ticks(hass, data)
        assert _positions(cover_calls) == [50]

        hass.states.async_set(RADIATION, 100)  # Wolke zieht durch
        await _ticks(hass, data)
        assert _positions(cover_calls) == [50, 100], "genau einmal auffahren"
        assert not is_cover_sun_protected(data, COVER)

    async def test_area_aggregate_matches_the_covers(self, hass, cover_calls):
        """Der Bereichswert lief aus dem Tritt und blockierte Hochfahrten."""
        hass.states.async_set(RADIATION, 100)
        areas = [_area("abends"), _with_condition(_area("morgens"), 500)]
        _entry, data = await _setup(
            hass, areas, [_shutter(up_id="morgens", down_id="abends")]
        )
        await _ticks(hass, data)

        assert is_sun_protect_active(data, "abends") is True
        assert is_sun_protect_active(data, "morgens") is False, "kein Runter-Rollladen"
        assert data["sun_protect_covers"] == {COVER}


class TestSingleArea:
    """Der einfache Fall muss sich unverändert verhalten."""

    async def test_shades_once_and_stays(self, hass, cover_calls):
        _entry, data = await _setup(
            hass, [_area("gruppe")], [_shutter(up_id="gruppe", down_id="gruppe")]
        )
        await _ticks(hass, data, count=5)
        assert _positions(cover_calls) == [50]

    async def test_releases_when_the_sun_moves_on(self, hass, cover_calls):
        _entry, data = await _setup(
            hass, [_area("gruppe")], [_shutter(up_id="gruppe", down_id="gruppe")]
        )
        await _ticks(hass, data)
        assert _positions(cover_calls) == [50]

        # Sonne wandert aus der Fensterrichtung des Rollladens (225–315).
        hass.states.async_set(
            "sun.sun",
            "above_horizon",
            {
                "elevation": 10.3,
                "azimuth": 120.0,
                "next_rising": "2026-08-04T04:00:00+00:00",
                "next_setting": "2026-08-03T19:00:00+00:00",
            },
        )
        await _ticks(hass, data)
        assert _positions(cover_calls) == [50, 100]


class TestStaleFlag:
    async def test_flag_is_dropped_when_the_area_stops_shading(
        self, hass, cover_calls
    ):
        """Sonst blockiert der Restwert dauerhaft das automatische Hochfahren."""
        _entry, data = await _setup(
            hass, [_area("gruppe")], [_shutter(up_id="gruppe", down_id="gruppe")]
        )
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)

        # Der Rollladen schliesst jetzt über einen Bereich ohne Beschattung.
        data["shutters"] = [_shutter(up_id="gruppe", down_id="ohne")]
        hass.config_entries.async_update_entry(
            _entry,
            options={
                CONF_AREAS: [_area("gruppe"), _area("ohne", **{
                    CONF_AREA_SUN_PROTECT_ENABLED: False
                })],
                CONF_SHUTTERS: [_shutter(up_id="gruppe", down_id="ohne")],
            },
        )
        await hass.async_block_till_done()
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
