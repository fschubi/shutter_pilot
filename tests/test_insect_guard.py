"""Insektenschutz (Claus, simon42 #267).

Wespen nisten in Raffstore-Kaesten, die lange nicht ganz hochfahren. Einmal am
Tag im Zeitfenster kurz bis zum oberen Anschlag und zurueck - nur ab einer
Mindesttemperatur und unter einer Bedingung (niemand zu Hause). Opt-in je
Rollladen; alles, was einen Anspruch auf den Behang hat, geht vor."""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import cover_tracker, insect_guard
from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_AUTOMATION_LOCK_ENTITY,
    CONF_COVER_ENTITY_ID,
    CONF_INSECT_GUARD,
    CONF_INSECT_GUARD_ENTITY,
    CONF_INSECT_GUARD_FROM,
    CONF_INSECT_GUARD_TEMP_ENTITY,
    CONF_INSECT_GUARD_TEMP_MIN,
    CONF_INSECT_GUARD_TO,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_PRIVACY_ENTITY,
    CONF_SHUTTERS,
    CONF_TILT_ENABLED,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    DOMAIN,
)

COVER = "cover.raff_buero"
AWAY = "input_boolean.niemand_da"
TEMP = "sensor.aussen"

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Büro",
    CONF_AREA_UP_ID: "buero",
    CONF_AREA_DOWN_ID: "buero",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
    CONF_TILT_ENABLED: True,
    CONF_INSECT_GUARD: True,
    CONF_INSECT_GUARD_FROM: "11:00",
    CONF_INSECT_GUARD_TO: "16:00",
    CONF_INSECT_GUARD_ENTITY: AWAY,
    CONF_INSECT_GUARD_TEMP_ENTITY: TEMP,
    CONF_INSECT_GUARD_TEMP_MIN: 15,
}


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)
    monkeypatch.setattr(insect_guard, "WAIT_POLL_SEC", 0.0)
    monkeypatch.setattr(insect_guard, "BLIND_WAIT_SEC", 0.0)


