"""Referenzfahrt (Raffstore, Stufe 7, simon42 #172 Claus).

In festem Abstand nachts einmal auf "auf", auf "zu" und zurueck. Opt-in je
Rollladen (Vorgabe aus), der erste Lauf kommt erst nach einem Abstand, nicht
beim ersten Start. Sperren, Sturm, Sichtschutz und offenes Fenster halten den
Lauf zurueck."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import cover_tracker, reference_run
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
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_REFERENCE_RUN,
    CONF_REFERENCE_RUN_DAYS,
    CONF_REFERENCE_RUN_TIME,
    CONF_SHUTTERS,
    CONF_TILT_CLOSED,
    CONF_TILT_ENABLED,
    CONF_TILT_OPEN,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_REACT,
    DOMAIN,
)

COVER = "cover.raff_ref"
LOCK = "binary_sensor.ref_lock"
DOOR = "binary_sensor.ref_tuer"

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Ref",
    CONF_AREA_UP_ID: "ref",
    CONF_AREA_DOWN_ID: "ref",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 20,
    CONF_TILT_ENABLED: True,
    CONF_TILT_OPEN: 100,
    CONF_TILT_CLOSED: 30,
    CONF_REFERENCE_RUN: True,
    CONF_REFERENCE_RUN_DAYS: 30,
    CONF_REFERENCE_RUN_TIME: "00:00",
}


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)
    monkeypatch.setattr(reference_run, "WAIT_POLL_SEC", 0.0)
    monkeypatch.setattr(reference_run, "BLIND_WAIT_SEC", 0.0)


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
                "current_tilt_position": 55,
                "supported_features": 255,
            },
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return {"pos": pos, "tilt": tilt}


async def _setup(hass, shutter=None):
    hass.states.async_set(LOCK, "off")
    hass.states.async_set(DOOR, "off")
    hass.states.async_set(
        COVER,
        "open",
        {"current_position": 70, "current_tilt_position": 55, "supported_features": 255},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [
                {CONF_AREA_ID: "ref", CONF_AREA_NAME: "Ref", CONF_AREA_MODE: AREA_MODE_NONE}
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


def _positions(calls_) -> list:
    return [c.data["position"] for c in calls_["pos"]]


def _old(data) -> None:
    data["_refrun_last"][COVER] = "2000-01-01"


async def test_the_service_runs_up_down_and_back(hass, calls):
    _, data = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "reference_run", {"entity_id": COVER}, blocking=True
    )
    await _settle()

    assert _positions(calls) == [100, 20, 70]
    assert [c.data["tilt_position"] for c in calls["tilt"]] == [100, 30, 55]


async def test_it_runs_when_due(hass, calls):
    _, data = await _setup(hass)
    _old(data)
    for cb in list(data["_minute_callbacks"].values()):
        cb(dt_util.now())
    await _settle()

    assert _positions(calls) == [100, 20, 70]
    assert data["_refrun_last"][COVER] == dt_util.now().date().isoformat()


async def test_it_does_not_run_before_the_interval(hass, calls):
    _, data = await _setup(hass)
    for cb in list(data["_minute_callbacks"].values()):
        cb(dt_util.now())
    await _settle()

    assert calls["pos"] == []


async def test_the_first_start_waits_one_interval(hass, calls):
    """Kein Lauf in der ersten Nacht nach dem Einschalten."""
    _, data = await _setup(hass)
    assert data["_refrun_last"][COVER] == dt_util.now().date().isoformat()


async def test_without_the_hook_it_never_runs(hass, calls):
    """Bestandsschutz."""
    off = {k: v for k, v in SHUTTER.items() if k != CONF_REFERENCE_RUN}
    _, data = await _setup(hass, shutter=off)
    assert COVER not in data.get("_refrun_last", {})
    for cb in list(data["_minute_callbacks"].values()):
        cb(dt_util.now())
    await _settle()
    assert calls["pos"] == []


async def test_a_lock_holds_it_back(hass, calls):
    _, data = await _setup(hass, shutter={**SHUTTER, CONF_AUTOMATION_LOCK_ENTITY: LOCK})
    _old(data)
    hass.states.async_set(LOCK, "on")
    for cb in list(data["_minute_callbacks"].values()):
        cb(dt_util.now())
    await _settle()

    assert calls["pos"] == []
    assert data["_refrun_last"][COVER] == "2000-01-01"  # morgen wieder versuchen


async def test_an_open_window_holds_it_back(hass, calls):
    shutter = {
        **SHUTTER,
        CONF_WINDOW_ENTITY_ID: DOOR,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_REACT: False,
    }
    _, data = await _setup(hass, shutter=shutter)
    _old(data)
    hass.states.async_set(DOOR, "on")
    await hass.async_block_till_done()
    calls["pos"].clear()
    for cb in list(data["_minute_callbacks"].values()):
        cb(dt_util.now())
    await _settle()

    assert calls["pos"] == []


async def test_the_service_ignores_an_unknown_cover(hass, calls):
    await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "reference_run", {"entity_id": "cover.gibts_nicht"}, blocking=True
    )
    await _settle()
    assert calls["pos"] == []
