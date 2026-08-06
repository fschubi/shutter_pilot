"""Entprellung des Fensterkontakts – der Fall von Xerenas aus dem Forum.

Beim Drehen des Griffs von "gekippt" auf "offen" läuft der Kontakt kurz durch
"geschlossen". Ohne Wartezeit fährt der Rollladen sofort zurück, und die
Offen-Position wird nie angefahren.

`window_trigger.py` hatte bis hierher keinerlei Testabdeckung.
"""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import window_trigger
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)

COVER = "cover.living_room"
WINDOW = "sensor.living_room_window"

AREA = {
    CONF_AREA_ID: "living",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
}


def _shutter(**overrides) -> dict:
    """Dreizustands-Kontakt: offen, gekippt und geschlossen sind unterscheidbar."""
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Wohnzimmer",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "tilted",
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_WHEN_WINDOW_TILTED: 50,
        CONF_POSITION_WHEN_WINDOW_OPEN: 100,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


def _positions(calls) -> list[int]:
    return [call.data["position"] for call in calls]


@contextlib.contextmanager
def _gated_sleep(gated_delay: int = 5):
    """Ein steuerbarer Schlaf.

    Ein AsyncMock liefe sofort durch und machte das Abbrechen untestbar – hier
    hängt der Task, bis der Test das Gate öffnet.

    Angehalten wird ausschliesslich die Entprellungs-Wartezeit: `window_trigger.
    asyncio` *ist* das globale Modul, ein pauschaler Patch legt damit auch Home
    Assistant selbst lahm.
    """
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
        # Nachzügler freilassen, sonst wartet der Teardown ewig.
        gate.set()


async def _setup(hass, shutter: dict, cover_position: int = 0):
    hass.states.async_set(
        COVER, "closed", {"current_position": cover_position, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "closed")
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [shutter]},
    )
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry, hass.data[DOMAIN][config_entry.entry_id]


async def _window(hass, state: str) -> None:
    """Fensterzustand melden und alles zu Ende laufen lassen."""
    hass.states.async_set(WINDOW, state)
    await hass.async_block_till_done()


async def _window_bounce(hass, state: str) -> None:
    """Wie `_window`, aber ohne auf den Entprellungs-Task zu warten.

    `async_block_till_done()` wartet auch auf den gerade erzeugten Task – der
    hängt am Gate, und der Test käme nie zurück.
    """
    hass.states.async_set(WINDOW, state)
    for _ in range(10):
        await asyncio.sleep(0)


class TestHandleThroughClosed:
    """Der gemeldete Fall."""

    async def test_open_position_is_reached(self, hass, cover_calls):
        _, data = await _setup(hass, _shutter())

        await _window(hass, "tilted")
        assert _positions(cover_calls) == [50]
        # Der Rollladen steht jetzt auf Lüftung.
        hass.states.async_set(
            COVER, "open", {"current_position": 50, "supported_features": 15}
        )

        with _gated_sleep():
            await _window_bounce(hass, "closed")  # Griff läuft durch "zu"
            await _window_bounce(hass, "open")  # und weiter auf "offen"

        assert _positions(cover_calls) == [50, 100], "keine Rückfahrt, dann offen"
        assert data["_window_close_tasks"] == {}

    async def test_restore_height_stays_the_pre_cycle_position(self, hass, cover_calls):
        """Die Kipp-Position darf nicht zur Rückfahrhöhe werden."""
        _, data = await _setup(hass, _shutter(), cover_position=0)

        await _window(hass, "tilted")
        hass.states.async_set(
            COVER, "open", {"current_position": 50, "supported_features": 15}
        )
        with _gated_sleep():
            await _window_bounce(hass, "closed")
            await _window_bounce(hass, "open")

        assert data["trigger_heights"][COVER] == 0


class TestZeroDelay:
    async def test_behaves_exactly_like_before(self, hass, cover_calls):
        """0 s muss synchron bleiben – kein Task, keine geänderte Reihenfolge."""
        _, data = await _setup(hass, _shutter(**{CONF_WINDOW_CLOSE_DEBOUNCE: 0}))

        await _window(hass, "tilted")
        hass.states.async_set(
            COVER, "open", {"current_position": 50, "supported_features": 15}
        )

        with _gated_sleep() as gate:
            await _window_bounce(hass, "closed")
            # Ohne dass das Gate je geöffnet wurde:
            assert _positions(cover_calls) == [50, 0], "Rückfahrt sofort"
            assert not gate.is_set()
        assert not data.get("_window_close_tasks")


