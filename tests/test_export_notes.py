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


# --- Markisen im Bericht -----------------------------------------------------


class TestAwningReport:
    """Die haeufigste Frage an einer Markise ist „warum ist sie nicht draussen".

    Die Antwort steht oefter im Schutz als in der Geometrie – deshalb kommt der
    Block davor, und deshalb muessen Wert, Einheit und Freigabezeit drinstehen.
    """

    @pytest.fixture
    def awning_entry(self, hass):
        from custom_components.shutter_pilot.const import (
            AWNING_GUARD_WIND,
            CONF_DEVICE_KIND,
            CONF_POSITION_OPEN,
            CONF_POSITION_SUN_PROTECT,
            KIND_AWNING,
            awning_lockout_key,
            sun_condition_keys,
        )

        keys = sun_condition_keys(AWNING_GUARD_WIND)
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={
                CONF_AREAS: [AREA],
                CONF_SHUTTERS: [
                    {
                        CONF_COVER_ENTITY_ID: "cover.markise",
                        CONF_NAME: "Markise Terrasse",
                        CONF_DEVICE_KIND: KIND_AWNING,
                        CONF_AREA_DOWN_ID: "vorne",
                        CONF_POSITION_OPEN: 0,
                        CONF_POSITION_SUN_PROTECT: 100,
                    }
                ],
                keys[0]: "sensor.wind",
                keys[1]: 30,
                keys[2]: 15,
                awning_lockout_key(AWNING_GUARD_WIND): 20,
            },
        )
        config_entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
            "sun_protect_covers": set(),
            "covers_driven_up": set(),
            "covers_driven_down": set(),
            "_runtime_started": dt_util.utcnow() - timedelta(hours=6),
        }
        return config_entry

    async def test_it_is_called_a_markise_not_a_rollladen(self, hass, awning_entry):
        md = (await async_build_export(hass, awning_entry))["markdown"]
        assert "### Markise `cover.markise`" in md

    async def test_the_two_positions_are_named_by_their_meaning(
        self, hass, awning_entry
    ):
        md = (await async_build_export(hass, awning_entry))["markdown"]
        assert "Ruhestellung (eingefahren): 0 %" in md
        assert "Beschattung (ausgefahren): 100 %" in md

    async def test_the_guard_table_carries_value_and_unit(self, hass, awning_entry):
        """559,7 neben 30000 erklaert nichts, 559,7 W/m² neben 30000 alles."""
        hass.states.async_set(
            "sensor.wind", "34.1", {"unit_of_measurement": "km/h"}
        )

        md = (await async_build_export(hass, awning_entry))["markdown"]

        assert "34.1 km/h" in md
        assert "einfahren ab 30" in md

    async def test_a_barred_awning_says_why_and_until_when(
        self, hass, awning_entry
    ):
        from custom_components.shutter_pilot.awning_guard import evaluate_guard

        hass.states.async_set("sensor.wind", "41", {"unit_of_measurement": "km/h"})
        data = hass.data[DOMAIN][awning_entry.entry_id]
        shutter = awning_entry.options[CONF_SHUTTERS][0]
        evaluate_guard(hass, awning_entry, data, shutter)
        hass.states.async_set("sensor.wind", "4", {"unit_of_measurement": "km/h"})
        evaluate_guard(hass, awning_entry, data, shutter)

        md = (await async_build_export(hass, awning_entry))["markdown"]

        assert "**Ergebnis: gesperrt**" in md
        assert "Freigabe frühestens in" in md

    async def test_the_metres_per_second_trap_is_named(self, hass, awning_entry):
        """Faktor 3,6 daneben heisst: die Markise faehrt nie ein."""
        hass.states.async_set("sensor.wind", "6.2", {"unit_of_measurement": "m/s"})

        md = (await async_build_export(hass, awning_entry))["markdown"]

        assert "misst in **m/s**" in md
        assert "7 m/s" in md

    async def test_a_matching_unit_gets_no_warning(self, hass, awning_entry):
        hass.states.async_set("sensor.wind", "12", {"unit_of_measurement": "km/h"})

        md = (await async_build_export(hass, awning_entry))["markdown"]

        assert "misst in" not in md

    async def test_leftover_shutter_keys_are_named(self, hass, awning_entry):
        from custom_components.shutter_pilot.export import _awning_silent_notes

        notes = "\n".join(
            _awning_silent_notes(
                {
                    CONF_COVER_ENTITY_ID: "cover.markise",
                    CONF_LOCK_PROTECTION: True,
                    CONF_WINDOW_ENTITY_ID: "binary_sensor.tuer",
                }
            )
        )

        assert "lock_protection" in notes
        assert "window_entity_id" in notes

    async def test_a_clean_awning_gets_no_note(self, hass):
        from custom_components.shutter_pilot.export import _awning_silent_notes

        assert _awning_silent_notes({CONF_COVER_ENTITY_ID: "cover.markise"}) == []

    async def test_the_report_does_not_create_guard_state(self, hass, awning_entry):
        """Wie beim Hysterese-Speicher: der Bericht darf nichts verschieben."""
        hass.states.async_set("sensor.wind", "41", {"unit_of_measurement": "km/h"})

        await async_build_export(hass, awning_entry)

        assert "_awning_guard" not in hass.data[DOMAIN][awning_entry.entry_id]


# --- Helfer als Bedingung im Bericht -----------------------------------------


class TestHelperConditionInTheReport:
    """Ein an/aus-Helfer hat keine Schwellen – und das muss dastehen.

    Sonst zeigt die Spalte „ab – / auf unter –" und liest sich wie eine
    vergessene Einstellung; genau die Sorte Fehldeutung, gegen die der Export
    seit 2.8.0 gebaut ist.
    """

    async def test_an_on_off_helper_shows_no_thresholds(self, hass, entry):
        hass.states.async_set("input_boolean.reinigungsdienst", "on")
        area = dict(AREA)
        area["sun_cond_a_entity"] = "input_boolean.reinigungsdienst"
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_AREAS: [area]},
        )

        md = (await async_build_export(hass, entry))["markdown"]
        assert "an = erfüllt" in md
        assert "ab – / auf unter –" not in md

    async def test_a_numeric_sensor_still_shows_its_thresholds(self, hass, entry):
        hass.states.async_set("sensor.lux", "45000")
        area = dict(AREA)
        area["sun_cond_a_entity"] = "sensor.lux"
        area["sun_cond_a_on_above"] = 30000
        area["sun_cond_a_off_below"] = 20000
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_AREAS: [area]},
        )

        md = (await async_build_export(hass, entry))["markdown"]
        assert "ab 30000 / auf unter 20000" in md
        assert "an = erfüllt" not in md
