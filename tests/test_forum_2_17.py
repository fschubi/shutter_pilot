"""Die vier Forumsmeldungen zu 2.16.0, jede mit ihrem eigenen Beweis.

Leichter Aufbau wie in `test_export_notes.py`: kein echtes Setup, sondern
Optionen am Entry und ein hingestelltes Laufzeit-Dict. Die Funktionen, um die
es hier geht, lesen genau das – `test_forum_findings.py` kostet dagegen rund
vierzehn Sekunden Fixture je Test.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.util import dt as dt_util

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_UP_ID,
    CONF_AREA_WE_NO_UP,
    CONF_AREA_WORKDAY_SENSOR,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_CLOSED_ALT,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_POSITION_SUN_PROTECT_ALT,
    CONF_POSITION_SUN_PROTECT_ENTITY,
    CONF_SHADING_ENABLED,
    CONF_SHUTTERS,
    DOMAIN,
    KIND_AWNING,
    ROLE_SUN_PROTECT,
    ROLE_SUN_PROTECT_ALT,
    sun_condition_keys,
)
from custom_components.shutter_pilot.export import async_build_export
from custom_components.shutter_pilot.helpers import (
    manual_position_is_a_close,
    note_manual_position,
    resolve_shade_position,
    shading_enabled,
    should_skip_automated_up,
)
from custom_components.shutter_pilot.position_store import (
    SOURCE_AUTOMATION,
    SOURCE_MANUAL,
    get_position_store,
)

COVER = "cover.horst_rolladen"

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_NAME: "Horst",
    CONF_AREA_UP_ID: "sued",
    CONF_AREA_DOWN_ID: "sued",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
    CONF_POSITION_SUN_PROTECT: 50,
}

AREA = {
    CONF_AREA_ID: "sued",
    CONF_AREA_NAME: "Süd",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_SUN_PROTECT_ENABLED: True,
}


@pytest.fixture
def entry(hass):
    """Entry mit hingestelltem Laufzeit-Dict, ohne echtes Setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [dict(AREA)], CONF_SHUTTERS: [dict(SHUTTER)]},
    )
    config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "sun_protect_covers": set(),
        "covers_driven_up": set(),
        "covers_driven_down": set(),
        "_runtime_started": dt_util.utcnow(),
    }
    return config_entry


async def _remember(hass, entry, position: float, source: str) -> None:
    store = get_position_store(hass, entry.entry_id)
    await store.async_set_position(COVER, position, source)


# --- Smons: „morgens faehrt nichts hoch" -------------------------------------


class TestManualCloseIsNoOverride:
    """Wer abends von Hand schliesst, bekam nie wieder ein automatisches Auf.

    Der Merker „manuell" setzt jede Fahrt, die nicht von Shutter Pilot kommt –
    die Dashboard-Knoepfe eingeschlossen, denn die rufen die cover-Dienste
    direkt auf. Geloescht wird er nur von einer *automatischen* Fahrt. Damit
    sperrte das Zufahren von Hand das Hochfahren fuer immer.
    """

    def test_the_closed_position_itself_is_not_an_override(self):
        assert manual_position_is_a_close(SHUTTER, 0.0) is True

    def test_further_than_closed_counts_as_closed(self):
        shutter = {**SHUTTER, CONF_POSITION_CLOSED: 10}
        assert manual_position_is_a_close(shutter, 0.0) is True

    def test_a_position_in_between_stays_an_override(self):
        assert manual_position_is_a_close(SHUTTER, 50.0) is False

    def test_the_alternative_closing_position_counts_too(self):
        shutter = {**SHUTTER, CONF_POSITION_CLOSED_ALT: 40}
        assert manual_position_is_a_close(shutter, 40.0) is True
        # Dazwischen bleibt es eine Handhoehe: 20 faehrt hier nichts an.
        assert manual_position_is_a_close(shutter, 22.0) is False

    def test_an_awning_is_judged_the_other_way_round(self):
        """Bei einer Markise ist „zu" die groessere Zahl."""
        awning = {
            CONF_COVER_ENTITY_ID: "cover.markise",
            CONF_DEVICE_KIND: KIND_AWNING,
            CONF_POSITION_OPEN: 0,
            CONF_POSITION_CLOSED: 0,
        }
        assert manual_position_is_a_close(awning, 0.0) is True
        assert manual_position_is_a_close(awning, 60.0) is False

    async def test_a_shutter_closed_by_hand_opens_the_next_morning(
        self, hass, entry
    ):
        hass.states.async_set(COVER, "closed", {"current_position": 0})
        await _remember(hass, entry, 0.0, SOURCE_MANUAL)
        data = hass.data[DOMAIN][entry.entry_id]

        assert (
            should_skip_automated_up(hass, entry, SHUTTER, data, set(), area=AREA)
            is False
        )

    async def test_a_shutter_parked_half_way_still_wins(self, hass, entry):
        hass.states.async_set(COVER, "open", {"current_position": 50})
        await _remember(hass, entry, 50.0, SOURCE_MANUAL)
        data = hass.data[DOMAIN][entry.entry_id]

        assert (
            should_skip_automated_up(hass, entry, SHUTTER, data, set(), area=AREA)
            is True
        )


