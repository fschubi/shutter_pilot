"""Hinweise im Export, die ohne laufende Automatik pruefbar sind.

Bewusst nicht in `test_forum_findings.py`: dessen Fixture kostet rund vierzehn
Sekunden je Test. Hier braucht nichts davon zu laufen – der Export liest
Optionen und das Laufzeit-Dict, beides laesst sich hinstellen.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.util import dt as dt_util

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ELEVATION_ENABLED,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_LOCK_PROTECTION,
    CONF_NAME,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_SUN_GEOMETRY_OVERRIDE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)
from custom_components.shutter_pilot.export import (
    _silent_setting_notes,
    async_build_export,
)

COVER = "cover.kueche_vorne"
AREA = {
    CONF_AREA_ID: "vorne",
    CONF_AREA_NAME: "Wohnbereich vorne",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_SUN_PROTECT_ENABLED: True,
}


# --- Einstellungen, die dastehen und nichts tun ------------------------------


class TestSilentSettings:
    """Beides aus Wolfs Export: gespeichert, sichtbar, wirkungslos."""

    def test_own_geometry_without_the_override_switch_is_named(self):
        notes = "\n".join(
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: False,
                    CONF_AREA_ELEVATION_MIN: 19.5,
                    CONF_AREA_ELEVATION_MAX: 67.5,
                }
            )
        )
        assert "Eigene Ausrichtung" in notes
        assert "elevation_min" in notes

    def test_with_the_switch_on_the_values_apply_and_stay_quiet(self):
        assert (
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: True,
                    CONF_AREA_ELEVATION_MIN: 19.5,
                }
            )
            == []
        )

    def test_the_switched_off_height_check_is_named_too(self):
        """Ohne „Eigene Ausrichtung" liest die Beschattung den Haken nie."""
        notes = "\n".join(
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: False,
                    CONF_AREA_ELEVATION_ENABLED: False,
                }
            )
        )
        assert "elevation_enabled" in notes

    def test_the_switched_on_height_check_is_no_deviation(self):
        """Eingeschaltet ist die Vorgabe – als Warnung waere das Rauschen."""
        assert (
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: False,
                    CONF_AREA_ELEVATION_ENABLED: True,
                }
            )
            == []
        )

    def test_azimuth_counts_as_geometry_too(self):
        notes = "\n".join(
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_AREA_AZIMUTH_ENABLED: True,
                    CONF_AREA_AZIMUTH_MIN: 100,
                    CONF_AREA_AZIMUTH_MAX: 240,
                }
            )
        )
        assert "azimuth_min" in notes

    def test_two_state_contact_names_the_position_that_never_runs(self):
        notes = "\n".join(
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: True,
                    CONF_WINDOW_ENTITY_ID: "binary_sensor.tuer",
                    CONF_WINDOW_TILTED_STATE: "none",
                    CONF_POSITION_WHEN_WINDOW_OPEN: 100,
                    CONF_POSITION_WHEN_WINDOW_TILTED: 0,
                }
            )
        )
        assert "position_when_window_tilted" in notes
        assert "0 %" in notes
        assert "100 %" in notes

    def test_a_three_state_contact_uses_both_and_gets_no_note(self):
        assert (
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: True,
                    CONF_WINDOW_ENTITY_ID: "binary_sensor.tuer",
                    CONF_WINDOW_TILTED_STATE: "tilted",
                    CONF_POSITION_WHEN_WINDOW_OPEN: 100,
                    CONF_POSITION_WHEN_WINDOW_TILTED: 0,
                }
            )
            == []
        )

    def test_equal_positions_need_no_warning(self):
        assert (
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: True,
                    CONF_WINDOW_ENTITY_ID: "binary_sensor.tuer",
                    CONF_WINDOW_TILTED_STATE: "none",
                    CONF_POSITION_WHEN_WINDOW_OPEN: 100,
                    CONF_POSITION_WHEN_WINDOW_TILTED: 100,
                }
            )
            == []
        )

    def test_a_shutter_without_a_window_contact_says_nothing(self):
        assert (
            _silent_setting_notes(
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_SUN_GEOMETRY_OVERRIDE: True,
                    CONF_POSITION_WHEN_WINDOW_OPEN: 100,
                    CONF_POSITION_WHEN_WINDOW_TILTED: 0,
                }
            )
            == []
        )


# --- Merker nach einem Neuladen ---------------------------------------------


@pytest.fixture
def entry(hass):
    """Ein Entry mit hingestelltem Laufzeit-Dict – kein echtes Setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [AREA],
            CONF_SHUTTERS: [
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_NAME: "Küche vorne",
                    CONF_AREA_UP_ID: "vorne",
                    CONF_AREA_DOWN_ID: "vorne",
                    CONF_LOCK_PROTECTION: True,
                }
            ],
        },
    )
    config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "sun_protect_covers": set(),
        "covers_driven_up": set(),
        "covers_driven_down": set(),
        "_runtime_started": dt_util.utcnow(),
    }
    return config_entry


class TestReloadIsNotAFinding:
    """Jedes Speichern im Panel laedt neu und leert die Merker.

    Wer danach exportiert – also fast jeder, der gerade etwas umgestellt hat –
    bekam eine Tabelle voller Striche und die Aufforderung, das zu melden.
    """

    async def test_a_fresh_runtime_says_so(self, hass, entry):
        md = (await async_build_export(hass, entry))["markdown"]
        assert "zuletzt geladen" in md
        assert "gerade neu geladen" in md
        assert "kein Befund" in md

    async def test_an_old_runtime_keeps_quiet(self, hass, entry):
        data = hass.data[DOMAIN][entry.entry_id]
        data["_runtime_started"] = dt_util.utcnow() - timedelta(hours=6)

        md = (await async_build_export(hass, entry))["markdown"]
        assert "vor 360 min" in md
        assert "gerade neu geladen" not in md

    async def test_without_the_timestamp_the_row_is_empty(self, hass, entry):
        """Bestandsinstallation, die den Schluessel noch nicht kennt."""
        hass.data[DOMAIN][entry.entry_id].pop("_runtime_started")

        md = (await async_build_export(hass, entry))["markdown"]
        assert "| zuletzt geladen | – |" in md
        assert "gerade neu geladen" not in md
