"""Lüften mit Bedingungen – Anregung von Linos aus dem Forum.

Bisher war Lüften rein manuell. Jetzt lassen sich Entitäten angeben, die alle
erfüllt sein müssen, damit der Rollladen von selbst auf die Lüftungsposition
fährt – und zurück, sobald eine davon wegfällt.

Rangfolge, die hier festgeschrieben wird:
Fensterkontakt > Beschattung > Lüften.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import cover_tracker, ventilation
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREA_VENT_ENABLED,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    DOMAIN,
    VENT_CONDITION_SLOTS,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    set_cover_sun_protected,
    vent_conditions_met,
)

COVER = "cover.living_room"
PRESENCE = "binary_sensor.at_home"
TEMP = "sensor.room_temp"


def _area(**overrides) -> dict:
    """Bereich mit Linos' Beispiel: Entität = true UND Entität > 24."""
    a_entity, _on, _off, _s = sun_condition_keys(VENT_CONDITION_SLOTS[0])
    b_entity, b_on, b_off, _s2 = sun_condition_keys(VENT_CONDITION_SLOTS[1])
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_NAME: "Wohnbereich",
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_VENT_ENABLED: True,
        a_entity: PRESENCE,
        b_entity: TEMP,
        b_on: 24.0,
        b_off: 22.0,
    }
    area.update(overrides)
    return area


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Wohnzimmer",
        CONF_AREA_UP_ID: "living",
        CONF_AREA_DOWN_ID: "living",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_WHEN_WINDOW_TILTED: 50,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture(autouse=True)
def _fast_startup_restore():
    """Den Startup-Restore nicht abwarten.

    Er wartet fünf Sekunden, bevor er Positionen prüft – und wird hier
    ausgelöst, sobald das Lüften einmal gefahren ist.
    """
    with patch.object(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0), patch.object(
        cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0
    ):
        yield


@pytest.fixture
def cover_calls(hass):
    """Mitschreiben und den Rollladen tatsächlich bewegen.

    Ein reiner Mock lässt die Position auf dem alten Wert stehen; der
    Startup-Restore hält das für eine verschluckte Fahrt und wiederholt sie.
    """
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


def _conditions(hass, present: bool, temp: float) -> None:
    hass.states.async_set(PRESENCE, "on" if present else "off")
    hass.states.async_set(TEMP, temp)


async def _setup(hass, area=None, shutter=None, cover_position: int = 0):
    hass.states.async_set(
        COVER, "closed", {"current_position": cover_position, "supported_features": 15}
    )
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [area or _area()],
            CONF_SHUTTERS: [shutter or _shutter()],
        },
    )
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry, hass.data[DOMAIN][config_entry.entry_id]


async def _blocked_setup(hass, **kwargs):
    """Aufsetzen, ohne dass sofort gelüftet wird.

    `setup_ventilation` wertet einmal beim Start aus – eine Sperre, die erst
    danach gesetzt wird, käme zu spät.
    """
    _conditions(hass, present=False, temp=15.0)
    return await _setup(hass, **kwargs)


async def _evaluate(hass, entry) -> None:
    """Einen Minutentakt auslösen, ohne auf die Uhr zu warten."""
    await ventilation.setup_ventilation(hass, entry)
    await hass.async_block_till_done()


class TestConditions:
    async def test_all_conditions_must_hold(self, hass):
        _conditions(hass, present=True, temp=26.0)
        assert vent_conditions_met(hass, _area(), {}) is True

    async def test_one_missing_is_enough_to_stop(self, hass):
        _conditions(hass, present=False, temp=26.0)
        assert vent_conditions_met(hass, _area(), {}) is False

    async def test_numeric_below_threshold(self, hass):
        _conditions(hass, present=True, temp=20.0)
        assert vent_conditions_met(hass, _area(), {}) is False

    async def test_unconfigured_never_triggers(self, hass):
        """Fail closed – wer nichts einträgt, bekommt keine Fahrten."""
        area = {CONF_AREA_ID: "living", CONF_AREA_VENT_ENABLED: True}
        assert vent_conditions_met(hass, area, {}) is False

    async def test_hysteresis_on_the_numeric_slot(self, hass):
        data: dict = {}
        area = _area()
        _conditions(hass, present=True, temp=26.0)
        assert vent_conditions_met(hass, area, data) is True
        _conditions(hass, present=True, temp=23.0)  # zwischen 22 und 24
        assert vent_conditions_met(hass, area, data) is True, "hält"
        _conditions(hass, present=True, temp=21.0)
        assert vent_conditions_met(hass, area, data) is False