# --- c.radi: „faehrt weder hoch noch runter" ---------------------------------


class TestManualDriveIsBooked:
    """Eine blockierte Richtung fror bisher die andere ein.

    `covers_driven_down` haelt einen Rollladen von der naechsten Abendfahrt ab
    und wird nur vom morgendlichen Hochfahren wieder geloescht. Laeuft das nie,
    faehrt auch abends nie wieder etwas – von Hand hochzuziehen half nicht, weil
    das niemand mitgeschrieben hat.
    """

    def test_opening_by_hand_clears_the_down_marker(self):
        data = {"covers_driven_up": set(), "covers_driven_down": {COVER}}
        note_manual_position(data, SHUTTER, 100.0)
        assert data["covers_driven_down"] == set()
        assert data["covers_driven_up"] == {COVER}

    def test_closing_by_hand_clears_the_up_marker(self):
        data = {"covers_driven_up": {COVER}, "covers_driven_down": set()}
        note_manual_position(data, SHUTTER, 0.0)
        assert data["covers_driven_up"] == set()
        assert data["covers_driven_down"] == {COVER}

    def test_a_position_in_between_says_nothing(self):
        data = {"covers_driven_up": set(), "covers_driven_down": {COVER}}
        note_manual_position(data, SHUTTER, 55.0)
        assert data["covers_driven_down"] == {COVER}
        assert data["covers_driven_up"] == set()

    def test_the_sets_are_mutated_in_place(self):
        """Neu zuweisen haenge den Scheduler an ein totes Set (2.10.0)."""
        up, down = set(), {COVER}
        data = {"covers_driven_up": up, "covers_driven_down": down}
        note_manual_position(data, SHUTTER, 100.0)
        assert data["covers_driven_up"] is up
        assert data["covers_driven_down"] is down


# --- pcsv17: zweite Beschattungsposition -------------------------------------


class TestSecondShadingPosition:
    SLOT_ENTITY = sun_condition_keys("sp_alt")[0]

    def test_without_a_condition_the_ordinary_position_applies(self, hass):
        shutter = {**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 25}
        pos, why = resolve_shade_position(hass, AREA, shutter, {})
        assert (pos, why) == (50.0, ROLE_SUN_PROTECT)

    def test_the_condition_switches_to_the_second_position(self, hass):
        hass.states.async_set("input_boolean.hitze", "on")
        area = {**AREA, self.SLOT_ENTITY: "input_boolean.hitze"}
        shutter = {**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 25}
        pos, why = resolve_shade_position(hass, area, shutter, {})
        assert (pos, why) == (25.0, ROLE_SUN_PROTECT_ALT)

    def test_without_a_second_position_the_condition_does_nothing(self, hass):
        hass.states.async_set("input_boolean.hitze", "on")
        area = {**AREA, self.SLOT_ENTITY: "input_boolean.hitze"}
        pos, why = resolve_shade_position(hass, area, SHUTTER, {})
        assert (pos, why) == (50.0, ROLE_SUN_PROTECT)

    def test_an_entity_wins_over_both_fixed_positions(self, hass):
        hass.states.async_set("input_boolean.hitze", "on")
        hass.states.async_set("input_number.beschattung", "33")
        area = {**AREA, self.SLOT_ENTITY: "input_boolean.hitze"}
        shutter = {
            **SHUTTER,
            CONF_POSITION_SUN_PROTECT_ALT: 25,
            CONF_POSITION_SUN_PROTECT_ENTITY: "input_number.beschattung",
        }
        pos, why = resolve_shade_position(hass, area, shutter, {})
        assert (pos, why) == (33.0, "entity")

    @pytest.mark.parametrize("value", ["unavailable", "keine Zahl", "140", "-5"])
    def test_an_unusable_value_falls_back_instead_of_stopping(self, hass, value):
        """Eine Beschattung, die wegen eines Templates aussetzt, waere schlimmer."""
        hass.states.async_set("input_number.beschattung", value)
        shutter = {
            **SHUTTER,
            CONF_POSITION_SUN_PROTECT_ENTITY: "input_number.beschattung",
        }
        pos, why = resolve_shade_position(hass, AREA, shutter, {})
        assert (pos, why) == (50.0, ROLE_SUN_PROTECT)


