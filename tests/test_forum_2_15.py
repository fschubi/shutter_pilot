"""Die Meldungen aus dem Forum vom August, gegen den echten Code gehalten.

Vier Wuensche und vier Fehler, alle aus demselben Fenster von zwei Wochen:

* bjoerg: die Beschattung wurde bei sinkender Sonne nie aufgeloest, der
  Rollladen stand bis zum Abendplan auf halber Hoehe.
* bjoerg und charly166: die Markisenschutz-Einstellungen standen nach dem
  Speichern wieder leer im Formular.
* bjoerg: der Sperrzeit-Hinweis stand bei Wind, Regen und Frost gleich da.
* Im Export war die Zeile "Fensterrichtung" die Geometriepruefung *insgesamt*,
  also Hoehe und Richtung – und widersprach damit dem Wert in derselben
  Klammer.
* Linos, c.radi, hollsten: am Wochenende gar nicht hochfahren.
* Linos: eine Bedingungs-Entitaet, die das morgendliche Oeffnen blockiert.
* charly166 und Linos: nicht beschatten, was noch gar nicht offen ist.
* MartyBr: die Beschattung je Bereich abschaltbar, ohne die Automatik.
* Thsu: ein zweiter Fensterkontakt fuer Doppelfluegelfenster.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SHADE_ONLY_WHEN_OPEN,
    CONF_AREA_SHADE_RELEASE_OPENS,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREA_WE_NO_UP,
    CONF_AREA_WORKDAY_SENSOR,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_ENTITY_ID_2,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
    NO_UP_CONDITION_SLOT,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    automated_up_blocked,
    is_cover_sun_protected,
    is_sun_protect_enabled,
    no_up_condition_blocks,
    weekend_blocks_up,
)
from custom_components.shutter_pilot.window_helper import (
    get_window_state,
    is_window_open_or_tilted,
)

COVER = "cover.kinderzimmer"
NO_UP_ENTITY = sun_condition_keys(NO_UP_CONDITION_SLOT)[0]


# --- Die Fensterkontakte: reine Funktion, kein Setup noetig ------------------


class TestSecondWindowContact:
    """Thsu: Doppelfluegelfenster, ein Kontakt je Fluegel."""

    @staticmethod
    def _shutter(**extra):
        return {
            CONF_COVER_ENTITY_ID: COVER,
            CONF_WINDOW_ENTITY_ID: "binary_sensor.fluegel_a",
            CONF_WINDOW_ENTITY_ID_2: "binary_sensor.fluegel_b",
            CONF_WINDOW_OPEN_STATE: "on",
            **extra,
        }

    async def test_either_leaf_open_makes_the_window_open(self, hass):
        hass.states.async_set("binary_sensor.fluegel_a", "off")
        hass.states.async_set("binary_sensor.fluegel_b", "on")

        assert get_window_state(hass, self._shutter()) == "open"
        assert is_window_open_or_tilted(hass, self._shutter())

    async def test_both_closed_is_closed(self, hass):
        hass.states.async_set("binary_sensor.fluegel_a", "off")
        hass.states.async_set("binary_sensor.fluegel_b", "off")

        assert get_window_state(hass, self._shutter()) == "closed"

    async def test_open_beats_tilted(self, hass):
        """Ein Fluegel gekippt, der andere ganz auf – das Fenster ist auf."""
        hass.states.async_set("binary_sensor.fluegel_a", "tilted")
        hass.states.async_set("binary_sensor.fluegel_b", "on")

        state = get_window_state(
            hass, self._shutter(**{CONF_WINDOW_TILTED_STATE: "tilted"})
        )
        assert state == "open"

    async def test_one_leaf_tilted_alone_is_tilted(self, hass):
        hass.states.async_set("binary_sensor.fluegel_a", "tilted")
        hass.states.async_set("binary_sensor.fluegel_b", "off")

        state = get_window_state(
            hass, self._shutter(**{CONF_WINDOW_TILTED_STATE: "tilted"})
        )
        assert state == "tilted"

    async def test_without_a_second_contact_nothing_changes(self, hass):
        hass.states.async_set("binary_sensor.fluegel_a", "on")
        shutter = {
            CONF_COVER_ENTITY_ID: COVER,
            CONF_WINDOW_ENTITY_ID: "binary_sensor.fluegel_a",
            CONF_WINDOW_OPEN_STATE: "on",
        }

        assert get_window_state(hass, shutter) == "open"

    async def test_a_missing_second_contact_does_not_report_open(self, hass):
        """Eine Entitaet, die es nicht gibt, gilt als geschlossen – nicht als offen."""
        hass.states.async_set("binary_sensor.fluegel_a", "off")

        assert get_window_state(hass, self._shutter()) == "closed"


# --- Die beiden Hochfahr-Sperren: reine Funktionen ---------------------------


class TestNoUpCondition:
    """Linos: eine Bedingung, die das morgendliche Oeffnen blockiert."""

    @staticmethod
    def _area(**extra):
        return {CONF_AREA_ID: "og", **extra}

    async def test_unset_never_blocks(self, hass):
        assert no_up_condition_blocks(hass, self._area(), {}) is False

    async def test_a_helper_that_is_on_blocks(self, hass):
        hass.states.async_set("input_boolean.ferien", "on")
        area = self._area(**{NO_UP_ENTITY: "input_boolean.ferien"})

        assert no_up_condition_blocks(hass, area, {}) is True

    async def test_a_helper_that_is_off_does_not_block(self, hass):
        hass.states.async_set("input_boolean.ferien", "off")
        area = self._area(**{NO_UP_ENTITY: "input_boolean.ferien"})

        assert no_up_condition_blocks(hass, area, {}) is False

    async def test_an_unreadable_sensor_does_not_block(self, hass):
        """Die eine Richtung, in der ein Fehler nicht wehtun darf.

        Andersherum bliebe jeder Rollladen unten, bis es jemand merkt – und
        aus dem Zimmer heraus kommt man daran nicht vorbei.
        """
        hass.states.async_set("input_boolean.ferien", "unavailable")
        area = self._area(**{NO_UP_ENTITY: "input_boolean.ferien"})

        assert no_up_condition_blocks(hass, area, {}) is False


class TestWeekendBlocksUp:
    """c.radi, Linos, hollsten: am Wochenende gar nicht hochfahren."""

    SATURDAY = datetime(2026, 8, 22, 8, 0)
    MONDAY = datetime(2026, 8, 24, 8, 0)

    async def test_off_by_default(self, hass):
        assert weekend_blocks_up(hass, {CONF_AREA_ID: "og"}, self.SATURDAY) is False

    async def test_blocks_on_saturday_and_sunday(self, hass):
        area = {CONF_AREA_ID: "og", CONF_AREA_WE_NO_UP: True}

        assert weekend_blocks_up(hass, area, self.SATURDAY) is True
        assert weekend_blocks_up(hass, area, self.MONDAY) is False

    async def test_the_workday_sensor_wins(self, hass):
        """hollstens Fall: samstags arbeiten, sonntags ausschlafen.

        Der Sondertage-Sensor entscheidet vor dem Kalender – ein
        Workday-Sensor mit `excludes: [sun]` macht Sonnabend zum Arbeitstag.
        """
        hass.states.async_set("binary_sensor.workday", "on")
        area = {
            CONF_AREA_ID: "og",
            CONF_AREA_WE_NO_UP: True,
            CONF_AREA_WORKDAY_SENSOR: "binary_sensor.workday",
        }

        assert weekend_blocks_up(hass, area, self.SATURDAY) is False

        hass.states.async_set("binary_sensor.workday", "off")
        assert weekend_blocks_up(hass, area, self.SATURDAY) is True

    async def test_both_gates_report_through_one_call(self, hass):
        hass.states.async_set("input_boolean.ferien", "on")
        area = {CONF_AREA_ID: "og", NO_UP_ENTITY: "input_boolean.ferien"}

        assert automated_up_blocked(hass, area, {}, self.MONDAY) == "condition"
        assert automated_up_blocked(hass, {CONF_AREA_ID: "og"}, {}, self.MONDAY) is None


# --- Gegen den echten Aufbau ------------------------------------------------


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


async def _setup(hass, area_extra=None, shutter_extra=None, position=100, elevation=42.0):
    hass.states.async_set(
        COVER, "open", {"current_position": position, "supported_features": 15}
    )
    hass.states.async_set(
        "sun.sun", "above_horizon", {"elevation": elevation, "azimuth": 180.0}
    )
    area = {
        CONF_AREA_ID: "og",
        CONF_AREA_NAME: "Obergeschoss",
        CONF_AREA_MODE: AREA_MODE_TIME,
        CONF_AREA_TIME_UP: "07:00",
        CONF_AREA_TIME_DOWN: "19:00",
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_MIN: 10,
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


def _rearm_scheduler(data) -> None:
    """Die Tagesmerker des Schedulers loeschen.

    Beim Aufbau gilt jede heute schon vergangene Uhrzeit als erledigt – sonst
    holte ein Reload um 23 Uhr den ganzen Tag nach. Im Test ist genau das der
    Grund, warum sonst nie etwas faehrt.
    """
    data.get("_scheduler_fired", {}).clear()


async def _ticks(hass, data, count: int = 2) -> None:
    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()


class TestShadeOnlyWhenOpen:
    """charly166 und Linos: nicht beschatten, was noch gar nicht offen ist."""

    async def test_a_closed_shutter_is_opened_without_the_option(
        self, hass, cover_calls
    ):
        """Das bisherige Verhalten – und genau das, was gemeldet wurde."""
        _entry, data = await _setup(hass, position=0)
        await _ticks(hass, data)

        assert 40 in [c.data["position"] for c in cover_calls]

    async def test_with_the_option_it_stays_down(self, hass, cover_calls):
        _entry, data = await _setup(
            hass,
            area_extra={CONF_AREA_SHADE_ONLY_WHEN_OPEN: True},
            position=0,
        )
        await _ticks(hass, data)

        assert 40 not in [c.data["position"] for c in cover_calls]
        assert not is_cover_sun_protected(data, COVER)

    async def test_an_open_shutter_is_still_shaded(self, hass, cover_calls):
        _entry, data = await _setup(
            hass,
            area_extra={CONF_AREA_SHADE_ONLY_WHEN_OPEN: True},
            position=100,
        )
        await _ticks(hass, data)

        assert 40 in [c.data["position"] for c in cover_calls]
        assert is_cover_sun_protected(data, COVER)


class TestShadeReleaseOpens:
    """bjoerg: die Beschattung wurde bei sinkender Sonne nie aufgeloest."""

    async def test_without_the_option_it_stays_put(self, hass, cover_calls):
        """Das alte Verhalten: Merker faellt, gefahren wird nicht."""
        _entry, data = await _setup(hass, elevation=42.0)
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)

        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 2.0, "azimuth": 180.0}
        )
        cover_calls.clear()
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
        assert 100 not in [c.data["position"] for c in cover_calls]

    async def test_with_the_option_it_opens(self, hass, cover_calls):
        _entry, data = await _setup(
            hass,
            area_extra={CONF_AREA_SHADE_RELEASE_OPENS: True},
            elevation=42.0,
        )
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)

        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 2.0, "azimuth": 180.0}
        )
        cover_calls.clear()
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
        assert 100 in [c.data["position"] for c in cover_calls]


class TestSunProtectSwitch:
    """MartyBr: die Beschattung je Bereich abschalten, ohne die Automatik."""

    async def test_the_switch_exists_only_where_shading_is_configured(self, hass):
        await _setup(hass)
        assert hass.states.get("switch.shutter_pilot_sonnenschutz_obergeschoss")

    async def test_no_switch_without_shading(self, hass):
        await _setup(hass, area_extra={CONF_AREA_SUN_PROTECT_ENABLED: False})
        assert hass.states.get("switch.shutter_pilot_sonnenschutz_obergeschoss") is None

    async def test_switching_off_releases_what_is_shaded(self, hass, cover_calls):
        """Der Punkt der ganzen Uebung: die Rollladen kommen wieder hoch.

        Stehenlassen waere die schlechtere Haelfte – wer abschaltet, weil es
        kuehl wird, will nicht bis zum Abend auf halber Hoehe sitzen.
        """
        entry, data = await _setup(hass)
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)

        data.setdefault("sun_protect_modes", {})["og"] = False
        cover_calls.clear()
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
        assert 100 in [c.data["position"] for c in cover_calls]

    async def test_switched_off_it_does_not_start_shading(self, hass, cover_calls):
        # Mit tiefer Sonne starten, damit beim Aufbau noch nichts beschattet
        # ist – sonst pruefte der Test die Freigabe statt den Nichtbeginn.
        _entry, data = await _setup(hass, elevation=2.0)
        data.setdefault("sun_protect_modes", {})["og"] = False
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 42.0, "azimuth": 180.0}
        )
        cover_calls.clear()
        await _ticks(hass, data)

        assert 40 not in [c.data["position"] for c in cover_calls]
        assert not is_cover_sun_protected(data, COVER)

    async def test_the_area_automation_switch_is_untouched(self, hass):
        """Die zwei Schalter sind getrennt – das war der ganze Wunsch."""
        entry, data = await _setup(hass)
        area = entry.options[CONF_AREAS][0]

        data.setdefault("sun_protect_modes", {})["og"] = False
        assert is_sun_protect_enabled(hass, entry, area) is False
        assert data.get("auto_modes", {}).get("og") is not False


class TestUpIsBlocked:
    """Die Sperre wirkt im Scheduler – und nur nach oben."""

    async def test_the_condition_keeps_the_shutter_down(self, hass, cover_calls):
        hass.states.async_set("input_boolean.ferien", "on")
        _entry, data = await _setup(
            hass,
            area_extra={
                CONF_AREA_SUN_PROTECT_ENABLED: False,
                NO_UP_ENTITY: "input_boolean.ferien",
                CONF_AREA_TIME_UP: "00:01",
            },
            position=0,
        )
        _rearm_scheduler(data)
        await _ticks(hass, data)

        assert 100 not in [c.data["position"] for c in cover_calls]

    async def test_without_the_condition_it_drives(self, hass, cover_calls):
        _entry, data = await _setup(
            hass,
            area_extra={
                CONF_AREA_SUN_PROTECT_ENABLED: False,
                CONF_AREA_TIME_UP: "00:01",
            },
            position=0,
        )
        _rearm_scheduler(data)
        await _ticks(hass, data)

        assert 100 in [c.data["position"] for c in cover_calls]

    async def test_closing_still_runs_under_the_block(self, hass, cover_calls):
        """Sonst stuende das Haus unter der Ferien-Kennung den Abend offen."""
        hass.states.async_set("input_boolean.ferien", "on")
        _entry, data = await _setup(
            hass,
            area_extra={
                CONF_AREA_SUN_PROTECT_ENABLED: False,
                NO_UP_ENTITY: "input_boolean.ferien",
                CONF_AREA_TIME_UP: "00:01",
                CONF_AREA_TIME_DOWN: "00:02",
            },
            position=100,
        )
        _rearm_scheduler(data)
        await _ticks(hass, data)

        assert 0 in [c.data["position"] for c in cover_calls]


class TestShadingWaitsForTheWindow:
    """hollizone: bei offenem Dachfenster soll die Beschattung warten.

    Kein neuer Code – „Nachholen nach dem Schließen" deckt das seit 2.6.0 ab,
    und die Beschattung ist einer der Fahrwege, die es benutzen. Hier steht
    es als Test, weil die Antwort im Forum sonst eine Behauptung wäre.
    """

    WINDOW = "binary_sensor.dachfenster"

    async def _setup_with_window(self, hass, window_state):
        hass.states.async_set(self.WINDOW, window_state)
        return await _setup(
            hass,
            shutter_extra={
                CONF_WINDOW_ENTITY_ID: self.WINDOW,
                CONF_WINDOW_OPEN_STATE: "on",
                "drive_after_close": True,
            },
        )

    async def test_an_open_window_holds_the_shading_back(self, hass, cover_calls):
        _entry, data = await self._setup_with_window(hass, "on")
        await _ticks(hass, data)

        assert 40 not in [c.data["position"] for c in cover_calls]
        assert COVER in data.get("drive_after_close_pending", {})

    async def test_closing_the_window_runs_it(self, hass, cover_calls):
        _entry, data = await self._setup_with_window(hass, "on")
        await _ticks(hass, data)
        cover_calls.clear()

        hass.states.async_set(self.WINDOW, "off")
        await hass.async_block_till_done()

        assert 40 in [c.data["position"] for c in cover_calls]

    async def test_a_closed_window_shades_immediately(self, hass, cover_calls):
        _entry, data = await self._setup_with_window(hass, "off")
        await _ticks(hass, data)

        assert 40 in [c.data["position"] for c in cover_calls]
