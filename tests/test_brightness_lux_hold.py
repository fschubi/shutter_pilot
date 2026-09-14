"""Mindestdauer an der Lux-Schwelle im Helligkeitsmodus.

bjoerg (community-smarthome.com/11378/147): um 15:12 Uhr fuhren alle
Jalousien herunter - bei 21 000 lx, nicht wirklich dunkel, keine andere
Automation. Nachgerechnet: dieses Muster (Schlafzimmer auf Lueftungsposition
*mit* vorgemerkter Nachhol-Fahrt, alle vier in `covers_driven_down`) erzeugt
nur `brightness._run_down`, und das laeuft ausschliesslich bei einer
Sensormeldung unterhalb der Runter-Schwelle. Die MQTT-Wetterstation hat also
einen einzelnen Ausreisser gemeldet - und eine einzige Meldung war bisher eine
vollstaendige Abendfahrt.

`lux_hold` verlangt, dass die Schwelle N Minuten anhaltend ueber- bzw.
unterschritten ist. Vorgabe 0 = wie bisher. Ein Sensor, der in der
Daemmerung minutenlang denselben Wert meldet, loest kein Event aus, deshalb
prueft der Minutentakt den letzten bekannten Wert nach.

Wie test_brightness_latest.py ohne das schwere Fixture: die Fahrt wird
gepatcht, die Zeitfenster stehen auf ganztags, damit die Uhr nicht mitspielt.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.util import dt as dt_util

from custom_components.shutter_pilot.brightness import setup_brightness_listener
from custom_components.shutter_pilot.const import (
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_LUX_HOLD,
    CONF_AREA_MODE,
    CONF_AREA_UP_ID,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_DOWN_TO,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WE_UP_TO,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_SHUTTERS,
    DOMAIN,
)

COVER = "cover.wohnzimmer"
SENSOR = "sensor.wetterstation_illuminance"


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_MODE: AREA_MODE_BRIGHTNESS,
        CONF_AREA_BRIGHTNESS_SENSOR: SENSOR,
        CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD: 199,
        CONF_AREA_BRIGHTNESS_UP_THRESHOLD: 201,
        CONF_AREA_W_UP_FROM: "00:00", CONF_AREA_W_UP_TO: "23:59",
        CONF_AREA_W_DOWN_FROM: "00:00", CONF_AREA_W_DOWN_TO: "23:59",
        CONF_AREA_WE_UP_FROM: "00:00", CONF_AREA_WE_UP_TO: "23:59",
        CONF_AREA_WE_DOWN_FROM: "00:00", CONF_AREA_WE_DOWN_TO: "23:59",
    }
    area.update(overrides)
    return area


async def _setup(hass, area: dict):
    hass.states.async_set(SENSOR, "21174")
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_AREAS: [area],
            CONF_SHUTTERS: [
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_AREA_UP_ID: "living",
                    CONF_AREA_DOWN_ID: "living",
                    CONF_POSITION_OPEN: 100,
                    CONF_POSITION_CLOSED: 0,
                }
            ],
        },
    )
    entry.add_to_hass(hass)
    data: dict = hass.data.setdefault(DOMAIN, {}).setdefault(
        entry.entry_id, {"master_enabled": True}
    )
    await setup_brightness_listener(hass, entry)
    return entry, data


@pytest.fixture
def clock(monkeypatch):
    """Monotone Uhr von Hand: die Frist rechnet in Sekunden seit der ersten
    Unterschreitung, nicht nach Wanduhr."""
    state = {"t": 1000.0}
    monkeypatch.setattr(
        "custom_components.shutter_pilot.brightness.time_mod.monotonic",
        lambda: state["t"],
    )
    return state


@pytest.fixture
def drive():
    with patch(
        "custom_components.shutter_pilot.brightness.set_cover_position",
        new=AsyncMock(return_value=True),
    ) as mock:
        yield mock


async def _lux(hass, value: float) -> None:
    hass.states.async_set(SENSOR, str(value))
    await hass.async_block_till_done()


async def _tick(hass, data) -> None:
    cb = data.get("_minute_callbacks", {}).get("brightness")
    assert cb is not None, "mit Frist muss der Minutentakt registriert sein"
    cb(dt_util.now())
    await hass.async_block_till_done()


def _positions(drive) -> list[float]:
    return [c.args[3] for c in drive.await_args_list]


class TestWithoutAHoldNothingChanges:
    async def test_one_reading_drives_as_before(self, hass, drive, clock):
        _, data = await _setup(hass, _area())
        assert data.get("_minute_callbacks", {}).get("brightness") is None, (
            "ohne Frist und ohne Uhrzeit-Notnagel kein Minutentakt - wie bisher"
        )
        await _lux(hass, 0)
        assert _positions(drive) == [0]


class TestTheStrayReading:
    async def test_bjoergs_15_12_does_not_close_the_house(self, hass, drive, clock):
        """Ein einzelner 0-lx-Ausreisser zwischen zwei normalen Werten."""
        _, data = await _setup(hass, _area(**{CONF_AREA_LUX_HOLD: 3}))
        # Tag: der Rollladen steht oben, die Automatik hat ihn morgens gefahren.
        data["covers_driven_up"].add(COVER)
        await _lux(hass, 0)
        assert _positions(drive) == [], "die erste Meldung ist noch kein Trend"
        clock["t"] += 30
        await _lux(hass, 21963)
        clock["t"] += 600
        await _tick(hass, data)
        assert _positions(drive) == [], (
            "der Ausreisser ist vorbei, die Frist wurde nie erreicht"
        )

    async def test_real_dusk_still_closes_after_the_hold(self, hass, drive, clock):
        """Bleibt es dunkel, faehrt der Bereich - auch ohne neues Sensor-Event."""
        _, data = await _setup(hass, _area(**{CONF_AREA_LUX_HOLD: 3}))
        await _lux(hass, 150)
        clock["t"] += 60
        await _tick(hass, data)
        clock["t"] += 60
        await _tick(hass, data)
        assert _positions(drive) == [], "nach zwei Minuten noch nicht"
        clock["t"] += 60
        await _tick(hass, data)
        assert _positions(drive) == [0], "nach drei Minuten unter der Schwelle: zu"

    async def test_a_gap_restarts_the_clock(self, hass, drive, clock):
        _, data = await _setup(hass, _area(**{CONF_AREA_LUX_HOLD: 3}))
        await _lux(hass, 150)
        clock["t"] += 120
        await _lux(hass, 5000)   # Wolkenluecke
        clock["t"] += 10
        await _lux(hass, 150)
        clock["t"] += 120
        await _tick(hass, data)
        assert _positions(drive) == [], (
            "seit der Luecke sind erst zwei Minuten vergangen"
        )
        clock["t"] += 60
        await _tick(hass, data)
        assert _positions(drive) == [0]

    async def test_the_up_direction_holds_too(self, hass, drive, clock):
        """Eine kurze Aufhellung nachts (Blitz, Scheinwerfer) oeffnet nichts."""
        _, data = await _setup(hass, _area(**{CONF_AREA_LUX_HOLD: 3}))
        data["covers_driven_down"].add(COVER)
        hass.states.async_set(SENSOR, "0")
        await hass.async_block_till_done()
        drive.reset_mock()
        await _lux(hass, 5000)
        assert _positions(drive) == []
        clock["t"] += 20
        await _lux(hass, 0)
        clock["t"] += 600
        await _tick(hass, data)
        assert _positions(drive) == []
        # Echter Morgen: hell und bleibt hell.
        await _lux(hass, 5000)
        clock["t"] += 180
        await _tick(hass, data)
        assert _positions(drive) == [100]