# --- Linos: einen Rollladen aus der Beschattung nehmen -----------------------


class TestShadingOptOut:
    def test_missing_means_it_takes_part(self):
        assert shading_enabled(SHUTTER) is True

    def test_unticked_takes_it_out(self):
        assert shading_enabled({**SHUTTER, CONF_SHADING_ENABLED: False}) is False


# --- Der Bericht muss die Antwort selbst geben -------------------------------


class TestDriveVerdictInExport:
    """„Warum faehrt er morgens nicht hoch" stand bisher nirgends im Bericht.

    Jede Sperre auf diesem Weg ist lautlos und laesst keinen Merker zurueck –
    zu sehen war nur, dass nichts gefahren ist. Das ist das Symptom.
    """

    async def test_a_free_path_says_so(self, hass, entry):
        hass.states.async_set(COVER, "open", {"current_position": 100})
        md = (await async_build_export(hass, entry))["markdown"]
        assert "Automatisches Hochfahren, Stand jetzt:" in md
        assert "Nichts hält das Öffnen auf" in md

    async def test_a_manual_position_is_named_with_its_value(self, hass, entry):
        hass.states.async_set(COVER, "open", {"current_position": 50})
        await _remember(hass, entry, 50.0, SOURCE_MANUAL)

        md = (await async_build_export(hass, entry))["markdown"]
        assert "von Hand gefahrene Position" in md
        assert "50 %" in md

    async def test_a_closed_shutter_is_no_finding(self, hass, entry):
        hass.states.async_set(COVER, "closed", {"current_position": 0})
        await _remember(hass, entry, 0.0, SOURCE_MANUAL)

        md = (await async_build_export(hass, entry))["markdown"]
        assert "von Hand gefahrene Position" not in md
        assert "Nichts hält das Öffnen auf" in md

    async def test_the_weekend_lock_is_named(self, hass, entry):
        hass.states.async_set(COVER, "open", {"current_position": 100})
        hass.states.async_set("binary_sensor.arbeitstag", "off")
        area = dict(entry.options[CONF_AREAS][0])
        area[CONF_AREA_WE_NO_UP] = True
        area[CONF_AREA_WORKDAY_SENSOR] = "binary_sensor.arbeitstag"
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_AREAS: [area]},
        )

        md = (await async_build_export(hass, entry))["markdown"]
        assert "Am Wochenende nicht hochfahren" in md

    async def test_an_automated_position_is_not_an_override(self, hass, entry):
        hass.states.async_set(COVER, "open", {"current_position": 50})
        await _remember(hass, entry, 50.0, SOURCE_AUTOMATION)

        md = (await async_build_export(hass, entry))["markdown"]
        assert "von Hand gefahrene Position" not in md

    async def test_the_second_position_is_reported_when_it_applies(
        self, hass, entry
    ):
        hass.states.async_set(COVER, "open", {"current_position": 100})
        hass.states.async_set("input_boolean.hitze", "on")
        area = {
            **entry.options[CONF_AREAS][0],
            sun_condition_keys("sp_alt")[0]: "input_boolean.hitze",
        }
        shutter = {**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 25}
        hass.config_entries.async_update_entry(
            entry, options={CONF_AREAS: [area], CONF_SHUTTERS: [shutter]}
        )

        md = (await async_build_export(hass, entry))["markdown"]
        assert "zweite Position" in md
        assert "**25 %**" in md

    async def test_a_second_position_without_its_condition_is_named(
        self, hass, entry
    ):
        """Gespeichert, sichtbar, wirkungslos – die bekannte Klasse."""
        hass.states.async_set(COVER, "open", {"current_position": 100})
        shutter = {**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 25}
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_SHUTTERS: [shutter]}
        )

        md = (await async_build_export(hass, entry))["markdown"]
        assert "keine Bedingung dafür" in md


# --- Dieselben Aenderungen am echten Fahrweg ---------------------------------


from unittest.mock import patch  # noqa: E402

from custom_components.shutter_pilot import cover_tracker  # noqa: E402
from custom_components.shutter_pilot.const import (  # noqa: E402
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_WINDOW_ENTITY_ID,
)
from custom_components.shutter_pilot.helpers import (  # noqa: E402
    is_cover_sun_protected,
)

