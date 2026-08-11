"""Beschattung nur innerhalb bestimmter Uhrzeiten.

Aus GitHub-Diskussion #5 (Fireblade900rr): das Kinderzimmer soll in den
Schulferien bis neun dunkel bleiben. Elevation, Azimut, Bedingungen und Saison
beschreiben alle *die Sonne* – dies hier beschreibt den Haushalt, und dafuer
gab es bisher nichts.

Beide Grenzen sind einzeln optional: „erst ab 09:00" ist fuer sich eine
gueltige Einstellung, und genau die war gefragt.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.util import dt as dt_util

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SHADE_FROM,
    CONF_AREA_SHADE_TO,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import (
    is_cover_sun_protected,
    resolve_shading_config,
    shading_time_window_ok,
)

COVER = "cover.kinderzimmer"


def _at(hh: int, mm: int = 0) -> datetime:
    """Ein Zeitpunkt in Ortszeit – die Funktion vergleicht die Wanduhr."""
    return dt_util.now().replace(hour=hh, minute=mm, second=0, microsecond=0)


# --- Die Fensterprüfung selbst ----------------------------------------------


class TestWindow:
    def test_without_any_bound_shading_runs_all_day(self):
        assert shading_time_window_ok({}, _at(6)) is True
        assert shading_time_window_ok({}, _at(23)) is True

    def test_a_lower_bound_alone_is_valid(self):
        """Genau der gefragte Fall: „erst ab 09:00", ohne obere Grenze."""
        cfg = {CONF_AREA_SHADE_FROM: "09:00"}

        assert shading_time_window_ok(cfg, _at(8, 59)) is False
        assert shading_time_window_ok(cfg, _at(9, 0)) is True
        assert shading_time_window_ok(cfg, _at(20)) is True

    def test_an_upper_bound_alone_is_valid(self):
        cfg = {CONF_AREA_SHADE_TO: "18:00"}

        assert shading_time_window_ok(cfg, _at(17, 59)) is True
        assert shading_time_window_ok(cfg, _at(18, 1)) is False

    def test_both_bounds_form_a_window(self):
        cfg = {CONF_AREA_SHADE_FROM: "09:00", CONF_AREA_SHADE_TO: "18:00"}

        assert shading_time_window_ok(cfg, _at(8)) is False
        assert shading_time_window_ok(cfg, _at(12)) is True
        assert shading_time_window_ok(cfg, _at(19)) is False

    def test_the_bounds_are_inclusive(self):
        cfg = {CONF_AREA_SHADE_FROM: "09:00", CONF_AREA_SHADE_TO: "18:00"}

        assert shading_time_window_ok(cfg, _at(9, 0)) is True
        assert shading_time_window_ok(cfg, _at(18, 0)) is True


class TestFailOpen:
    """Ein unbrauchbarer Wert darf die Beschattung nie blockieren.

    Von den drei moeglichen Ausgaengen ist „Zimmer heizt sich auf und nichts
    sagt warum" der schlechteste.
    """

    def test_empty_strings_are_no_window(self):
        assert shading_time_window_ok(
            {CONF_AREA_SHADE_FROM: "", CONF_AREA_SHADE_TO: "  "}, _at(3)
        ) is True

    def test_nonsense_does_not_block(self):
        assert shading_time_window_ok({CONF_AREA_SHADE_FROM: "neun"}, _at(3)) is True

    def test_a_window_across_midnight_is_refused_and_logged(self, caplog):
        """Kein Wrap wie bei Saison und Azimut – die Sonne scheint nachts nicht.

        `from > to` als Wrap zu lesen waere die Verwechslung von Spanne und
        Punktepaar, die 2.8.0 vier Bedingungen wirkungslos gemacht hat.
        """
        cfg = {CONF_AREA_SHADE_FROM: "18:00", CONF_AREA_SHADE_TO: "09:00"}

        assert shading_time_window_ok(cfg, _at(12)) is True
        assert "ends before it starts" in caplog.text


# --- Rückfall je Rollladen ---------------------------------------------------


