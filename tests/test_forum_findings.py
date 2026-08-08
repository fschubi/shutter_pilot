"""Die fünf Funde aus der Forum-Runde vom 08.08.2026 – und der Export.

Zwei Meldungen (MartyBr, heinzie) liessen sich aus ihren Screenshots nicht
beantworten. Die Tests hier halten fest, was beim Nachprüfen des Codes
tatsächlich kaputt war, damit keiner der fünf Punkte zurückkommt.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    CONF_AREA_DOWN_ID,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ELEVATION_THRESHOLD,
    CONF_AREA_ID,
    CONF_AREA_SHADE_HOLD,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SUN_GEOMETRY_OVERRIDE,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import (
    _condition_slot_met,
    get_elevation_bounds,
    resolve_sun_geometry,
    set_cover_sun_protected,
    set_sun_protect_active,
    should_skip_full_open_preserving_sun_protect,
)


# --- F3: der Haken allein darf die Elevationsgrenzen nicht verschieben -------


class TestGeometryOverrideKeepsAreaBounds:
    """Ticken ohne eigene Werte kippte den Bereich auf die Vorgabe (1°–4°)."""

    def test_legacy_threshold_survives_a_bare_override(self):
        area = {CONF_AREA_ID: "wz", CONF_AREA_ELEVATION_THRESHOLD: 25.0}
        shutter = {CONF_COVER_ENTITY_ID: "cover.x", CONF_SUN_GEOMETRY_OVERRIDE: True}

        assert get_elevation_bounds(resolve_sun_geometry(area, shutter)) == (
            get_elevation_bounds(area)
        )

    def test_own_elevation_still_replaces_the_legacy_threshold(self):
        area = {CONF_AREA_ID: "wz", CONF_AREA_ELEVATION_THRESHOLD: 25.0}
        shutter = {
            CONF_COVER_ENTITY_ID: "cover.x",
            CONF_SUN_GEOMETRY_OVERRIDE: True,
            CONF_AREA_ELEVATION_MIN: 5.0,
            CONF_AREA_ELEVATION_MAX: 60.0,
        }

        assert get_elevation_bounds(resolve_sun_geometry(area, shutter)) == (5.0, 60.0)


# --- F2: „Aufheben unter" über „Beschatten ab" -------------------------------


class TestHysteresisTheWrongWayRound:
    """MartyBr trug beim Azimut 40 / 130 ein und meinte den Bereich 40°–130°."""

    def test_clamped_condition_warns_once(self, hass, caplog):
        hass.states.async_set("sensor.azimut", "96.8")
        cfg = {
            "sun_cond_b_entity": "sensor.azimut",
            "sun_cond_b_on_above": 40,
            "sun_cond_b_off_below": 130,
        }
        memory: dict = {}

        assert _condition_slot_met(hass, cfg, "b", memory) is True
        assert "wrong side" in caplog.text

        caplog.clear()
        assert _condition_slot_met(hass, cfg, "b", memory) is True
        assert "wrong side" not in caplog.text

    def test_sane_hysteresis_stays_quiet(self, hass, caplog):
        hass.states.async_set("sensor.lux", "32898")
        cfg = {
            "sun_cond_a_entity": "sensor.lux",
            "sun_cond_a_on_above": 30000,
            "sun_cond_a_off_below": 25000,
        }

        assert _condition_slot_met(hass, cfg, "a", {}) is True
        assert "wrong side" not in caplog.text


# --- F4: der Hoch-Blocker fragte den Bereich statt den Rollladen -------------


class TestOpenBlockerIsPerCover:
    """Ein beschattetes Fenster sperrte den ganzen Bereich."""

    def _shutter(self, cover: str) -> dict:
        return {
            CONF_COVER_ENTITY_ID: cover,
            CONF_AREA_DOWN_ID: "living",
            CONF_POSITION_OPEN: 100,
            CONF_POSITION_SUN_PROTECT: 40,
        }

    def _hass_at(self, hass, cover: str, position: int):
        hass.states.async_set(cover, "open", {"current_position": position})

    def test_shaded_cover_is_blocked(self, hass):
        data: dict = {}
        self._hass_at(hass, "cover.a", 40)
        set_cover_sun_protected(data, "cover.a", True)
        set_sun_protect_active(data, "living", True)

        assert should_skip_full_open_preserving_sun_protect(
            hass, self._shutter("cover.a"), data, {"living"}
        ) is True

    def test_neighbour_in_the_same_area_is_not(self, hass):
        """cover.b steht auf seiner Beschattungsposition, ist aber frei."""
        data: dict = {}
        self._hass_at(hass, "cover.b", 40)
        set_cover_sun_protected(data, "cover.a", True)
        set_sun_protect_active(data, "living", True)  # Bereichs-Summe: aktiv

        assert should_skip_full_open_preserving_sun_protect(
            hass, self._shutter("cover.b"), data, {"living"}
        ) is False


# --- F1 + F5: gegen den laufenden Kern ---------------------------------------


SUN_OPTIONS = {
    "areas": [
        {
            CONF_AREA_ID: "living",
            "name": "Wohnbereich",
            "mode": "time",
            "time_up": "07:00",
            "time_down": "19:00",
            "drive_delay": 0,
            CONF_AREA_SUN_PROTECT_ENABLED: True,
            CONF_AREA_ELEVATION_MIN: 2.0,
            CONF_AREA_ELEVATION_MAX: 70.0,
            CONF_AREA_SHADE_HOLD: 30,
            "sun_cond_a_entity": "sensor.lux",
            "sun_cond_a_on_above": 30000,
            "sun_cond_a_off_below": 25000,
        }
    ],
    "shutters": [
        {
            CONF_COVER_ENTITY_ID: "cover.living_room",
            "name": "Wohnzimmer",
            "area_up_id": "living",
            CONF_AREA_DOWN_ID: "living",
            CONF_POSITION_OPEN: 100,
            "position_closed": 0,
            CONF_POSITION_SUN_PROTECT: 40,
        }
    ],
}


@pytest.fixture
def drives(hass):
    """Aufgezeichnete Fahrbefehle – ohne echte Cover-Integration."""
    return async_mock_service(hass, "cover", "set_cover_position")


@pytest.fixture
async def sun_entry(hass, drives):
    """Ein Bereich mit Sonnenschutz, Haltezeit 30 min und einer Lux-Bedingung."""
    hass.states.async_set(
        "cover.living_room", "open", {"current_position": 100, "supported_features": 15}
    )
    hass.states.async_set("sensor.lux", "32898")
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 25.5,
            "azimuth": 96.8,
            "next_rising": "2025-07-08T05:00:00+00:00",
            "next_setting": "2025-07-07T21:00:00+00:00",
        },
    )
    config_entry = MockConfigEntry(
        domain=DOMAIN, title="Shutter Pilot", options=SUN_OPTIONS
    )
    config_entry.add_to_hass(hass)
    # Ohne echte Cover-Integration bleibt die Position stehen; der
    # Startup-Restore hält die Fahrt für verschluckt und wartet seine vollen
    # Wartezeiten ab. Das kostete 14 s Aufbau je Test in dieser Datei.
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ), patch.object(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0), patch.object(
        cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry


async def _tick(hass, entry):
    """Eine Runde der Sonnenschutz-Auswertung."""
    data = hass.data[DOMAIN][entry.entry_id]
    data["_minute_callbacks"]["elevation"](None)
    await hass.async_block_till_done()


class TestShadingFlagFollowsTheDrive:
    """F1: der Merker wurde gesetzt, bevor gefahren wurde."""

    async def test_shading_marked_after_a_good_drive(self, hass, sun_entry):
        data = hass.data[DOMAIN][sun_entry.entry_id]
        await _tick(hass, sun_entry)
        assert "cover.living_room" in data["sun_protect_covers"]

    async def test_failed_drive_is_retried_next_minute(self, hass, sun_entry):
        data = hass.data[DOMAIN][sun_entry.entry_id]
        # Der Aufbau hat schon einmal ausgewertet – zurück auf „nicht beschattet",
        # sonst gilt die Beschattung bereits als erledigt und nichts fährt.
        data["sun_protect_covers"] = set()

        with patch(
            "custom_components.shutter_pilot.elevation.set_cover_position",
            new_callable=AsyncMock,
            return_value=False,
        ) as failing:
            await _tick(hass, sun_entry)

        assert failing.await_count == 1
        assert "cover.living_room" not in data["sun_protect_covers"]

        # Zweiter Anlauf: die Beschattung wurde nicht als erledigt verbucht.
        with patch(
            "custom_components.shutter_pilot.elevation.set_cover_position",
            new_callable=AsyncMock,
            return_value=True,
        ) as retry:
            await _tick(hass, sun_entry)

        assert retry.await_count == 1
        assert "cover.living_room" in data["sun_protect_covers"]


class TestHoldTimeOnlyForClouds:
    """F5: die Haltezeit hielt auch das berechtigte Ende auf."""

    async def test_condition_dropping_out_waits(self, hass, sun_entry):
        data = hass.data[DOMAIN][sun_entry.entry_id]
        await _tick(hass, sun_entry)
        assert "cover.living_room" in data["sun_protect_covers"]

        # Wolke: Lux fällt unter „Aufheben unter".
        hass.states.async_set("sensor.lux", "12000")
        await _tick(hass, sun_entry)

        assert "cover.living_room" in data["sun_protect_covers"]
        assert "cover.living_room" in data["_shade_release_since"]

    async def test_sun_leaving_the_range_does_not_wait(self, hass, sun_entry):
        data = hass.data[DOMAIN][sun_entry.entry_id]
        await _tick(hass, sun_entry)
        assert "cover.living_room" in data["sun_protect_covers"]

        # Die Sonne steigt über den Bereich – das ist keine Wolke.
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 80.0, "azimuth": 180.0}
        )
        await _tick(hass, sun_entry)

        assert "cover.living_room" not in data["sun_protect_covers"]


# --- Export ------------------------------------------------------------------


class TestExport:
    async def test_report_carries_settings_values_and_verdict(self, hass, sun_entry):
        from custom_components.shutter_pilot.export import async_build_export

        report = await async_build_export(hass, sun_entry)
        md = report["markdown"]

        assert "cover.living_room" in md
        assert "sensor.lux" in md          # Bedingung samt Sensor
        assert "32898" in md               # und ihr Wert von jetzt
        assert "sun_cond_a_on_above" in md  # jede gespeicherte Einstellung
        assert "**Ergebnis: beschatten**" in md
        assert report["options"]["shutters"][0][CONF_COVER_ENTITY_ID] == (
            "cover.living_room"
        )

    async def test_export_does_not_move_the_hysteresis_memory(self, hass, sun_entry):
        """Eine Frage zu stellen darf die Antwort nicht verändern."""
        from copy import deepcopy

        from custom_components.shutter_pilot.export import async_build_export

        data = hass.data[DOMAIN][sun_entry.entry_id]
        await _tick(hass, sun_entry)
        before = deepcopy(data.get("sun_cond_state", {}))

        await async_build_export(hass, sun_entry)

        assert data.get("sun_cond_state", {}) == before

    async def test_warns_about_shading_settings_on_an_area_without_sun_protect(
        self, hass, sun_entry
    ):
        """Der stille Fall: eigene Bedingungen, Sonnenschutz im Bereich aus."""
        from custom_components.shutter_pilot.export import async_build_export

        options = deepcopy_options(SUN_OPTIONS)
        options["areas"][0][CONF_AREA_SUN_PROTECT_ENABLED] = False
        options["shutters"][0]["sun_cond_a_entity"] = "sensor.lux"
        hass.config_entries.async_update_entry(sun_entry, options=options)
        await hass.async_block_till_done()

        md = (await async_build_export(hass, sun_entry))["markdown"]
        assert "ist der Sonnenschutz **aus**" in md


def deepcopy_options(options: dict) -> dict:
    from copy import deepcopy

    return deepcopy(options)


# --- Nachtrag 08.08.2026, zweite Runde ---------------------------------------


class TestExportReadsTheWayTheReportWasMeant:
    """Was MartyBrs Export offenliess, obwohl alles darin stand."""

    async def test_unit_stands_next_to_the_value(self, hass, sun_entry):
        """Fünfstellige Lux-Schwellen an einem Sensor in W/m².

        Nebeneinander sehen 559,7 und 30000 nach „noch nicht hell genug" aus.
        Erst die Einheit sagt, dass dieser Sensor die Schwelle nie erreicht.
        """
        from custom_components.shutter_pilot.export import async_build_export

        hass.states.async_set("sensor.lux", "559.7", {"unit_of_measurement": "W/m²"})
        md = (await async_build_export(hass, sun_entry))["markdown"]

        assert "559.7 W/m²" in md

    async def test_clamped_release_threshold_is_named(self, hass, sun_entry):
        from custom_components.shutter_pilot.export import async_build_export

        options = deepcopy_options(SUN_OPTIONS)
        options["areas"][0]["sun_cond_a_on_above"] = 40
        options["areas"][0]["sun_cond_a_off_below"] = 130
        hass.config_entries.async_update_entry(sun_entry, options=options)
        await hass.async_block_till_done()

        md = (await async_build_export(hass, sun_entry))["markdown"]
        assert "wird verworfen" in md
        assert "≥ 40" in md

    async def test_sane_thresholds_get_no_note(self, hass, sun_entry):
        from custom_components.shutter_pilot.export import async_build_export

        md = (await async_build_export(hass, sun_entry))["markdown"]
        assert "wird verworfen" not in md

    async def test_dead_sensor_says_why_it_ticks(self, hass, sun_entry):
        """Ein ✅ hinter „unknown" liest sich wie eine bestandene Prüfung."""
        from custom_components.shutter_pilot.export import async_build_export

        hass.states.async_set("sensor.lux", "unknown")
        md = (await async_build_export(hass, sun_entry))["markdown"]

        assert "fail open" in md

    async def test_switched_off_automation_is_said_out_loud(self, hass, sun_entry):
        """„Ergebnis: beschatten" bei ausgeschalteter Automatik ist ein Versprechen."""
        from custom_components.shutter_pilot.export import async_build_export

        data = hass.data[DOMAIN][sun_entry.entry_id]
        data["auto_modes"] = {"living": False}

        md = (await async_build_export(hass, sun_entry))["markdown"]
        assert "steht auf **aus**" in md


class TestReleaseDropsTheWindowCycle:
    """Fenster auf unter Beschattung, Beschattung endet – nichts fährt zurück."""

    async def test_stale_restore_height_is_dropped(self, hass, sun_entry):
        data = hass.data[DOMAIN][sun_entry.entry_id]
        await _tick(hass, sun_entry)
        assert "cover.living_room" in data["sun_protect_covers"]

        # Der Fensterkontakt hat den beschatteten Rollladen hochgefahren und
        # sich 40 % als Rückfahrhöhe gemerkt.
        data["trigger_actions"]["cover.living_room"] = "triggered"
        data["trigger_heights"]["cover.living_room"] = 40

        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 80.0, "azimuth": 180.0}
        )
        await _tick(hass, sun_entry)

        assert "cover.living_room" not in data["sun_protect_covers"]
        assert "cover.living_room" not in data["trigger_actions"]
        assert "cover.living_room" not in data["trigger_heights"]