DRIVE_AREA = {
    CONF_AREA_ID: "sued",
    CONF_AREA_NAME: "Süd",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
    CONF_AREA_SUN_PROTECT_ENABLED: True,
    CONF_AREA_ELEVATION_MIN: 0,
    CONF_AREA_ELEVATION_MAX: 90,
    CONF_AREA_AZIMUTH_ENABLED: False,
}


@pytest.fixture(autouse=True)
def _fast_startup_restore(monkeypatch):
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def cover_calls(hass):
    calls: list = []

    async def _handler(call):
        calls.append(call)
        position = call.data["position"]
        hass.states.async_set(
            call.data["entity_id"],
            "closed" if position <= 0 else "open",
            {"current_position": position, "supported_features": 15},
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return calls


async def _setup_drive(hass, options: dict, position: float = 100.0):
    hass.states.async_set(
        COVER, "open", {"current_position": position, "supported_features": 15}
    )
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 41.0,
            "azimuth": 198.0,
            "next_rising": "2026-08-29T04:00:00+00:00",
            "next_setting": "2026-08-28T19:00:00+00:00",
        },
    )
    config_entry = MockConfigEntry(
        domain=DOMAIN, title="Shutter Pilot", options=options
    )
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry, hass.data[DOMAIN][config_entry.entry_id]


async def _ticks(hass, data, count: int = 2) -> None:
    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()


def _positions(calls) -> list[int]:
    return [c.data["position"] for c in calls]


class TestShadingOptOutDrives:
    async def test_an_opted_out_shutter_is_never_shaded(self, hass, cover_calls):
        _entry, data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [DRIVE_AREA],
                CONF_SHUTTERS: [{**SHUTTER, CONF_SHADING_ENABLED: False}],
            },
        )
        await _ticks(hass, data)

        assert 50 not in _positions(cover_calls)
        assert not is_cover_sun_protected(data, COVER)

    async def test_without_the_tick_it_shades_as_before(self, hass, cover_calls):
        """Gegenprobe: derselbe Aufbau, nur der Haken fehlt."""
        _entry, data = await _setup_drive(
            hass, {CONF_AREAS: [DRIVE_AREA], CONF_SHUTTERS: [dict(SHUTTER)]}
        )
        await _ticks(hass, data)

        assert 50 in _positions(cover_calls)
        assert is_cover_sun_protected(data, COVER)

    async def test_unticking_releases_a_shutter_that_is_already_shaded(
        self, hass, cover_calls
    ):
        """Abwaehlen mitten am Nachmittag ist genau der Moment, in dem jemand
        diesen Rollladen wieder oben haben will – einfrieren waere falsch.

        Der Merker wird von Hand gesetzt: das Panel laedt beim Speichern neu,
        und danach stuende er ohnehin da, waehrend der Rollladen auf
        Beschattungshoehe steht. Genau diesen Zustand bildet der Test ab.
        """
        _entry, data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [DRIVE_AREA],
                CONF_SHUTTERS: [{**SHUTTER, CONF_SHADING_ENABLED: False}],
            },
            position=50.0,
        )
        data["sun_protect_covers"] = {COVER}
        cover_calls.clear()
        await _ticks(hass, data)

        assert 100 in _positions(cover_calls)
        assert not is_cover_sun_protected(data, COVER)


class TestSecondPositionDrives:
    async def test_the_second_position_is_the_one_that_gets_driven(
        self, hass, cover_calls
    ):
        hass.states.async_set("input_boolean.hitze", "on")
        area = {**DRIVE_AREA, sun_condition_keys("sp_alt")[0]: "input_boolean.hitze"}
        _entry, data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [area],
                CONF_SHUTTERS: [{**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 25}],
            },
        )
        await _ticks(hass, data)

        assert 25 in _positions(cover_calls)
        assert 50 not in _positions(cover_calls)

    async def test_switching_it_on_while_shaded_moves_the_shutter(
        self, hass, cover_calls
    ):
        """Binaer geschaltet heisst sofort, nicht bei der naechsten Freigabe."""
        hass.states.async_set("input_boolean.hitze", "off")
        area = {**DRIVE_AREA, sun_condition_keys("sp_alt")[0]: "input_boolean.hitze"}
        _entry, data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [area],
                CONF_SHUTTERS: [{**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 25}],
            },
        )
        await _ticks(hass, data)
        assert 50 in _positions(cover_calls)

        hass.states.async_set("input_boolean.hitze", "on")
        cover_calls.clear()
        await _ticks(hass, data)

        assert 25 in _positions(cover_calls)


