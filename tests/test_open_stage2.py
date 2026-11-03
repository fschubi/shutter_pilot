"""Zweite Oeffnungsstufe (simon42 #225 Claus).

Morgens nur die Lamellen (normale Hochfahrt mit "Hoehe unveraendert"), ab zehn
Uhr - wenn jemand da ist - ganz hoch. Opt-in je Rollladen. Die Stufe vollendet
nur eine Hochfahrt, die wirklich stattfand, und uebergeht keine Entscheidung."""

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
from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_KEEP_POSITION_OPEN,
    CONF_NAME,
    CONF_OPEN_STAGE2,
    CONF_OPEN_STAGE2_ENTITY,
    CONF_OPEN_STAGE2_TIME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_OPEN_STAGE2,
    CONF_PRIVACY_ENTITY,
    CONF_SHUTTERS,
    CONF_TILT_CLOSED,
    CONF_TILT_ENABLED,
    CONF_TILT_OPEN,
    CONF_TILT_OPEN_STAGE2,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    DOMAIN,
)

COVER = "cover.raff_diele"
HOME = "input_boolean.jemand_da"

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Diele",
    CONF_AREA_UP_ID: "diele",
    CONF_AREA_DOWN_ID: "diele",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
    CONF_TILT_ENABLED: True,
    CONF_TILT_OPEN: 80,
    CONF_TILT_CLOSED: 0,
    CONF_KEEP_POSITION_OPEN: True,  # morgens nur die Lamellen
    CONF_OPEN_STAGE2: True,
    CONF_OPEN_STAGE2_TIME: "10:00",
    CONF_OPEN_STAGE2_ENTITY: HOME,
    CONF_POSITION_OPEN_STAGE2: 100,
    CONF_TILT_OPEN_STAGE2: 100,
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


async def _setup(hass, shutter=None, home="on"):
    hass.states.async_set(HOME, home)
    hass.states.async_set(
        COVER,
        "open",
        {"current_position": 20, "current_tilt_position": 80, "supported_features": 255},
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
    # Die Hochfahrt am Morgen hat stattgefunden.
    data.setdefault("covers_driven_up", set()).add(COVER)
    return entry, data


async def _tick(hass, data, monkeypatch, hour: int, minute: int = 0, day: int = 4):
    moment = datetime(2026, 11, day, hour, minute, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    monkeypatch.setattr(dt_util, "now", lambda *a, **k: moment)
    data["_minute_callbacks"]["open_stage2"](moment)
    await hass.async_block_till_done()


def _positions(calls_) -> list:
    return [c.data["position"] for c in calls_["pos"]]


def _tilts(calls_) -> list:
    return [c.data["tilt_position"] for c in calls_["tilt"]]


async def test_before_the_time_nothing_happens(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 9, 59)
    assert calls["pos"] == [] and calls["tilt"] == []


async def test_from_the_time_it_opens_fully(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 10, 0)
    assert _positions(calls) == [100]
    assert _tilts(calls) == [100]


async def test_without_somebody_home_it_waits_and_fires_later(hass, calls, monkeypatch):
    _, data = await _setup(hass, home="off")
    await _tick(hass, data, monkeypatch, 11)
    assert calls["pos"] == []

    hass.states.async_set(HOME, "on")
    await _tick(hass, data, monkeypatch, 14)
    assert _positions(calls) == [100]


async def test_it_fires_once_a_day(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 10, 0)
    await _tick(hass, data, monkeypatch, 10, 1)
    assert _positions(calls) == [100]


async def test_a_dead_condition_entity_holds_it_back(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    hass.states.async_remove(HOME)
    await _tick(hass, data, monkeypatch, 11)
    assert calls["pos"] == []


async def test_a_morning_that_never_opened_has_no_second_stage(hass, calls, monkeypatch):
    """Wochenend-Sperre, Sichtschutz, "nicht hochfahren": keine Hochfahrt, keine Stufe 2."""
    _, data = await _setup(hass)
    data["covers_driven_up"].discard(COVER)
    await _tick(hass, data, monkeypatch, 11)
    assert calls["pos"] == []


async def test_after_the_evening_drive_it_stays_quiet(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    data["covers_driven_down"] = {COVER}
    await _tick(hass, data, monkeypatch, 20)
    assert calls["pos"] == []


async def test_a_hand_move_today_is_respected(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    data.setdefault("_hand_moved_at", {})[COVER] = time.monotonic()
    await _tick(hass, data, monkeypatch, 11)
    assert calls["pos"] == []


async def test_a_hand_move_from_yesterday_is_not(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    data.setdefault("_hand_moved_at", {})[COVER] = time.monotonic() - 2 * 86400
    await _tick(hass, data, monkeypatch, 11)
    assert _positions(calls) == [100]


async def test_shading_keeps_it_where_it_is(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    data.setdefault("sun_protected_covers", set()).add(COVER)
    from custom_components.shutter_pilot.helpers import set_cover_sun_protected

    set_cover_sun_protected(data, COVER, True)
    await _tick(hass, data, monkeypatch, 11)
    assert calls["pos"] == []


async def test_privacy_keeps_it_where_it_is(hass, calls, monkeypatch):
    hass.states.async_set("binary_sensor.bad", "on")
    shutter = dict(SHUTTER, **{CONF_PRIVACY_ENTITY: "binary_sensor.bad"})
    _, data = await _setup(hass, shutter)
    calls["pos"].clear()
    await _tick(hass, data, monkeypatch, 11)
    assert 100 not in _positions(calls)


async def test_an_open_window_keeps_it_where_it_is(hass, calls, monkeypatch):
    hass.states.async_set("binary_sensor.fenster", "on")
    shutter = dict(
        SHUTTER,
        **{CONF_WINDOW_ENTITY_ID: "binary_sensor.fenster", CONF_WINDOW_OPEN_STATE: "on"},
    )
    _, data = await _setup(hass, shutter)
    calls["pos"].clear()
    await _tick(hass, data, monkeypatch, 11)
    assert 100 not in _positions(calls)


async def test_without_the_hook_nothing_ever_runs(hass, calls, monkeypatch):
    """Bestandsschutz."""
    shutter = {k: v for k, v in SHUTTER.items() if k != CONF_OPEN_STAGE2}
    _, data = await _setup(hass, shutter)
    assert "open_stage2" not in data.get("_minute_callbacks", {})
