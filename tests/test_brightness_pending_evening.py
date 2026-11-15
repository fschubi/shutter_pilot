"""Die Vormerkung "heute noch hochfahren" endet mit der Abendfahrt (Claus, #249).

Diele im Helligkeitsmodus, Hoch-Fenster 05:00-12:00, Runter-Fenster ab 15:00,
hoch ueber 400 lx, runter unter 300 lx. Der Sensor ist ein Template: 0 lx,
solange das Dielenlicht brennt. Am 08.11. fuhr die Raff um 15:35 zu (Licht an)
und um 15:40 wieder auf (Licht aus, 1000 lx) - dreieinhalb Stunden nach dem
Ende des Hoch-Fensters.

Nachgerechnet: faellt der Sensor im Hoch-Fenster *nach* der Morgenfahrt noch
einmal unter die Schwelle, wurde der Bereich vorgemerkt. Eingeloest wird die
Vormerkung nur von einer Hochfahrt, die es nicht mehr gibt (alles ist oben) -
sie blieb bis Mitternacht stehen und galt abends als "im Fenster".
"""

from __future__ import annotations

from datetime import datetime as real_datetime
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import brightness
from custom_components.shutter_pilot.brightness import setup_brightness_listener
from custom_components.shutter_pilot.const import (
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
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

COVER = "cover.fenster_diele_jalousie"
SENSOR = "sensor.diele_helligkeit_raff"

# Claus' Werte aus dem Export vom 08.11.
AREA = {
    CONF_AREA_ID: "diele",
    CONF_AREA_MODE: AREA_MODE_BRIGHTNESS,
    CONF_AREA_BRIGHTNESS_SENSOR: SENSOR,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD: 300,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD: 400,
    CONF_AREA_W_UP_FROM: "05:00", CONF_AREA_W_UP_TO: "12:00",
    CONF_AREA_W_DOWN_FROM: "15:00", CONF_AREA_W_DOWN_TO: "23:59",
    CONF_AREA_WE_UP_FROM: "05:00", CONF_AREA_WE_UP_TO: "12:00",
    CONF_AREA_WE_DOWN_FROM: "15:00", CONF_AREA_WE_DOWN_TO: "23:59",
}
SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_AREA_UP_ID: "diele",
    CONF_AREA_DOWN_ID: "diele",
    CONF_POSITION_OPEN: 70,
    CONF_POSITION_CLOSED: 0,
}


@pytest.fixture
def wall_clock(monkeypatch):
    """`datetime.now()` in brightness.py auf eine stellbare Uhr legen."""
    state = {"now": real_datetime(2026, 11, 8, 6, 0)}

    class _Clock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return state["now"]

    monkeypatch.setattr(brightness, "datetime", _Clock)

    def _set(hour: int, minute: int) -> None:
        state["now"] = real_datetime(2026, 11, 8, hour, minute)

    return _set


@pytest.fixture
def drive():
    with patch(
        "custom_components.shutter_pilot.brightness.set_cover_position",
        new=AsyncMock(return_value=True),
    ) as mock:
        yield mock


async def _setup(hass, shutters: list[dict] | None = None, areas: list[dict] | None = None):
    hass.states.async_set(SENSOR, "350")
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={CONF_AREAS: areas or [AREA], CONF_SHUTTERS: shutters or [SHUTTER]},
    )
    entry.add_to_hass(hass)
    data: dict = hass.data.setdefault(DOMAIN, {}).setdefault(
        entry.entry_id, {"master_enabled": True}
    )
    await setup_brightness_listener(hass, entry)
    return data


async def _lux(hass, value: float) -> None:
    hass.states.async_set(SENSOR, str(value))
    await hass.async_block_till_done()


def _drives(drive) -> list[float]:
    return [c.args[3] for c in drive.await_args_list]


async def test_claus_no_reopen_after_the_evening_close(hass, drive, wall_clock):
    """Der gemeldete Tag, Meldung fuer Meldung."""
    data = await _setup(hass)

    wall_clock(6, 30)
    await _lux(hass, 0)  # noch dunkel
    wall_clock(7, 30)
    await _lux(hass, 1000)  # Morgenfahrt
    assert _drives(drive) == [70]

    wall_clock(11, 0)
    await _lux(hass, 0)  # Licht an, im Hoch-Fenster
    wall_clock(11, 5)
    await _lux(hass, 1000)  # Licht aus
    assert data["_pending_up"] == {}, "nichts mehr hochzufahren, nichts vorzumerken"

    wall_clock(15, 35)
    await _lux(hass, 0)  # Licht an: Abendfahrt
    assert _drives(drive) == [70, 0]

    wall_clock(15, 40)
    await _lux(hass, 1000)  # Licht aus
    assert _drives(drive) == [70, 0], "kein Hochfahren nach 12:00"


async def test_evening_close_ends_a_legitimate_pending(hass, drive, wall_clock):
    """Vorgemerkt und nie eingeloest (Automatik des Rollladens war morgens aus)."""
    data = await _setup(hass)
    wall_clock(6, 30)
    await _lux(hass, 100)
    assert "diele" in data["_pending_up"]

    wall_clock(15, 35)
    await _lux(hass, 0)
    assert _drives(drive) == [0]
    assert data["_pending_up"] == {}

    wall_clock(15, 40)
    await _lux(hass, 1000)
    assert _drives(drive) == [0]


async def test_evening_without_a_drive_ends_it_too(hass, drive, wall_clock):
    """Gilt der Rollladen schon als unten, faehrt abends nichts - trotzdem Schluss."""
    data = await _setup(hass)
    data["covers_driven_down"].add(COVER)
    wall_clock(6, 30)
    await _lux(hass, 100)
    wall_clock(15, 35)
    await _lux(hass, 0)
    wall_clock(15, 40)
    await _lux(hass, 1000)
    assert _drives(drive) == []


async def test_pending_still_opens_after_the_window(hass, drive, wall_clock):
    """Wozu es die Vormerkung gibt: im Fenster dunkel, hell erst danach."""
    await _setup(hass)
    wall_clock(11, 50)
    await _lux(hass, 100)
    wall_clock(12, 30)
    await _lux(hass, 1000)
    assert _drives(drive) == [70]


async def test_no_pending_without_a_dark_reading_in_the_window(hass, drive, wall_clock):
    await _setup(hass)
    wall_clock(12, 30)
    await _lux(hass, 1000)
    assert _drives(drive) == []


async def test_down_area_differs_from_up_area(hass, drive, wall_clock):
    """Die Vormerkung haengt am Hoch-Bereich, die Abendfahrt am Runter-Bereich."""
    abend = {**AREA, CONF_AREA_ID: "abend"}
    shutter = {**SHUTTER, CONF_AREA_DOWN_ID: "abend"}
    data = await _setup(hass, shutters=[shutter], areas=[AREA, abend])
    wall_clock(6, 30)
    await _lux(hass, 380)  # ueber "runter", unter "hoch": nur die Vormerkung
    assert "diele" in data["_pending_up"]
    wall_clock(15, 35)
    await _lux(hass, 0)
    assert _drives(drive) == [0]
    assert "diele" not in data["_pending_up"]