@pytest.fixture
def calls(hass):
    pos: list = []
    tilt = async_mock_service(hass, "cover", "set_cover_tilt_position")

    async def _handler(call):
        pos.append(call)
        hass.states.async_set(
            call.data["entity_id"],
            "open",
            {
                "current_position": call.data["position"],
                "current_tilt_position": 40,
                "supported_features": 255,
            },
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return {"pos": pos, "tilt": tilt}


async def _setup(hass, shutter=None, position=30, away="on", temp="22"):
    hass.states.async_set(AWAY, away)
    hass.states.async_set(TEMP, temp)
    hass.states.async_set(
        COVER,
        "open",
        {"current_position": position, "current_tilt_position": 40, "supported_features": 255},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [
                {CONF_AREA_ID: "buero", CONF_AREA_NAME: "Büro", CONF_AREA_MODE: AREA_MODE_NONE}
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
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _settle() -> None:
    """Hintergrund-Aufgaben werden von async_block_till_done nicht abgewartet."""
    for _ in range(60):
        await asyncio.sleep(0.01)


async def _tick(hass, data, monkeypatch, hour: int, minute: int = 0, day: int = 4):
    moment = datetime(2026, 7, day, hour, minute, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    monkeypatch.setattr(dt_util, "now", lambda *a, **k: moment)
    data["_minute_callbacks"]["insect_guard"](moment)
    await _settle()


def _positions(calls_) -> list:
    return [c.data["position"] for c in calls_["pos"]]


async def test_it_goes_up_and_back(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 11, 0)
    assert _positions(calls) == [100, 30]
    # Lamellen zurueck auf das, was vorher stand.
    assert [c.data["tilt_position"] for c in calls["tilt"]][-1] == 40


async def test_once_a_day(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 11, 0)
    await _tick(hass, data, monkeypatch, 12, 0)
    assert _positions(calls) == [100, 30]
    await _tick(hass, data, monkeypatch, 11, 0, day=5)
    assert _positions(calls) == [100, 30, 100, 30]


async def test_outside_the_window_nothing_happens(hass, calls, monkeypatch):
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 10, 59)
    await _tick(hass, data, monkeypatch, 16, 0)
    assert calls["pos"] == []


async def test_too_cold_waits(hass, calls, monkeypatch):
    _, data = await _setup(hass, temp="12")
    await _tick(hass, data, monkeypatch, 11, 0)
    assert calls["pos"] == []
    hass.states.async_set(TEMP, "18")
    await _tick(hass, data, monkeypatch, 13, 0)
    assert _positions(calls) == [100, 30]


async def test_a_dead_temperature_sensor_waits(hass, calls, monkeypatch):
    _, data = await _setup(hass, temp="unavailable")
    await _tick(hass, data, monkeypatch, 11, 0)
    assert calls["pos"] == []


async def test_somebody_home_waits(hass, calls, monkeypatch):
    _, data = await _setup(hass, away="off")
    await _tick(hass, data, monkeypatch, 11, 0)
    assert calls["pos"] == []


async def test_without_conditions_only_the_window_counts(hass, calls, monkeypatch):
    shutter = {
        k: v for k, v in SHUTTER.items()
        if k not in (CONF_INSECT_GUARD_ENTITY, CONF_INSECT_GUARD_TEMP_ENTITY)
    }
    _, data = await _setup(hass, shutter, temp="5")
    await _tick(hass, data, monkeypatch, 11, 0)
    assert _positions(calls) == [100, 30]


async def test_already_at_the_top_counts_as_done(hass, calls, monkeypatch):
    _, data = await _setup(hass, position=100)
    await _tick(hass, data, monkeypatch, 11, 0)
    assert calls["pos"] == []
    hass.states.async_set(
        COVER, "open", {"current_position": 30, "current_tilt_position": 40, "supported_features": 255}
    )
    await _tick(hass, data, monkeypatch, 12, 0)
    assert calls["pos"] == []


async def test_an_inverted_scale_goes_to_zero(hass, calls, monkeypatch):
    shutter = dict(SHUTTER, **{CONF_POSITION_OPEN: 0, CONF_POSITION_CLOSED: 100})
    _, data = await _setup(hass, shutter, position=70)
    await _tick(hass, data, monkeypatch, 11, 0)
    assert _positions(calls) == [0, 70]


async def test_an_open_window_holds_it(hass, calls, monkeypatch):
    hass.states.async_set("binary_sensor.tuer", "on")
    shutter = dict(
        SHUTTER, **{CONF_WINDOW_ENTITY_ID: "binary_sensor.tuer", CONF_WINDOW_OPEN_STATE: "on"}
    )
    _, data = await _setup(hass, shutter)
    calls["pos"].clear()
    await _tick(hass, data, monkeypatch, 11, 0)
    assert 100 not in _positions(calls)


async def test_privacy_holds_it(hass, calls, monkeypatch):
    hass.states.async_set("binary_sensor.bad", "on")
    shutter = dict(SHUTTER, **{CONF_PRIVACY_ENTITY: "binary_sensor.bad"})
    _, data = await _setup(hass, shutter)
    calls["pos"].clear()
    await _tick(hass, data, monkeypatch, 11, 0)
    assert 100 not in _positions(calls)


async def test_a_lock_holds_it(hass, calls, monkeypatch):
    hass.states.async_set("input_boolean.sperre", "on")
    shutter = dict(SHUTTER, **{CONF_AUTOMATION_LOCK_ENTITY: "input_boolean.sperre"})
    _, data = await _setup(hass, shutter)
    await _tick(hass, data, monkeypatch, 11, 0)
    assert calls["pos"] == []


async def test_the_frost_opening_position_holds_it(hass, calls, monkeypatch):
    """MartyBr #268: bei Frost nicht in den Kasten - auch nicht fuer Wespen."""
    monkeypatch.setattr(insect_guard, "frost_opening_applies", lambda *a: True)
    _, data = await _setup(hass)
    await _tick(hass, data, monkeypatch, 11, 0)
    assert calls["pos"] == []


async def test_without_the_hook_nothing_ever_runs(hass, calls, monkeypatch):
    shutter = {k: v for k, v in SHUTTER.items() if k != CONF_INSECT_GUARD}
    _, data = await _setup(hass, shutter)
    assert "insect_guard" not in data.get("_minute_callbacks", {})


class TestWindow:
    def _at(self, h, m):
        return datetime(2026, 7, 4, h, m)

    def test_defaults(self):
        s = {}
        assert not insect_guard.in_window(s, self._at(10, 59))
        assert insect_guard.in_window(s, self._at(11, 0))
        assert not insect_guard.in_window(s, self._at(16, 0))

    def test_over_midnight_wraps(self):
        s = {CONF_INSECT_GUARD_FROM: "22:00", CONF_INSECT_GUARD_TO: "02:00"}
        assert insect_guard.in_window(s, self._at(23, 0))
        assert insect_guard.in_window(s, self._at(1, 0))
        assert not insect_guard.in_window(s, self._at(12, 0))
