"""Zweite Schliessstufe (simon42 #267 Claus).

Abends die normale Fahrt (Hoehe 0, Lamellen 80), wenn es draussen ganz dunkel
ist - bei Claus fuenf Minuten unter 1 lx - Lamellen 60. Opt-in je Rollladen.
Die Stufe vollendet nur eine Abendfahrt, die wirklich auf die normale
Schliessposition gefahren ist, und uebergeht keine Entscheidung danach."""

from __future__ import annotations

import time
from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.close_stage2 import has_trigger, time_reached
from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_AUTOMATION_LOCK_ENTITY,
    CONF_CLOSE_STAGE2,
    CONF_CLOSE_STAGE2_ENTITY,
    CONF_CLOSE_STAGE2_LUX,
    CONF_CLOSE_STAGE2_LUX_ENTITY,
    CONF_CLOSE_STAGE2_MINUTES,
    CONF_CLOSE_STAGE2_TIME,
    CONF_COVER_ENTITY_ID,
    CONF_KEEP_POSITION_CLOSED_STAGE2,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_PRIVACY_ENTITY,
    CONF_SHUTTERS,
    CONF_TILT_CLOSED,
    CONF_TILT_CLOSED_STAGE2,
    CONF_TILT_ENABLED,
    CONF_TILT_OPEN,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    DOMAIN,
)

COVER = "cover.raff_diele"
LUX = "sensor.aussen_lux"

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Diele",
    CONF_AREA_UP_ID: "diele",
    CONF_AREA_DOWN_ID: "diele",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
    CONF_TILT_ENABLED: True,
    CONF_TILT_OPEN: 100,
    CONF_TILT_CLOSED: 80,
    CONF_CLOSE_STAGE2: True,
    CONF_CLOSE_STAGE2_LUX_ENTITY: LUX,
    CONF_CLOSE_STAGE2_LUX: 1,
    CONF_CLOSE_STAGE2_MINUTES: 5,
    CONF_KEEP_POSITION_CLOSED_STAGE2: True,  # Hoehe bleibt, nur die Lamellen
    CONF_TILT_CLOSED_STAGE2: 60,
}


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

    hass.services.async_register("cover", "set_cover_position", _handler)
    return {"pos": pos, "tilt": tilt}


