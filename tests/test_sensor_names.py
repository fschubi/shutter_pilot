"""Die Vorhersagesensoren heissen jetzt in der Sprache der Oberfläche.

Vorher waren sie hart deutsch – auch für einen englischen Nutzer. Genau daran
ist im Forum jemand gescheitert, der nach „forecast" gesucht hat.

Der heikle Teil daran ist nicht die Übersetzung, sondern dass bestehende
Installationen ihre Entitäts-IDs behalten müssen: Wer sie in Automationen
verwendet, darf durch ein Update nicht auflaufen.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    CONF_AREAS,
    CONF_SHUTTERS,
    CONF_WEATHER_ENTITY,
    DOMAIN,
)

# So hiessen die Entitäten, als die Namen noch hart deutsch waren.
OLD_IDS = {
    "_forecast_temp_max": "sensor.shutter_pilot_vorhersage_hochsttemperatur",
    "_forecast_temp_min": "sensor.shutter_pilot_vorhersage_tiefsttemperatur",
    "_forecast_condition": "sensor.shutter_pilot_vorhersage_wetterlage",
}


async def _setup(hass) -> MockConfigEntry:
    hass.states.async_set("weather.dwd", "sunny", {})
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [],
            CONF_SHUTTERS: [],
            CONF_WEATHER_ENTITY: "weather.dwd",
        },
    )
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry


class TestExistingInstallations:
    async def test_entity_ids_are_kept(self, hass):
        """Eine bestehende Installation behält ihre Entitäts-IDs."""
        registry = er.async_get(hass)
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={
                CONF_AREAS: [],
                CONF_SHUTTERS: [],
                CONF_WEATHER_ENTITY: "weather.dwd",
            },
        )
        config_entry.add_to_hass(hass)

        # Die Entitäten so eintragen, wie eine ältere Version sie angelegt hat.
        for suffix, old_id in OLD_IDS.items():
            registry.async_get_or_create(
                "sensor",
                DOMAIN,
                f"{config_entry.entry_id}{suffix}",
                suggested_object_id=old_id.split(".", 1)[1],
                config_entry=config_entry,
            )

        hass.states.async_set("weather.dwd", "sunny", {})
        with patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()

        for suffix, old_id in OLD_IDS.items():
            found = registry.async_get_entity_id(
                "sensor", DOMAIN, f"{config_entry.entry_id}{suffix}"
            )
            assert found == old_id, f"{suffix}: {found} statt {old_id}"


class TestTranslatedNames:
    async def test_names_follow_the_translation(self, hass):
        """Kein hart kodierter Name mehr – der Schlüssel entscheidet."""
        await _setup(hass)
        names = {
            state.entity_id: state.attributes.get("friendly_name")
            for state in hass.states.async_all("sensor")
        }
        assert names, "die Vorhersagesensoren wurden angelegt"
        for entity_id, name in names.items():
            assert name, f"{entity_id} hat keinen Namen"
            assert "Shutter Pilot" in name, f"{entity_id}: {name}"

    async def test_all_three_forecast_sensors_exist(self, hass):
        config_entry = await _setup(hass)
        registry = er.async_get(hass)
        for suffix in OLD_IDS:
            assert registry.async_get_entity_id(
                "sensor", DOMAIN, f"{config_entry.entry_id}{suffix}"
            ), suffix

    async def test_no_sensors_without_a_weather_entity(self, hass):
        """Sonst stünden sie dauerhaft auf „unbekannt"."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={CONF_AREAS: [], CONF_SHUTTERS: []},
        )
        config_entry.add_to_hass(hass)
        with patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()

        registry = er.async_get(hass)
        for suffix in OLD_IDS:
            assert not registry.async_get_entity_id(
                "sensor", DOMAIN, f"{config_entry.entry_id}{suffix}"
            )


class TestTranslationFiles:
    """Ein fehlender Schlüssel macht die Entität namenlos – das faellt sonst
    erst in der laufenden Installation auf."""

    @pytest.mark.parametrize(
        "path",
        [
            "custom_components/shutter_pilot/strings.json",
            "custom_components/shutter_pilot/translations/de.json",
            "custom_components/shutter_pilot/translations/en.json",
        ],
    )
    def test_every_key_is_translated(self, path):
        import json
        import pathlib

        data = json.loads(pathlib.Path(path).read_text())
        sensors = data.get("entity", {}).get("sensor", {})
        for key in ("forecast_temp_max", "forecast_temp_min", "forecast_condition"):
            assert key in sensors, f"{path}: {key} fehlt"
            assert sensors[key].get("name"), f"{path}: {key} ohne Namen"