class TestRealClose:
    async def test_restores_after_the_delay(self, hass, cover_calls):
        _, data = await _setup(hass, _shutter())

        await _window(hass, "tilted")
        hass.states.async_set(
            COVER, "open", {"current_position": 50, "supported_features": 15}
        )

        with _gated_sleep() as gate:
            await _window_bounce(hass, "closed")
            assert _positions(cover_calls) == [50], "noch nichts gefahren"
            gate.set()
            await hass.async_block_till_done()

        assert _positions(cover_calls) == [50, 0], "genau eine Rückfahrt"
        assert COVER not in data["trigger_actions"]
        assert COVER not in data["trigger_heights"]

    async def test_nothing_happens_without_a_cycle(self, hass, cover_calls):
        """Ein Fenster, das nie offen war, löst beim Schließen keine Fahrt aus."""
        await _setup(hass, _shutter())
        with _gated_sleep() as gate:
            await _window_bounce(hass, "closed")
            gate.set()
            await hass.async_block_till_done()
        assert _positions(cover_calls) == []


class TestDriveAfterClose:
    async def test_pending_survives_a_short_bounce(self, hass, cover_calls):
        """Der Nachhol-Eintrag darf beim Prellimpuls nicht verloren gehen."""
        _, data = await _setup(hass, _shutter())
        data["drive_after_close_pending"][COVER] = {
            "position": 0,
            "reason": "Nachholen",
            "tilt": None,
        }

        with _gated_sleep():
            await _window_bounce(hass, "closed")
            await _window_bounce(hass, "open")

        assert COVER in data["drive_after_close_pending"], "Eintrag noch da"

        # Jetzt wirklich schließen.
        with _gated_sleep() as gate:
            await _window_bounce(hass, "closed")
            gate.set()
            await hass.async_block_till_done()

        assert COVER not in data["drive_after_close_pending"]
        assert _positions(cover_calls).count(0) == 1, "genau einmal nachgeholt"


class TestStateRecheck:
    async def test_state_changed_back_without_an_event(self, hass, cover_calls):
        """Nach dem Schlaf wird der Zustand neu gelesen, nicht geglaubt."""
        _, data = await _setup(hass, _shutter())

        await _window(hass, "tilted")
        hass.states.async_set(
            COVER, "open", {"current_position": 50, "supported_features": 15}
        )

        with _gated_sleep() as gate:
            await _window_bounce(hass, "closed")
            # Zustand wechselt zurück, ohne dass ein Event ankommt: die
            # Listener werden vorher abbestellt. Damit greift als einzige
            # Sicherung die erneute Abfrage nach dem Schlaf.
            for unsub in data["_window_unsubs"]:
                unsub()
            data["_window_unsubs"] = []
            hass.states.async_set(WINDOW, "tilted")
            gate.set()
            await hass.async_block_till_done()

        assert _positions(cover_calls) == [50], "keine Rückfahrt"


class TestCancellation:
    async def _pending(self, hass, cover_calls):
        entry, data = await _setup(hass, _shutter())
        await _window(hass, "tilted")
        hass.states.async_set(
            COVER, "open", {"current_position": 50, "supported_features": 15}
        )
        return entry, data

    async def test_unload_cancels(self, hass, cover_calls):
        with _gated_sleep():
            entry, data = await self._pending(hass, cover_calls)
            await _window_bounce(hass, "closed")
            task = data["_window_close_tasks"][COVER]

            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()

        assert task.cancelled() or task.done()
        assert _positions(cover_calls) == [50]

    async def test_reload_cancels(self, hass, cover_calls):
        """Sonst führe ein Timer die Konfiguration von vor dem Speichern aus."""
        with _gated_sleep():
            entry, data = await self._pending(hass, cover_calls)
            await _window_bounce(hass, "closed")
            task = data["_window_close_tasks"][COVER]

            await window_trigger.setup_window_triggers(hass, entry)
            await hass.async_block_till_done()

        assert task.cancelled() or task.done()
        assert data["_window_close_tasks"] == {}

    async def test_automation_off_cancels(self, hass, cover_calls):
        """Ein abgeschalteter Rollladen darf nicht doch noch nachfahren."""
        with _gated_sleep():
            entry, data = await self._pending(hass, cover_calls)
            await _window_bounce(hass, "closed")
            task = data["_window_close_tasks"][COVER]

            data["shutter_automation"] = {COVER: False}
            # Irgendein Fenster-Event: der Automatik-Zweig greift, bevor der
            # Zustand überhaupt ausgewertet wird.
            await _window_bounce(hass, "open")

        await hass.async_block_till_done()
        assert task.cancelled()
        assert _positions(cover_calls) == [50], "keine weitere Fahrt"


class TestDebounceClamping:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (-5, 0),
            (0, 0),
            (7, 7),
            (30, 30),
            (999, 30),
            ("abc", 5),
            (None, 5),
        ],
    )
    def test_clamped(self, value, expected):
        assert window_trigger._debounce_seconds(
            {CONF_WINDOW_CLOSE_DEBOUNCE: value}
        ) == expected

    def test_missing_key_uses_default(self):
        assert window_trigger._debounce_seconds({}) == 5
