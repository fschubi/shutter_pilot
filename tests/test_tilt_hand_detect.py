"""Handverstellung nur der Lamellen (Raffstore, Stufe 4, simon42 #172 Claus).

Der Tracker las nur `current_position` und kehrte bei unveraenderter Hoehe frueh
zurueck: eine reine Winkelaenderung war unsichtbar. Mit `tilt_hand_detect`
(Vorgabe aus) zaehlt sie wie eine Handfahrt - nicht aber die Nachmeldung
unserer eigenen Fahrt und nicht das Rauschen nach einer Hoehenfahrt."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import cover_tracker
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
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_SHUTTERS,
    CONF_TILT_CLOSED,
    CONF_TILT_ENABLED,
    CONF_TILT_HAND_DETECT,
    CONF_TILT_OPEN,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import set_cover_position
from custom_components.shutter_pilot.position_store import (
    SOURCE_MANUAL,
    get_position_store,
)

COVER = "cover.raff_diele"
AREA = {
    CONF_AREA_ID: "living",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
}


def _blind(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Diele",
        CONF_AREA_UP_ID: "living",
        CONF_AREA_DOWN_ID: "living",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 70,
        CONF_TILT_ENABLED: True,
        CONF_TILT_OPEN: 100,
        CONF_TILT_CLOSED: 40,
        CONF_TILT_HAND_DETECT: True,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture(autouse=True)
def _services(hass):
    async_mock_service(hass, "cover", "set_cover_position")
    async_mock_service(hass, "cover", "set_cover_tilt_position")


def _report(hass, position=70, tilt=40, state="open") -> None:
    hass.states.async_set(
        COVER,
        state,
        {
            "current_position": position,
            "current_tilt_position": tilt,
            "supported_features": 255,
        },
    )


async def _setup(hass, shutter: dict):
    _report(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [shutter]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _settle(hass, data) -> None:
    """Die Hoehe steht seit Ewigkeit still - nur der Winkel aendert sich."""
    data["_height_changed_at"] = {COVER: -1e9}
    data["recent_automation_covers"] = {}
    data["pending_automation_covers"] = set()
    await hass.async_block_till_done()


async def test_a_slat_only_change_counts_as_a_hand_move(hass):
    entry, data = await _setup(hass, _blind())
    await _settle(hass, data)

    _report(hass, tilt=75)
    await hass.async_block_till_done()

    assert COVER in data["_hand_moved_at"]
    store = get_position_store(hass, entry.entry_id)
    assert store.get_source_sync(COVER) == SOURCE_MANUAL


async def test_a_hand_move_drops_the_window_cycle(hass):
    _, data = await _setup(hass, _blind())
    await _settle(hass, data)
    data["trigger_actions"][COVER] = "triggered"
    data["trigger_heights"][COVER] = 70

    _report(hass, tilt=75)
    await hass.async_block_till_done()

    assert COVER not in data["trigger_actions"]
    assert COVER not in data["trigger_heights"]


async def test_without_the_hook_nothing_is_noticed(hass):
    """Bestandsschutz: ohne Haken bleibt der Tracker fuer Winkel blind."""
    _, data = await _setup(hass, _blind(**{CONF_TILT_HAND_DETECT: False}))
    await _settle(hass, data)

    _report(hass, tilt=75)
    await hass.async_block_till_done()

    assert COVER not in data.get("_hand_moved_at", {})


async def test_the_echo_of_our_own_tilt_is_not_a_hand_move(hass):
    entry, data = await _setup(hass, _blind())
    await _settle(hass, data)
    await set_cover_position(hass, entry, COVER, 70, "test", tilt_position=40)
    data["recent_automation_covers"] = {}  # Karenz vorbei, das Ziel bleibt gemerkt
    data["pending_automation_covers"] = set()

    _report(hass, tilt=42)  # KNX: 2 % daneben
    await hass.async_block_till_done()

    assert COVER not in data.get("_hand_moved_at", {})


async def test_noise_right_after_a_height_drive_is_ignored(hass, monkeypatch):
    """Nach einer Hoehenfahrt melden manche Aktoren kurz falsche Winkel."""
    _, data = await _setup(hass, _blind())
    await _settle(hass, data)
    monkeypatch.setattr(cover_tracker, "TILT_SETTLE_SEC", 15.0)
    data["commanded_positions"][COVER] = 100  # die Hoehenfahrt war unsere

    _report(hass, position=100, tilt=40)  # die Hoehe aendert sich
    _report(hass, position=100, tilt=0)  # kurz Lamellen 0
    await hass.async_block_till_done()

    assert COVER not in data.get("_hand_moved_at", {})


async def test_a_moving_cover_is_not_a_hand_move(hass):
    _, data = await _setup(hass, _blind())
    await _settle(hass, data)

    _report(hass, tilt=75, state="closing")
    await hass.async_block_till_done()

    assert COVER not in data.get("_hand_moved_at", {})


async def test_the_height_target_stays_after_a_hand_tilt(hass):
    """Die Hoehe hat niemand angefasst - ihr Ziel bleibt gueltig."""
    entry, data = await _setup(hass, _blind())
    await _settle(hass, data)
    await set_cover_position(hass, entry, COVER, 70, "test", tilt_position=40)
    data["recent_automation_covers"] = {}
    data["pending_automation_covers"] = set()

    _report(hass, tilt=90)
    await hass.async_block_till_done()

    assert data["commanded_positions"][COVER] == 70
    assert "commanded_tilts" not in data or COVER not in data["commanded_tilts"]
