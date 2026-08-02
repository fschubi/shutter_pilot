"""Automatik pro Rollladen – dritte Ebene unter Hauptschalter und Bereich.

Der Fall aus dem Forum: Ein Rollladen ist defekt und darf nicht fahren, seine
Konfiguration soll aber erhalten bleiben. Automatische Fahrten müssen ihn
auslassen, von Hand muss er weiterhin fahren – sonst kann man ihn nach der
Reparatur nicht einmal prüfen.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.shutter_pilot.const import (
    CONF_COVER_ENTITY_ID,
    CONF_SHUTTERS,
    CONF_SHUTTER_AUTOMATION_ENABLED,
    CONF_SHUTTER_AUTO_ENTITY_ID,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import is_shutter_automation_enabled


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


def _positions(calls) -> dict[str, int]:
    return {call.data["entity_id"]: call.data["position"] for call in calls}


def _shutter(cover: str = "cover.living_room", **overrides) -> dict:
    """Rollladen-Datensatz. `cover.spare` hat bewusst keinen Schalter und keinen
    Laufzeitwert – daran lässt sich der gespeicherte Wert allein prüfen."""
    shutter = {CONF_COVER_ENTITY_ID: cover}
    shutter.update(overrides)
    return shutter


class TestFlagResolution:
    """Reihenfolge: Laufzeitwert (Schalter) → Schalter-Entität → gespeicherter Wert.

    Der gespeicherte Wert ist nur der Startwert. Sobald es einen Schalter gibt,
    entscheidet der – sonst würde ein Umlegen in Home Assistant beim nächsten
    Reload wieder überschrieben.
    """

    def test_missing_key_counts_as_on(self, hass, entry):
        """Bestandsanlagen kennen den Schlüssel nicht – die müssen weiterlaufen."""
        assert is_shutter_automation_enabled(hass, entry, _shutter("cover.spare")) is True

    def test_config_value_off(self, hass, entry):
        shutter = _shutter("cover.spare", **{CONF_SHUTTER_AUTOMATION_ENABLED: False})
        assert is_shutter_automation_enabled(hass, entry, shutter) is False

    def test_switch_entity_beats_config(self, hass, entry):
        """Der Schalter ist die lebende Wahrheit, der gespeicherte Wert der Start."""
        hass.states.async_set("switch.sp_auto_test", "off")
        shutter = _shutter(
            "cover.spare",
            **{
                CONF_SHUTTER_AUTOMATION_ENABLED: True,
                CONF_SHUTTER_AUTO_ENTITY_ID: "switch.sp_auto_test",
            },
        )
        assert is_shutter_automation_enabled(hass, entry, shutter) is False

    def test_runtime_beats_switch_entity(self, hass, entry):
        """Der eigene Schalter des Rollladens hat den Laufzeitwert schon gesetzt."""
        hass.states.async_set("switch.sp_auto_test", "off")
        data = hass.data[DOMAIN][entry.entry_id]
        data.setdefault("shutter_automation", {})["cover.spare"] = True
        shutter = _shutter(
            "cover.spare", **{CONF_SHUTTER_AUTO_ENTITY_ID: "switch.sp_auto_test"}
        )
        assert is_shutter_automation_enabled(hass, entry, shutter) is True

    def test_unavailable_switch_does_not_block(self, hass, entry):
        """Fail open: Ein toter Schalter darf keinen Rollladen stilllegen."""
        hass.states.async_set("switch.sp_auto_test", "unavailable")
        shutter = _shutter(
            "cover.spare", **{CONF_SHUTTER_AUTO_ENTITY_ID: "switch.sp_auto_test"}
        )
        assert is_shutter_automation_enabled(hass, entry, shutter) is True

    def test_runtime_state_wins(self, hass, entry):
        """Umgelegter Schalter wirkt sofort, ohne Reload des Config-Entry."""
        data = hass.data[DOMAIN][entry.entry_id]
        data.setdefault("shutter_automation", {})["cover.living_room"] = False
        assert is_shutter_automation_enabled(hass, entry, _shutter()) is False


class TestSwitchEntity:
    def test_switch_created_per_shutter(self, hass, entry):
        """Je Rollladen ein eigener Schalter, zusätzlich zu Haupt- und Bereichsschalter."""
        assert hass.states.get("switch.shutter_pilot_auto_wohnzimmer") is not None
        assert hass.states.get("switch.shutter_pilot_auto_kuche") is not None

    async def test_turning_switch_off_updates_runtime(self, hass, entry):
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.shutter_pilot_auto_wohnzimmer"},
            blocking=True,
        )
        await hass.async_block_till_done()
        data = hass.data[DOMAIN][entry.entry_id]
        assert data["shutter_automation"]["cover.living_room"] is False


class TestDrivePaths:
    async def test_manual_service_still_drives_disabled_shutter(
        self, hass, entry, cover_calls
    ):
        """Der wichtigste Fall: Von Hand muss er weiter fahren."""
        data = hass.data[DOMAIN][entry.entry_id]
        data.setdefault("shutter_automation", {})["cover.living_room"] = False

        await hass.services.async_call(
            DOMAIN, "open_group", {"area_id": "living"}, blocking=True
        )
        await hass.async_block_till_done()

        assert _positions(cover_calls) == {
            "cover.living_room": 90,
            "cover.kitchen": 80,
        }

    async def test_scheduler_skips_disabled_shutter(self, hass, entry, cover_calls):
        """Geplante Fahrt: der abgeschaltete bleibt stehen, der andere fährt."""
        from custom_components.shutter_pilot.scheduler import setup_schedulers

        data = hass.data[DOMAIN][entry.entry_id]
        data.setdefault("shutter_automation", {})["cover.living_room"] = False
        await setup_schedulers(hass, entry)

        tick = data["_minute_callbacks"]["scheduler"]
        from datetime import datetime

        tick(datetime(2025, 7, 7, 19, 0))
        await hass.async_block_till_done()

        driven = _positions(cover_calls)
        assert "cover.living_room" not in driven
        assert driven.get("cover.kitchen") == 20


class TestOptionsRoundTrip:
    async def test_saved_value_survives(self, hass, entry):
        """Der Wert liegt im Config-Entry und geht beim Speichern nicht verloren."""
        from custom_components.shutter_pilot import _apply_shutter_automation_state

        shutters = [dict(s) for s in entry.options[CONF_SHUTTERS]]
        shutters[0][CONF_SHUTTER_AUTOMATION_ENABLED] = False
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_SHUTTERS: shutters}
        )
        _apply_shutter_automation_state(hass, entry, shutters[0])
        await hass.async_block_till_done()

        data = hass.data[DOMAIN][entry.entry_id]
        assert data["shutter_automation"]["cover.living_room"] is False