class TestGroupServices:
    async def test_sun_protect_group_skips_an_opted_out_shutter(
        self, hass, cover_calls
    ):
        entry, _data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [{**DRIVE_AREA, CONF_AREA_SUN_PROTECT_ENABLED: False}],
                CONF_SHUTTERS: [{**SHUTTER, CONF_SHADING_ENABLED: False}],
            },
        )
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "sun_protect_group", {"area_id": "sued"}, blocking=True
        )
        await hass.async_block_till_done()

        assert _positions(cover_calls) == []

    async def test_ventilating_cannot_close_in_front_of_an_open_door(
        self, hass, cover_calls
    ):
        """Der Aussperrschutz galt an jedem Fahrweg – nur hier nicht."""
        hass.states.async_set("binary_sensor.tuer", "on")
        entry, _data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [{**DRIVE_AREA, CONF_AREA_SUN_PROTECT_ENABLED: False}],
                CONF_SHUTTERS: [
                    {
                        **SHUTTER,
                        CONF_WINDOW_ENTITY_ID: "binary_sensor.tuer",
                        CONF_LOCK_PROTECTION: True,
                        CONF_MIN_POSITION_WHEN_OPEN: 90,
                        CONF_POSITION_WHEN_WINDOW_TILTED: 30,
                    }
                ],
            },
        )
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "ventilate_group", {"area_id": "sued"}, blocking=True
        )
        await hass.async_block_till_done()

        assert _positions(cover_calls) == [90]


class TestManualDriveIsBookedInTheTracker:
    """Die Verdrahtung, nicht nur die Funktion.

    Der Merker ist nur dann etwas wert, wenn der Positions-Tracker ihn auch
    fuellt – und der ist die einzige Stelle, die eine fremde Fahrt ueberhaupt
    mitbekommt.
    """

    async def test_closing_the_cover_from_outside_books_it_as_down(
        self, hass, cover_calls
    ):
        _entry, data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [{**DRIVE_AREA, CONF_AREA_SUN_PROTECT_ENABLED: False}],
                CONF_SHUTTERS: [dict(SHUTTER)],
            },
        )
        data["covers_driven_up"].add(COVER)

        hass.states.async_set(
            COVER, "closed", {"current_position": 0, "supported_features": 15}
        )
        await hass.async_block_till_done()

        assert data["covers_driven_down"] == {COVER}
        assert data["covers_driven_up"] == set()

    async def test_opening_it_from_outside_frees_the_evening_drive(
        self, hass, cover_calls
    ):
        """Genau c.radis Fall: von Hand hochgezogen, abends faehrt wieder was."""
        _entry, data = await _setup_drive(
            hass,
            {
                CONF_AREAS: [{**DRIVE_AREA, CONF_AREA_SUN_PROTECT_ENABLED: False}],
                CONF_SHUTTERS: [dict(SHUTTER)],
            },
            position=0.0,
        )
        data["covers_driven_down"].add(COVER)

        hass.states.async_set(
            COVER, "open", {"current_position": 100, "supported_features": 15}
        )
        await hass.async_block_till_done()

        assert data["covers_driven_down"] == set()
        assert data["covers_driven_up"] == {COVER}


class TestTheReportDoesNotMoveWhatItMeasures:
    """Der Vertrag aus 2.8.0, jetzt eine Ebene hoeher.

    `_memory_copy()` schuetzt die Beschattungspruefung. Die neuen Aufrufe
    reichen aber `data` weiter, nicht den Merker – und `_own_slot_met()`
    schreibt die Hysterese beim Auswerten mit.
    """

    async def test_the_export_writes_no_hysteresis_state(self, hass, entry):
        hass.states.async_set(COVER, "open", {"current_position": 100})
        hass.states.async_set("sensor.hitze", "31")
        area = {
            **entry.options[CONF_AREAS][0],
            sun_condition_keys("sp_alt")[0]: "sensor.hitze",
            sun_condition_keys("sp_alt")[1]: 24,
            sun_condition_keys("no_up")[0]: "sensor.hitze",
            sun_condition_keys("no_up")[1]: 24,
        }
        shutter = {**SHUTTER, CONF_POSITION_SUN_PROTECT_ALT: 25}
        hass.config_entries.async_update_entry(
            entry, options={CONF_AREAS: [area], CONF_SHUTTERS: [shutter]}
        )
        data = hass.data[DOMAIN][entry.entry_id]
        data.pop("sun_cond_state", None)

        await async_build_export(hass, entry)

        assert data.get("sun_cond_state", {}) == {}
