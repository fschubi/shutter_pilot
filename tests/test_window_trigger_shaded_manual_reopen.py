"""Ein Beschattungs-Merker (shaded=True) ueberlebt eine manuelle Fahrt.

`elevation.py` raeumt sun_protect_covers nicht auf, wenn jemand den
Rollladen von Hand aus der Beschattung herausfaehrt - das ist Absicht, siehe
forget_shading_for_cover() ("Deliberately not called automatically when a
foreign drive is noticed"). Der Fenstertrigger benutzte genau diesen Merker
aber als unbedingten Grund zu reagieren ("Shading counts as a reason to
react, whatever the position"), unabhaengig von der tatsaechlichen Position.

Charly (community-smarthome.com/11378): Rollladen morgens von Hand voll
hochgefahren, kurz danach Fenster geoeffnet und wieder geschlossen - der
Rollladen fuhr wieder herunter, obwohl er laengst nicht mehr an seiner
Beschattungsposition stand. Der Fensterkontakt reagierte allein wegen des
alten Beschattungs-Merkers, nicht weil der Rollladen tatsaechlich noch im
Weg stand.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import set_cover_sun_protected

COVER = "cover.charly_test"
WINDOW = "binary_sensor.charly_fenster_test"

SHADE_POS = 40
VENT_POS = 50  # Kipp-/Lueftungsposition (2-Zustand-Kontakt Default)

AREA = {
    CONF_AREA_ID: "charly_area",
    CONF_AREA_NAME: "Charly-Bereich",
    CONF_AREA_MODE: AREA_MODE_NONE,
}


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Charly-Rollladen",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "none",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_SUN_PROTECT: SHADE_POS,
        CONF_POSITION_WHEN_WINDOW_TILTED: VENT_POS,
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture(autouse=True)
def _fast_startup(monkeypatch):
    from custom_components.shutter_pilot import cover_tracker

    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def cover_calls(hass):
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
    return [c.data["position"] for c in calls]


async def _setup(hass, start_position: float):
    hass.states.async_set(
        COVER, "open", {"current_position": start_position, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "off")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter()]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


class TestStaleShadeFlagDoesNotOverrideAManualReopen:
    async def test_a_fully_reopened_shutter_stays_put(self, hass, cover_calls):
        """Rollladen ist von Hand voll offen (100%), der Beschattungs-Merker
        aus der vorherigen Beschattung ist noch gesetzt. Fenster auf, ein
        paar Minuten spaeter wieder zu - der Rollladen darf sich in keiner
        Richtung ruehren, er steht laengst nicht mehr an seiner
        Beschattungsposition."""
        entry, data = await _setup(hass, start_position=100)
        assert data.get("commanded_positions", {}).get(COVER) is None

        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        assert _positions(cover_calls) == [], (
            "Ein bereits voll offener Rollladen darf beim Oeffnen des Fensters "
            f"nicht herunterfahren, ist aber gefahren: {_positions(cover_calls)}"
        )

        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()
        assert _positions(cover_calls) == []

    async def test_a_shutter_still_at_shade_position_still_reacts(
        self, hass, cover_calls
    ):
        """Gegenprobe zum Fix: steht der Rollladen tatsaechlich noch an
        seiner Beschattungsposition (der ursprueliche heinzig-/2.15.0-Fall),
        muss der Fensterkontakt weiterhin reagieren - der Fix darf das nicht
        mitgebrochen haben."""
        entry, data = await _setup(hass, start_position=SHADE_POS)
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert _positions(cover_calls) == [VENT_POS]
