"""c.radis Fall: der Rollladen parkt auf 74 %, einer Zahl, die nirgends steht.

Sein Fenstergriff meldet offen, gekippt und geschlossen. Offen und gekippt
werden korrekt angefahren – beim Schliessen bleibt der Rollladen auf 74 %
stehen. Weder `position_closed` (0) noch eine der Fensterpositionen (100/15)
erklaeren die Zahl.
"""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot.const import (
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_UP_ID,
    CONF_AREA_VENT_ENABLED,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
    VENT_CONDITION_SLOTS,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import set_cover_position

COVER = "cover.arbeitszimmer_links"
WINDOW = "sensor.arbeitszimmer_fenster_links"
VENT_SENSOR = "binary_sensor.lueften"

AREA = {
    CONF_AREA_ID: "arbeiten",
    CONF_AREA_NAME: "Arbeiten",
    CONF_AREA_MODE: AREA_MODE_BRIGHTNESS,
    CONF_AREA_DRIVE_DELAY: 0,
}


def _shutter(**overrides) -> dict:
    """c.radis „Arbeitszimmer links", Werte aus seinem Export."""
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Arbeitszimmer links",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "open",
        CONF_WINDOW_TILTED_STATE: "tilted",
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_WHEN_WINDOW_TILTED: 15,
        CONF_POSITION_WHEN_WINDOW_OPEN: 100,
        CONF_WINDOW_CLOSE_DEBOUNCE: 5,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


def _positions(calls) -> list[int]:
    return [int(call.data["position"]) for call in calls]


@contextlib.contextmanager
def _gated_sleep(gated_delay: int = 5):
    """Nur die Entprellungs-Wartezeit anhalten – `asyncio` ist das globale Modul."""
    gate = asyncio.Event()
    real_sleep = asyncio.sleep

    async def _sleep(seconds, *args, **kwargs):
        if seconds == gated_delay:
            await gate.wait()
            return None
        return await real_sleep(seconds, *args, **kwargs)

    try:
        with patch.object(asyncio, "sleep", _sleep):
            yield gate
    finally:
        gate.set()


async def _tick(hass, data) -> None:
    for cb in list(data.get("_minute_callbacks", {}).values()):
        cb(dt_util.now())
    await hass.async_block_till_done()


async def _setup(hass, shutter: dict, position: int, state: str = "open", area=None):
    hass.states.async_set(
        COVER, state, {"current_position": position, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "closed")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [area or AREA], CONF_SHUTTERS: [shutter]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _window(hass, state: str) -> None:
    hass.states.async_set(WINDOW, state)
    await hass.async_block_till_done()


async def _window_bounce(hass, state: str) -> None:
    hass.states.async_set(WINDOW, state)
    for _ in range(10):
        await asyncio.sleep(0)


def _moving(hass, position: float, direction: str = "closing") -> None:
    """Der Rollladen ist unterwegs – die gemeldete Position ist eine Momentaufnahme."""
    hass.states.async_set(
        COVER, direction, {"current_position": position, "supported_features": 15}
    )


def _resting(hass, position: float) -> None:
    hass.states.async_set(
        COVER,
        "closed" if position <= 0 else "open",
        {"current_position": position, "supported_features": 15},
    )


class TestParkedMidTravel:
    """Fenster wird angefasst, waehrend der Abendlauf noch faehrt."""

    async def test_restore_uses_the_target_not_the_snapshot(self, hass, cover_calls):
        entry, data = await _setup(hass, _shutter(), position=100)

        # Abends: die Helligkeit faehrt zu. Der Rollladen ist unterwegs.
        await set_cover_position(hass, entry, COVER, 0, "Abendfahrt")
        _moving(hass, 74)
        await hass.async_block_till_done()
        cover_calls.clear()

        # Waehrend er faehrt, wird das Fenster geoeffnet.
        await _window(hass, "open")
        assert _positions(cover_calls) == [100], "Fensterposition wird angefahren"
        _resting(hass, 100)
        await hass.async_block_till_done()

        # ... und gekippt.
        await _window(hass, "tilted")
        assert _positions(cover_calls) == [100, 15]
        _resting(hass, 15)
        await hass.async_block_till_done()

        # Griff zurueck auf zu: laeuft durch „offen".
        with _gated_sleep() as gate:
            await _window_bounce(hass, "open")
            await _window_bounce(hass, "closed")
            _moving(hass, 74, "opening")
            await _window_bounce(hass, "closed")
            gate.set()
            await hass.async_block_till_done()

        assert _positions(cover_calls)[-1] == 0, (
            f"zurueck auf geschlossen, nicht auf eine Zwischenstellung: "
            f"{_positions(cover_calls)}"
        )
        assert data["trigger_heights"].get(COVER) != 74

    async def test_a_resting_cover_keeps_its_reported_height(self, hass, cover_calls):
        """Steht er still, gilt weiter die Meldung – auch mitten im Weg."""
        entry, data = await _setup(hass, _shutter(), position=100)
        await set_cover_position(hass, entry, COVER, 0, "Abendfahrt")
        # Angekommen, aber nicht auf 0: von Hand auf 60 geparkt.
        _resting(hass, 60)
        await hass.async_block_till_done()
        cover_calls.clear()

        await _window(hass, "open")
        assert data["trigger_heights"][COVER] == 60, (
            "eine Handstellung ist eine Stellung, kein Durchgangswert"
        )


class TestCommandedPosition:
    async def test_a_hand_drive_drops_our_target(self, hass, cover_calls):
        """Wer von aussen faehrt, macht unser Ziel wertlos."""
        entry, data = await _setup(hass, _shutter(), position=100)
        await set_cover_position(hass, entry, COVER, 0, "Abendfahrt")
        await hass.async_block_till_done()
        assert data["commanded_positions"][COVER] == 0

        # Karenz abwarten waere der echte Weg – hier reicht die Buchung:
        # der Mitschreiber verbucht die Fahrt als manuell.
        data["pending_automation_covers"].discard(COVER)
        data["recent_automation_covers"].pop(COVER, None)
        _moving(hass, 55, "opening")
        await hass.async_block_till_done()

        assert COVER not in data["commanded_positions"]

    async def test_restore_falls_back_to_the_target_not_the_live_mirror(
        self, hass, cover_calls
    ):
        """Ohne Rueckfahrhoehe zaehlt das letzte Ziel, nicht der Mitschnitt."""
        from custom_components.shutter_pilot import window_trigger

        entry, data = await _setup(hass, _shutter(), position=0, state="closed")
        await _window(hass, "tilted")
        _resting(hass, 15)
        await hass.async_block_till_done()

        # Die Rueckfahrhoehe geht verloren, der Zyklus bleibt stehen.
        data["trigger_heights"].pop(COVER, None)
        await set_cover_position(hass, entry, COVER, 30, "irgendwas")
        _moving(hass, 21, "opening")
        await hass.async_block_till_done()
        cover_calls.clear()

        with _gated_sleep() as gate:
            await _window_bounce(hass, "closed")
            gate.set()
            await hass.async_block_till_done()

        assert _positions(cover_calls) == [30], (
            "last_positions ist der laufende Mitschnitt – als Ziel heisst das "
            "„bleib stehen, wo du bist\""
        )


class TestVentilation:
    """`vent_heights` ist dieselbe Frage wie `trigger_heights`.

    Nicht ueber die Hilfsfunktion geprueft, sondern ueber den Minutentakt:
    entschieden wird in der Schleife, nicht in der Funktion – die Verdrahtung
    ist hier die Aenderung (2.17.0, 2.20.0).
    """

    async def test_the_tick_does_not_remember_a_moving_cover(self, hass, cover_calls):
        vent_area = dict(AREA)
        vent_area[CONF_AREA_VENT_ENABLED] = True
        a_entity, _on, _off, _states = sun_condition_keys(VENT_CONDITION_SLOTS[0])
        vent_area[a_entity] = VENT_SENSOR

        hass.states.async_set(VENT_SENSOR, "off")
        shutter = _shutter(**{CONF_AREA_UP_ID: "arbeiten", CONF_AREA_DOWN_ID: "arbeiten"})
        entry, data = await _setup(hass, shutter, position=100, area=vent_area)

        # Abendfahrt laeuft noch, der Rollladen ist bei 74 unterwegs nach 0.
        await set_cover_position(hass, entry, COVER, 0, "Abendfahrt")
        _moving(hass, 74)
        await hass.async_block_till_done()

        hass.states.async_set(VENT_SENSOR, "on")
        await _tick(hass, data)

        assert data["vent_heights"][COVER] == 0, (
            f"nicht die Durchgangszahl: {data['vent_heights'].get(COVER)}"
        )

        # Und zurueck geht es auf 0, nicht auf 74.
        cover_calls.clear()
        hass.states.async_set(VENT_SENSOR, "off")
        await _tick(hass, data)
        assert _positions(cover_calls) == [0]