async def _setup(hass, shutter=None, lux="0", position=0, closed=True):
    hass.states.async_set(LUX, lux)
    hass.states.async_set(
        COVER,
        "closed",
        {"current_position": position, "current_tilt_position": 80, "supported_features": 255},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [
                {CONF_AREA_ID: "diele", CONF_AREA_NAME: "Diele", CONF_AREA_MODE: AREA_MODE_NONE}
            ],
            CONF_SHUTTERS: [shutter or dict(SHUTTER)],
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    data = hass.data[DOMAIN][entry.entry_id]
    if closed:
        # Die Abendfahrt hat stattgefunden.
        data.setdefault("covers_driven_down", set()).add(COVER)
        data.setdefault("covers_driven_up", set()).discard(COVER)
    return entry, data


async def _tick(hass, data, monkeypatch, hour: int, minute: int = 0, day: int = 4):
    moment = datetime(2026, 11, day, hour, minute, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    monkeypatch.setattr(dt_util, "now", lambda *a, **k: moment)
    data["_minute_callbacks"]["close_stage2"](moment)
    await hass.async_block_till_done()


def _positions(calls_) -> list:
    return [c.data["position"] for c in calls_["pos"]]


def _tilts(calls_) -> list:
    return [c.data["tilt_position"] for c in calls_["tilt"]]


async def _dark_for(hass, data, monkeypatch, start_minute: int, minutes: int, hour=21):
    for m in range(start_minute, start_minute + minutes + 1):
        await _tick(hass, data, monkeypatch, hour, m)


async def test_dark_for_five_minutes_turns_the_slats(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 21, 0)
    await _tick(hass, data, monkeypatch, 21, 4)
    assert calls["tilt"] == []
    await _tick(hass, data, monkeypatch, 21, 5)
    assert _tilts(calls) == [60]
    # Hoehe "unveraendert": kein Positionsbefehl.
    assert calls["pos"] == []


async def test_a_bright_moment_starts_the_wait_over(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 21, 0)
    hass.states.async_set(LUX, "30")
    await _tick(hass, data, monkeypatch, 21, 3)
    hass.states.async_set(LUX, "0")
    await _tick(hass, data, monkeypatch, 21, 4)
    await _tick(hass, data, monkeypatch, 21, 8)
    assert calls["tilt"] == []
    await _tick(hass, data, monkeypatch, 21, 9)
    assert _tilts(calls) == [60]


async def test_already_dark_at_the_evening_drive_follows_straight_away(
    hass, calls, monkeypatch
):
    _, data = await _setup(hass, closed=False)
    await _tick(hass, data, monkeypatch, 21, 0)
    await _tick(hass, data, monkeypatch, 21, 10)
    assert calls["tilt"] == []
    data["covers_driven_down"].add(COVER)
    await _tick(hass, data, monkeypatch, 21, 11)
    assert _tilts(calls) == [60]


async def test_it_fires_once_a_night(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _dark_for(hass, data, monkeypatch, 0, 8)
    assert _tilts(calls) == [60]


async def test_the_next_morning_resets_it(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _dark_for(hass, data, monkeypatch, 0, 5)
    data["covers_driven_down"].discard(COVER)
    await _tick(hass, data, monkeypatch, 7, 0, day=5)
    data["covers_driven_down"].add(COVER)
    await _dark_for(hass, data, monkeypatch, 0, 5, hour=22)
    assert _tilts(calls) == [60, 60]


async def test_a_dead_lux_sensor_holds_it_back(hass, calls, monkeypatch):
    _, data = await _setup(hass, lux="unavailable")
    await _dark_for(hass, data, monkeypatch, 0, 10)
    assert calls["tilt"] == []


async def test_without_an_evening_drive_nothing_happens(hass, calls, monkeypatch):
    _, data = await _setup(hass, closed=False)
    await _dark_for(hass, data, monkeypatch, 0, 10)
    assert calls["tilt"] == []


async def test_a_part_way_close_is_left_alone(hass, calls, monkeypatch):
    """Laue-Abend- oder Frostposition: gewollt nicht ganz zu."""
    _, data = await _setup(hass, position=50)
    await _dark_for(hass, data, monkeypatch, 0, 10)
    assert calls["tilt"] == []


async def test_a_hand_move_after_the_evening_drive_is_respected(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 21, 0)
    data.setdefault("_hand_moved_at", {})[COVER] = time.monotonic() + 1
    await _dark_for(hass, data, monkeypatch, 1, 10)
    assert calls["tilt"] == []


async def test_a_hand_move_before_the_evening_drive_is_not(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    data.setdefault("_hand_moved_at", {})[COVER] = time.monotonic() - 3600
    await _dark_for(hass, data, monkeypatch, 0, 5)
    assert _tilts(calls) == [60]


async def test_an_open_window_keeps_it_where_it_is(hass, calls, monkeypatch):
    hass.states.async_set("binary_sensor.tuer", "on")
    shutter = dict(
        SHUTTER,
        **{CONF_WINDOW_ENTITY_ID: "binary_sensor.tuer", CONF_WINDOW_OPEN_STATE: "on"},
    )
    _, data = await _setup(hass, shutter)
    calls["tilt"].clear()
    await _dark_for(hass, data, monkeypatch, 0, 10)
    assert 60 not in _tilts(calls)


async def test_privacy_keeps_it_where_it_is(hass, calls, monkeypatch):
    hass.states.async_set("binary_sensor.bad", "on")
    shutter = dict(SHUTTER, **{CONF_PRIVACY_ENTITY: "binary_sensor.bad"})
    _, data = await _setup(hass, shutter)
    calls["tilt"].clear()
    await _dark_for(hass, data, monkeypatch, 0, 10)
    assert 60 not in _tilts(calls)


async def test_a_lock_keeps_it_where_it_is(hass, calls, monkeypatch):
    hass.states.async_set("input_boolean.sperre", "on")
    shutter = dict(SHUTTER, **{CONF_AUTOMATION_LOCK_ENTITY: "input_boolean.sperre"})
    _, data = await _setup(hass, shutter)
    await _dark_for(hass, data, monkeypatch, 0, 10)
    assert calls["tilt"] == []


async def test_time_only_trigger(hass, calls, monkeypatch):
    shutter = {
        k: v for k, v in SHUTTER.items()
        if k not in (CONF_CLOSE_STAGE2_LUX_ENTITY,)
    }
    shutter[CONF_CLOSE_STAGE2_TIME] = "23:00"
    _, data = await _setup(hass, shutter)
    await _tick(hass, data, monkeypatch, 22, 59)
    assert calls["tilt"] == []
    await _tick(hass, data, monkeypatch, 23, 0)
    assert _tilts(calls) == [60]


async def test_a_condition_entity_holds_it_back(hass, calls, monkeypatch):
    hass.states.async_set("input_boolean.nacht", "off")
    shutter = dict(SHUTTER, **{CONF_CLOSE_STAGE2_ENTITY: "input_boolean.nacht"})
    _, data = await _setup(hass, shutter)
    await _dark_for(hass, data, monkeypatch, 0, 6)
    assert calls["tilt"] == []
    hass.states.async_set("input_boolean.nacht", "on")
    await _tick(hass, data, monkeypatch, 21, 7)
    assert _tilts(calls) == [60]


async def test_without_a_trigger_nothing_runs(hass, calls, monkeypatch):
    shutter = {k: v for k, v in SHUTTER.items() if k != CONF_CLOSE_STAGE2_LUX_ENTITY}
    _, data = await _setup(hass, shutter)
    assert "close_stage2" not in data.get("_minute_callbacks", {})


async def test_without_the_hook_nothing_ever_runs(hass, calls, monkeypatch):
    """Bestandsschutz."""
    shutter = {k: v for k, v in SHUTTER.items() if k != CONF_CLOSE_STAGE2}
    _, data = await _setup(hass, shutter)
    assert "close_stage2" not in data.get("_minute_callbacks", {})


class TestTimeReached:
    def _at(self, h, m):
        return datetime(2026, 11, 4, h, m)

    def test_unset_means_no_time_criterion(self):
        assert time_reached({}, self._at(18, 0))

    def test_past_midnight_counts_as_after_an_evening_time(self):
        s = {CONF_CLOSE_STAGE2_TIME: "23:00"}
        assert not time_reached(s, self._at(22, 0))
        assert time_reached(s, self._at(23, 30))
        assert time_reached(s, self._at(1, 0))

    def test_an_after_midnight_time_waits_through_the_evening(self):
        s = {CONF_CLOSE_STAGE2_TIME: "00:30"}
        assert not time_reached(s, self._at(22, 0))
        assert not time_reached(s, self._at(0, 15))
        assert time_reached(s, self._at(0, 30))

    def test_a_broken_value_never_fires(self):
        assert not time_reached({CONF_CLOSE_STAGE2_TIME: "kaputt"}, self._at(23, 0))

    def test_has_trigger(self):
        assert not has_trigger({})
        assert has_trigger({CONF_CLOSE_STAGE2_TIME: "23:00"})
        assert has_trigger({CONF_CLOSE_STAGE2_ENTITY: "input_boolean.x"})
        assert has_trigger({CONF_CLOSE_STAGE2_LUX_ENTITY: LUX})