class TestPerShutterOverride:
    """Gefragt war „single shutter" – ein Kinderzimmer, nicht der ganze Bereich."""

    def test_the_area_value_applies_without_an_override(self):
        area = {CONF_AREA_ID: "og", CONF_AREA_SHADE_FROM: "08:00"}
        geo = resolve_shading_config(area, {CONF_COVER_ENTITY_ID: COVER})

        assert geo[CONF_AREA_SHADE_FROM] == "08:00"

    def test_a_shutter_may_set_its_own(self):
        area = {CONF_AREA_ID: "og", CONF_AREA_SHADE_FROM: "08:00"}
        geo = resolve_shading_config(
            area, {CONF_COVER_ENTITY_ID: COVER, CONF_AREA_SHADE_FROM: "09:30"}
        )

        assert geo[CONF_AREA_SHADE_FROM] == "09:30"
        assert area[CONF_AREA_SHADE_FROM] == "08:00", "der Bereich bleibt unberuehrt"

    def test_it_does_not_need_the_geometry_tick(self):
        """Sonst erzwaenge ein Zeitfenster eine voellig unabhaengige Einstellung."""
        area = {CONF_AREA_ID: "og"}
        geo = resolve_shading_config(
            area, {CONF_COVER_ENTITY_ID: COVER, CONF_AREA_SHADE_FROM: "09:00"}
        )

        assert geo[CONF_AREA_SHADE_FROM] == "09:00"

    def test_an_empty_value_keeps_the_area_setting(self):
        area = {CONF_AREA_ID: "og", CONF_AREA_SHADE_FROM: "08:00"}
        geo = resolve_shading_config(
            area, {CONF_COVER_ENTITY_ID: COVER, CONF_AREA_SHADE_FROM: ""}
        )

        assert geo[CONF_AREA_SHADE_FROM] == "08:00"


# --- Gegen die echte Beschattung --------------------------------------------


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


async def _setup(hass, shutter_extra=None, area_extra=None):
    hass.states.async_set(
        COVER, "open", {"current_position": 100, "supported_features": 15}
    )
    hass.states.async_set(
        "sun.sun", "above_horizon", {"elevation": 42.0, "azimuth": 180.0}
    )
    area = {
        CONF_AREA_ID: "og",
        CONF_AREA_NAME: "Obergeschoss",
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_MIN: 0,
        CONF_AREA_ELEVATION_MAX: 90,
        CONF_AREA_AZIMUTH_ENABLED: False,
        **(area_extra or {}),
    }
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Kinderzimmer",
        CONF_AREA_UP_ID: "og",
        CONF_AREA_DOWN_ID: "og",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_SUN_PROTECT: 40,
        **(shutter_extra or {}),
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [area], CONF_SHUTTERS: [shutter]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


async def _ticks(hass, data, count: int = 2) -> None:
    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()


class TestAgainstTheRealShading:
    async def test_before_the_window_nothing_is_shaded(self, hass, cover_calls):
        """Alles andere spricht fuer Beschattung – nur die Uhr nicht."""
        _entry, data = await _setup(
            hass, shutter_extra={CONF_AREA_SHADE_FROM: "23:59"}
        )
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
        assert 40 not in [c.data["position"] for c in cover_calls]

    async def test_inside_the_window_it_shades_as_before(self, hass, cover_calls):
        _entry, data = await _setup(
            hass, shutter_extra={CONF_AREA_SHADE_FROM: "00:00"}
        )
        await _ticks(hass, data)

        assert is_cover_sun_protected(data, COVER)
        assert 40 in [c.data["position"] for c in cover_calls]

    async def test_leaving_the_window_releases_without_the_hold_time(
        self, hass, cover_calls
    ):
        """Eine Uhrzeitgrenze kommt nicht zurueck – anders als eine Wolke.

        Wuerde die Haltezeit hier gelten, bliebe das Zimmer bis zu zwei Stunden
        dunkel, und der Rollladen zaehlte solange als beschattet, was die
        Abendfahrt zusaetzlich blockiert.
        """
        _entry, data = await _setup(
            hass,
            shutter_extra={CONF_AREA_SHADE_FROM: "00:00"},
            area_extra={"shade_hold": 120},
        )
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)
        cover_calls.clear()

        # Fenster zu: ab jetzt liegt "jetzt" ausserhalb.
        entry_opts = dict(_entry.options)
        shutters = [dict(entry_opts[CONF_SHUTTERS][0])]
        shutters[0][CONF_AREA_SHADE_TO] = "00:01"
        hass.config_entries.async_update_entry(
            _entry, options={**entry_opts, CONF_SHUTTERS: shutters}
        )
        await hass.async_block_till_done()
        data = hass.data[DOMAIN][_entry.entry_id]
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
        assert 100 in [c.data["position"] for c in cover_calls], "sofort freigegeben"


# --- Im Export sichtbar ------------------------------------------------------


class TestExport:
    """Was entscheidet, muss im Bericht stehen – sonst sucht wieder jemand."""

    async def test_the_window_shows_up_when_set(self, hass):
        from custom_components.shutter_pilot.export import async_build_export

        entry, _data = await _setup(
            hass, shutter_extra={CONF_AREA_SHADE_FROM: "09:00"}
        )
        md = (await async_build_export(hass, entry))["markdown"]

        assert "- Uhrzeit" in md
        assert "09:00" in md

    async def test_without_a_window_the_line_stays_away(self, hass):
        """Sonst stuende an jedem Rollladen eine Zeile, die nichts beschreibt."""
        from custom_components.shutter_pilot.export import async_build_export

        entry, _data = await _setup(hass)
        md = (await async_build_export(hass, entry))["markdown"]

        assert "- Uhrzeit" not in md