class TestDriving:
    async def test_drives_to_the_ventilation_position(self, hass, cover_calls):
        _conditions(hass, present=True, temp=26.0)
        entry, data = await _setup(hass)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == [50]
        assert ventilation.is_cover_ventilating(data, COVER)
        assert data["vent_heights"][COVER] == 0

    async def test_returns_to_where_it_stood(self, hass, cover_calls):
        """Zurück auf die vorherige Position, nicht auf "offen" – nachts wäre
        das falsch."""
        _conditions(hass, present=True, temp=26.0)
        entry, data = await _setup(hass, cover_position=0)
        await _evaluate(hass, entry)

        _conditions(hass, present=True, temp=20.0)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == [50, 0]
        assert not ventilation.is_cover_ventilating(data, COVER)

    async def test_does_not_drive_twice(self, hass, cover_calls):
        _conditions(hass, present=True, temp=26.0)
        entry, _data = await _setup(hass)
        await _evaluate(hass, entry)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == [50]

    async def test_nothing_when_conditions_never_hold(self, hass, cover_calls):
        _conditions(hass, present=False, temp=15.0)
        entry, _data = await _setup(hass)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []

    async def test_already_in_position_is_left_alone(self, hass, cover_calls):
        _conditions(hass, present=True, temp=26.0)
        entry, data = await _setup(hass, cover_position=50)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []
        assert not ventilation.is_cover_ventilating(data, COVER)

    async def test_disabled_area_is_not_watched(self, hass, cover_calls):
        _conditions(hass, present=True, temp=26.0)
        entry, data = await _setup(hass, area=_area(**{CONF_AREA_VENT_ENABLED: False}))
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []
        assert "ventilation" not in data.get("_minute_callbacks", {})


class TestRanking:
    """Fensterkontakt > Beschattung > Lüften."""

    async def test_shading_wins(self, hass, cover_calls):
        entry, data = await _blocked_setup(hass)
        set_cover_sun_protected(data, COVER, True)
        _conditions(hass, present=True, temp=26.0)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []

    async def test_window_contact_wins(self, hass, cover_calls):
        entry, data = await _blocked_setup(hass)
        data["trigger_actions"][COVER] = "triggered"
        _conditions(hass, present=True, temp=26.0)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []

    async def test_open_window_is_left_alone(self, hass, cover_calls):
        """Steht das Fenster offen, regelt der Fenstertrigger – nicht wir."""
        _conditions(hass, present=True, temp=26.0)
        shutter = _shutter(window_entity_id="binary_sensor.window", window_open_state="on")
        hass.states.async_set("binary_sensor.window", "on")
        entry, _data = await _setup(hass, shutter=shutter)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []


class TestSwitches:
    async def test_area_switch_off_blocks_the_start(self, hass, cover_calls):
        entry, data = await _blocked_setup(hass)
        data["auto_modes"] = {"living": False}
        _conditions(hass, present=True, temp=26.0)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []

    async def test_master_switch_off_blocks_the_start(self, hass, cover_calls):
        entry, data = await _blocked_setup(hass)
        data["master_enabled"] = False
        _conditions(hass, present=True, temp=26.0)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []

    async def test_shutter_automation_off_blocks_the_start(self, hass, cover_calls):
        entry, data = await _blocked_setup(hass)
        data["shutter_automation"] = {COVER: False}
        _conditions(hass, present=True, temp=26.0)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == []

    async def test_switching_the_area_off_still_releases(self, hass, cover_calls):
        """Sonst bliebe der Rollladen halb offen stehen."""
        _conditions(hass, present=True, temp=26.0)
        entry, data = await _setup(hass)
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == [50]

        data["auto_modes"] = {"living": False}
        await _evaluate(hass, entry)
        assert _positions(cover_calls) == [50, 0], "fährt zurück"
