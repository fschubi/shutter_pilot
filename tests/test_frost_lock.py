"""Frostsperre für Rollläden (eurofinder, simon42 #237).

Der bestehende Frostschutz kürzt nur die Abendfahrt. Die Frostsperre hält
*jede* automatische Fahrt an, solange es kalt ist, fährt optional in eine
Frostposition und holt nach dem Frost nach, was die Sperre verschluckt hat.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import awning_guard
from custom_components.shutter_pilot.awning_guard import async_enforce_guard
from custom_components.shutter_pilot.const import (
    CONF_AREA_DOWN_ID,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_FROST_LOCK,
    CONF_FROST_LOCK_CATCH_UP,
    CONF_FROST_LOCK_POSITION,
    CONF_NAME,
    CONF_SHUTTERS,
    DOMAIN,
    ROLE_CLOSED,
    ROLE_OPEN,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import shutter_held
from tests.test_window_debounce import AREA, COVER, WINDOW

SENSOR = "sensor.outdoor_temp"


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Velux",
        CONF_AREA_UP_ID: "living",
        CONF_AREA_DOWN_ID: "living",
        CONF_FROST_LOCK: True,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture(autouse=True)
def _no_schedule():
    """Der Zeitplan hängt am Minutentakt mit der echten Uhr.

    Fällt ein Minutenwechsel in den Test, fährt er je nach Tageszeit "hoch"
    und verfälscht die Fahrliste – er gehört nicht zu dem, was hier geprüft
    wird. Für die ganze Testdauer abgeschaltet, nicht nur beim Setup.
    """
    with patch(
        "custom_components.shutter_pilot.scheduler.is_auto_enabled", return_value=False
    ):
        yield


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


def _positions(calls) -> list[int]:
    return [call.data["position"] for call in calls]


def _cover(hass, position: int) -> None:
    hass.states.async_set(
        COVER, "open", {"current_position": position, "supported_features": 15}
    )


async def _setup(hass, shutter: dict, **options):
    _cover(hass, 100)
    hass.states.async_set(SENSOR, "10")
    ent, on, off, _ = sun_condition_keys("cold")
    opts = {
        CONF_AREAS: [AREA],
        CONF_SHUTTERS: [shutter],
        ent: SENSOR,
        on: 2,
        off: 4,
        **options,
    }
    entry = MockConfigEntry(domain=DOMAIN, title="Shutter Pilot", options=opts)
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _temp(hass, entry, value: str) -> None:
    hass.states.async_set(SENSOR, value)
    await hass.async_block_till_done()
    await async_enforce_guard(hass, entry)
    await hass.async_block_till_done()


def _held(hass, entry, shutter) -> bool:
    return shutter_held(hass, entry, shutter)


async def test_frost_drives_to_position_and_holds(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, _ = await _setup(hass, shutter)
    assert not _held(hass, entry, shutter)

    await _temp(hass, entry, "1")

    assert _positions(cover_calls) == [0]
    assert _held(hass, entry, shutter)


async def test_without_position_it_only_holds(hass, cover_calls):
    shutter = _shutter()
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "1")
    assert _positions(cover_calls) == []
    assert _held(hass, entry, shutter)


async def test_hysteresis_keeps_holding_between_the_thresholds(hass, cover_calls):
    shutter = _shutter()
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "1")
    await _temp(hass, entry, "3")
    assert _held(hass, entry, shutter), "3 liegt zwischen 2 und 4"
    await _temp(hass, entry, "5")
    assert not _held(hass, entry, shutter)


async def test_not_opted_in_is_untouched(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK: False})
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "-5")
    assert not _held(hass, entry, shutter)
    assert _positions(cover_calls) == []


async def test_dead_sensor_never_holds(hass, cover_calls):
    """Ein leerer Akku darf das Haus nicht den ganzen Winter stilllegen."""
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "unavailable")
    assert not _held(hass, entry, shutter)
    assert _positions(cover_calls) == []


async def test_catch_up_after_the_frost(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "1")
    _cover(hass, 0)  # der Rollladen ist angekommen
    with patch.object(awning_guard, "scheduled_role_now", return_value=ROLE_OPEN):
        await _temp(hass, entry, "6")
    assert _positions(cover_calls) == [0, 100], "Morgenfahrt nachgeholt"
    assert not _held(hass, entry, shutter)


async def test_catch_up_can_be_switched_off(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, _ = await _setup(hass, shutter, **{CONF_FROST_LOCK_CATCH_UP: False})
    await _temp(hass, entry, "1")
    _cover(hass, 0)
    with patch.object(awning_guard, "scheduled_role_now", return_value=ROLE_OPEN):
        await _temp(hass, entry, "6")
    assert _positions(cover_calls) == [0]
    assert not _held(hass, entry, shutter)


async def test_hand_drive_during_frost_is_not_overridden(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "1")
    _cover(hass, 60)  # von Hand gefahren
    with patch.object(awning_guard, "scheduled_role_now", return_value=ROLE_OPEN):
        await _temp(hass, entry, "6")
    assert _positions(cover_calls) == [0], "nichts nachgeholt"
    assert not _held(hass, entry, shutter)


async def test_no_catch_up_with_open_window(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "1")
    _cover(hass, 0)
    with patch.object(awning_guard, "scheduled_role_now", return_value=ROLE_OPEN), patch.object(
        awning_guard, "is_window_open_or_tilted", return_value=True
    ):
        await _temp(hass, entry, "6")
    assert _positions(cover_calls) == [0]


async def test_catch_up_to_closed_after_a_frosty_evening(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 100})
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "1")
    _cover(hass, 100)
    with patch.object(awning_guard, "scheduled_role_now", return_value=ROLE_CLOSED):
        await _temp(hass, entry, "6")
    assert _positions(cover_calls)[-1] == 0


async def test_automation_off_holds_but_does_not_drive(hass, cover_calls):
    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, data = await _setup(hass, shutter)
    data["shutter_automation"] = {COVER: False}
    await _temp(hass, entry, "1")
    assert _positions(cover_calls) == []


async def test_export_names_the_frost_lock(hass, cover_calls):
    """Der Export zeigt Sperre, Schwellen und Urteil – aus dem eigenen Zustand."""
    from custom_components.shutter_pilot.export import async_build_export  # noqa: PLC0415

    shutter = _shutter(**{CONF_FROST_LOCK_POSITION: 0})
    entry, _ = await _setup(hass, shutter)
    await _temp(hass, entry, "1")
    report = (await async_build_export(hass, entry))["markdown"]
    assert "Frostsperre:" in report
    assert "Gefahr unter 2" in report
    assert "⛔ cold" in report
