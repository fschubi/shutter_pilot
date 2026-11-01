"""Mehrstufiger Sonnenschutz (Raffstore, Stufe 5, simon42 #172 Claus).

Bis zu drei Stufen ueber der normalen Beschattung: die Bedingung je Stufe am
Bereich (Slot sp_l1..3), Position und Lamellen je Stufe am Rollladen. Die
hoechste zutreffende Stufe gewinnt, auch gegen sp_alt. Ohne Stufen am Rollladen
aendert sich nichts - das ist der Bestandsschutz-Teil."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SHADE_LEVEL_HOLD,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_KEEP_POSITION_SUN_PROTECT_LEVELS,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_POSITION_SUN_PROTECT_ALT,
    CONF_POSITION_SUN_PROTECT_LEVELS,
    CONF_SHUTTERS,
    CONF_TILT_ENABLED,
    CONF_TILT_SUN_PROTECT,
    CONF_TILT_SUN_PROTECT_LEVELS,
    DOMAIN,
    ROLE_SUN_PROTECT,
    ROLE_SUN_PROTECT_ALT,
    ROLE_SUN_PROTECT_LEVELS,
    sun_condition_keys,
)
from custom_components.shutter_pilot.export import async_build_export
from custom_components.shutter_pilot.helpers import (
    get_tilt_for_role,
    resolve_shade_position,
)

COVER = "cover.raff_sued"
L1, L2, L3 = ("input_boolean.stufe1", "input_boolean.stufe2", "input_boolean.stufe3")

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Sued",
    CONF_AREA_UP_ID: "sued",
    CONF_AREA_DOWN_ID: "sued",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
    CONF_POSITION_SUN_PROTECT: 50,
    CONF_POSITION_SUN_PROTECT_LEVELS[0]: 40,
    CONF_POSITION_SUN_PROTECT_LEVELS[1]: 25,
    CONF_POSITION_SUN_PROTECT_LEVELS[2]: 10,
}


def _area(**extra) -> dict:
    area = {
        CONF_AREA_ID: "sued",
        CONF_AREA_NAME: "Sued",
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_MIN: 0,
        CONF_AREA_ELEVATION_MAX: 90,
        CONF_AREA_AZIMUTH_ENABLED: False,
        sun_condition_keys("sp_l1")[0]: L1,
        sun_condition_keys("sp_l2")[0]: L2,
        sun_condition_keys("sp_l3")[0]: L3,
    }
    area.update(extra)
    return area


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def calls(hass):
    pos: list = []
    tilt = async_mock_service(hass, "cover", "set_cover_tilt_position")

    async def _handler(call):
        pos.append(call)
        hass.states.async_set(
            call.data["entity_id"],
            "open",
            {"current_position": call.data["position"], "supported_features": 255},
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return {"pos": pos, "tilt": tilt}


def _flags(hass, l1="off", l2="off", l3="off") -> None:
    for entity, value in ((L1, l1), (L2, l2), (L3, l3)):
        hass.states.async_set(entity, value)


async def _setup(hass, area=None, shutter=None):
    _flags(hass)
    hass.states.async_set(
        COVER, "open", {"current_position": 100, "supported_features": 255}
    )
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 41.0,
            "azimuth": 198.0,
            "next_rising": "2026-08-29T04:00:00+00:00",
            "next_setting": "2026-08-28T19:00:00+00:00",
        },
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [area or _area()],
            CONF_SHUTTERS: [shutter or dict(SHUTTER)],
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _ticks(hass, data, count: int = 2) -> None:
    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()


def _positions(calls_) -> list:
    return [c.data["position"] for c in calls_["pos"]]


# --- Auswahl der Stufe ---------------------------------------------------------


class TestPicksTheHighestLevel:
    async def test_without_a_condition_the_plain_position_applies(self, hass, calls):
        entry, data = await _setup(hass)
        area, shutter = _area(), dict(SHUTTER)
        assert resolve_shade_position(hass, area, shutter, data) == (
            50.0,
            ROLE_SUN_PROTECT,
        )

    async def test_each_level_when_its_condition_holds(self, hass, calls):
        _, data = await _setup(hass)
        area, shutter = _area(), dict(SHUTTER)
        _flags(hass, l1="on")
        assert resolve_shade_position(hass, area, shutter, data) == (
            40.0,
            ROLE_SUN_PROTECT_LEVELS[0],
        )
        _flags(hass, l1="on", l2="on")
        assert resolve_shade_position(hass, area, shutter, data) == (
            25.0,
            ROLE_SUN_PROTECT_LEVELS[1],
        )
        _flags(hass, l1="on", l2="on", l3="on")
        assert resolve_shade_position(hass, area, shutter, data)[0] == 10.0

    async def test_the_highest_wins_even_when_a_lower_one_is_off(self, hass, calls):
        _, data = await _setup(hass)
        _flags(hass, l3="on")
        assert resolve_shade_position(hass, _area(), dict(SHUTTER), data)[0] == 10.0

    async def test_a_level_beats_the_second_position(self, hass, calls):
        _, data = await _setup(hass)
        hass.states.async_set("input_boolean.hitze", "on")
        area = _area(**{sun_condition_keys("sp_alt")[0]: "input_boolean.hitze"})
        shutter = {**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 30}
        assert resolve_shade_position(hass, area, shutter, data) == (
            30.0,
            ROLE_SUN_PROTECT_ALT,
        )
        _flags(hass, l1="on")
        assert resolve_shade_position(hass, area, shutter, data)[0] == 40.0

    async def test_a_shutter_without_levels_ignores_them(self, hass, calls):
        """Bestandsschutz: die Bedingung am Bereich allein aendert nichts."""
        _, data = await _setup(hass)
        _flags(hass, l1="on", l2="on", l3="on")
        plain = {
            k: v
            for k, v in SHUTTER.items()
            if k not in CONF_POSITION_SUN_PROTECT_LEVELS
        }
        assert resolve_shade_position(hass, _area(), plain, data) == (
            50.0,
            ROLE_SUN_PROTECT,
        )

    async def test_a_level_a_shutter_skips_falls_to_the_next_lower(self, hass, calls):
        _, data = await _setup(hass)
        _flags(hass, l1="on", l2="on")
        no_l2 = {
            k: v for k, v in SHUTTER.items() if k != CONF_POSITION_SUN_PROTECT_LEVELS[1]
        }
        assert resolve_shade_position(hass, _area(), no_l2, data)[0] == 40.0


# --- Haltezeit -----------------------------------------------------------------


class TestHoldTime:
    async def test_a_dropped_level_is_held_then_released(self, hass, calls):
        _, data = await _setup(hass, area=_area(**{CONF_AREA_SHADE_LEVEL_HOLD: 10}))
        area, shutter = _area(**{CONF_AREA_SHADE_LEVEL_HOLD: 10}), dict(SHUTTER)
        _flags(hass, l2="on")
        assert resolve_shade_position(hass, area, shutter, data)[0] == 25.0

        _flags(hass)  # Wolke: Bedingung weg
        assert resolve_shade_position(hass, area, shutter, data)[0] == 25.0

        level, stamp = data["_shade_level_hold"][COVER]
        data["_shade_level_hold"][COVER] = (level, stamp - 11 * 60)
        assert resolve_shade_position(hass, area, shutter, data)[0] == 50.0

    async def test_without_hold_it_drops_at_once(self, hass, calls):
        """Vorgabe 0: wie sp_alt, keine Haltezeit."""
        _, data = await _setup(hass)
        _flags(hass, l2="on")
        assert resolve_shade_position(hass, _area(), dict(SHUTTER), data)[0] == 25.0
        _flags(hass)
        assert resolve_shade_position(hass, _area(), dict(SHUTTER), data)[0] == 50.0


# --- Lamellen und Hoehe -----------------------------------------------------------


class TestTiltAndKeep:
    def test_a_level_without_its_own_angle_uses_the_shading_angle(self):
        shutter = {
            CONF_TILT_ENABLED: True,
            CONF_TILT_SUN_PROTECT: 35,
            CONF_POSITION_SUN_PROTECT_LEVELS[0]: 40,
        }
        assert get_tilt_for_role(shutter, ROLE_SUN_PROTECT_LEVELS[0]) == 35.0

    def test_a_level_with_its_own_angle_uses_that(self):
        shutter = {
            CONF_TILT_ENABLED: True,
            CONF_TILT_SUN_PROTECT: 35,
            CONF_TILT_SUN_PROTECT_LEVELS[0]: 80,
        }
        assert get_tilt_for_role(shutter, ROLE_SUN_PROTECT_LEVELS[0]) == 80.0


# --- Am echten Fahrweg -----------------------------------------------------------


class TestDrives:
    async def test_the_level_is_driven_and_changes_follow_live(self, hass, calls):
        _, data = await _setup(hass)
        await _ticks(hass, data)
        assert 50 in _positions(calls)

        _flags(hass, l1="on")
        calls["pos"].clear()
        await _ticks(hass, data)
        assert _positions(calls) == [40]

        _flags(hass, l1="on", l2="on")
        calls["pos"].clear()
        await _ticks(hass, data)
        assert _positions(calls) == [25]

        _flags(hass)
        calls["pos"].clear()
        await _ticks(hass, data)
        assert _positions(calls) == [50]

    async def test_without_levels_the_drive_is_exactly_as_before(self, hass, calls):
        plain = {
            k: v
            for k, v in SHUTTER.items()
            if k not in CONF_POSITION_SUN_PROTECT_LEVELS
        }
        _, data = await _setup(hass, shutter=plain)
        _flags(hass, l1="on", l2="on", l3="on")
        await _ticks(hass, data, 3)
        assert _positions(calls) == [50]

    async def test_a_level_can_keep_the_height_and_send_only_slats(self, hass, calls):
        shutter = {
            **SHUTTER,
            CONF_TILT_ENABLED: True,
            CONF_TILT_SUN_PROTECT: 60,
            CONF_KEEP_POSITION_SUN_PROTECT_LEVELS[0]: True,
            CONF_TILT_SUN_PROTECT_LEVELS[0]: 90,
        }
        shutter.pop(CONF_POSITION_SUN_PROTECT_LEVELS[0])
        _, data = await _setup(hass, shutter=shutter)
        await _ticks(hass, data)
        calls["pos"].clear()
        calls["tilt"].clear()

        _flags(hass, l1="on")
        await _ticks(hass, data)

        assert _positions(calls) == []
        assert [c.data["tilt_position"] for c in calls["tilt"]] == [90]


# --- Export -------------------------------------------------------------------


async def test_the_export_names_a_level_without_a_condition(hass, calls):
    area = _area()
    del area[sun_condition_keys("sp_l2")[0]]
    entry, _ = await _setup(hass, area=area)
    md = (await async_build_export(hass, entry))["markdown"]
    assert "Beschattungsstufe 2" in md and "keine Bedingung" in md
