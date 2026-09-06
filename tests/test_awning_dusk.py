"""Dusk retract für Markisen – Anregung von bjoerg aus dem Forum.

Er wollte, dass eine Markise abends bei Dunkelheit einfährt, aber am
nächsten Tag **nicht** automatisch wieder ausfährt – schon gar nicht, wenn
niemand zuhause ist. Sein eigener Workaround (Helfer-Schalter unter
"Hochfahren unterbinden") griff nicht, weil `only_shutters()` Markisen von
genau diesem Fahrweg ausschließt.

Deshalb ein eigenes, unabhängiges Modul statt der Beschattung: die würde am
nächsten Tag automatisch wieder ausfahren, sobald die Bedingung erneut
zutrifft – exakt das, was nicht gewollt war. Dieses Modul fährt nur nach
innen; ausfahren bleibt Sache der Beschattung (falls eingeschaltet) oder von
Hand.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.awning_dusk import is_dusk_retracted
from custom_components.shutter_pilot.const import (
    AWNING_DUSK_SLOT,
    AWNING_GUARD_WIND,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ELEVATION_ENABLED,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTER_AUTOMATION_ENABLED,
    CONF_SHUTTERS,
    DOMAIN,
    KIND_AWNING,
    KIND_WINDOW,
    sun_condition_invert_key,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    awning_dusk_condition_met,
    is_cover_sun_protected,
)

AWNING = "cover.markise"
LUX = "sensor.aussenhelligkeit"
TEMP = "sensor.terrassentemperatur"

DUSK_ENTITY, DUSK_ON, DUSK_OFF, _DUSK_STATES = sun_condition_keys(AWNING_DUSK_SLOT)
COND_A_ENTITY, COND_A_ON, COND_A_OFF, _COND_A_STATES = sun_condition_keys("a")
WIND_ENTITY, WIND_ON, WIND_OFF, _WIND_STATES = sun_condition_keys(AWNING_GUARD_WIND)
WIND = "sensor.wind_dusk_test"


def _awning(**overrides) -> dict:
    awning = {
        CONF_COVER_ENTITY_ID: AWNING,
        CONF_NAME: "Markise Terrasse",
        CONF_DEVICE_KIND: KIND_AWNING,
        CONF_AREA_DOWN_ID: "terrasse",
        CONF_POSITION_OPEN: 0,
        CONF_POSITION_SUN_PROTECT: 100,
        DUSK_ENTITY: LUX,
        DUSK_ON: 50,
        DUSK_OFF: 100,
    }
    awning.update(overrides)
    return awning


def _area(**overrides) -> dict:
    area = {CONF_AREA_ID: "terrasse", CONF_AREA_NAME: "Terrasse"}
    area.update(overrides)
    return area


@pytest.fixture(autouse=True)
def _fast_startup_restore():
    with patch.object(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0), patch.object(
        cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0
    ):
        yield


@pytest.fixture
def cover_calls(hass):
    """Fahrten mitschreiben und die Position tatsächlich setzen.

    Ein reiner Mock ohne Zustandsänderung lässt der Startup-Restore für eine
    verschluckte Fahrt halten und wiederholt sie.
    """
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
    return [call.data["position"] for call in calls]


async def _setup(hass, areas=None, shutters=None, cover_position: int = 0):
    hass.states.async_set(
        AWNING, "open", {"current_position": cover_position, "supported_features": 15}
    )
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: areas if areas is not None else [_area()],
            CONF_SHUTTERS: shutters if shutters is not None else [_awning()],
        },
    )
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry, hass.data[DOMAIN][config_entry.entry_id]


async def _tick(hass, entry) -> None:
    """Einen Minutentakt auslösen, ohne auf die Uhr zu warten.

    `setup_awning_dusk` wertet einmal beim Aufruf sofort aus - erneutes
    Aufrufen ist der Minutentakt, nur ohne zu warten.
    """
    from custom_components.shutter_pilot.awning_dusk import setup_awning_dusk

    await setup_awning_dusk(hass, entry)
    await hass.async_block_till_done()


class TestConditionHelper:
    """awning_dusk_condition_met() direkt: fail closed wie jeder eigene Slot."""

    async def test_unconfigured_never_triggers(self, hass):
        assert awning_dusk_condition_met(hass, {}, {}) is False

    @pytest.mark.parametrize("state", ["unavailable", "unknown"])
    async def test_dead_sensor_does_not_trigger(self, hass, state):
        hass.states.async_set(LUX, state)
        assert awning_dusk_condition_met(hass, _awning(), {}) is False

    async def test_below_threshold_triggers_by_default(self, hass):
        """Kein Haken noetig: dusk ist von sich aus invertiert, "dunkler als"."""
        hass.states.async_set(LUX, "20")
        assert awning_dusk_condition_met(hass, _awning(), {}) is True

    async def test_above_threshold_does_not_trigger(self, hass):
        hass.states.async_set(LUX, "500")
        assert awning_dusk_condition_met(hass, _awning(), {}) is False

    async def test_a_boolean_helper_reads_naturally(self, hass):
        dusk_helper = "input_boolean.es_ist_dunkel"
        awning = _awning(**{DUSK_ENTITY: dusk_helper, DUSK_ON: None, DUSK_OFF: None})
        hass.states.async_set(dusk_helper, "on")
        assert awning_dusk_condition_met(hass, awning, {}) is True

    async def test_two_awnings_keep_separate_hysteresis(self, hass):
        """Der Speicher haengt am Cover, nicht an einer Bereichs-ID - sonst
        wuerden zwei Markisen ohne echte Bereichs-ID in denselben Topf
        fallen (_own_slot_met liest area.get(CONF_AREA_ID) roh)."""
        data: dict = {}
        other_lux = "sensor.andere_helligkeit"
        a = _awning()
        b = _awning(**{CONF_COVER_ENTITY_ID: "cover.markise_2", DUSK_ENTITY: other_lux})

        hass.states.async_set(LUX, "20")
        hass.states.async_set(other_lux, "500")
        assert awning_dusk_condition_met(hass, a, data) is True
        assert awning_dusk_condition_met(hass, b, data) is False


class TestDriveBehavior:
    """Fährt einmal ein, wenn dunkel; fährt nie von selbst wieder aus."""

    async def test_it_retracts_once_dark(self, hass, cover_calls):
        hass.states.async_set(LUX, "500")  # hell beim Start
        entry, data = await _setup(hass, cover_position=100)
        cover_calls.clear()

        hass.states.async_set(LUX, "20")  # wird dunkel
        await _tick(hass, entry)

        assert _positions(cover_calls) == [0]

    async def test_it_does_not_repeat_the_drive_every_minute(self, hass, cover_calls):
        hass.states.async_set(LUX, "20")
        entry, data = await _setup(hass, cover_position=100)
        cover_calls.clear()

        await _tick(hass, entry)
        await _tick(hass, entry)

        assert len(cover_calls) == 0, (
            "bereits eingefahren gehalten - kein erneuter Befehl noetig"
        )

    async def test_it_never_extends_again_once_bright(self, hass, cover_calls):
        """Der Kern des Wunsches: keine automatische Wiederausfahrt."""
        hass.states.async_set(LUX, "20")
        entry, data = await _setup(hass, cover_position=100)
        await _tick(hass, entry)
        cover_calls.clear()

        hass.states.async_set(LUX, "500")  # wieder hell
        await _tick(hass, entry)
        await _tick(hass, entry)

        assert len(cover_calls) == 0, "durfte nicht von selbst wieder ausfahren"

    async def test_a_second_dusk_can_fire_after_a_bright_spell(self, hass, cover_calls):
        hass.states.async_set(LUX, "20")
        entry, data = await _setup(hass, cover_position=100)
        await _tick(hass, entry)
        cover_calls.clear()

        hass.states.async_set(LUX, "500")
        await _tick(hass, entry)
        hass.states.async_set(LUX, "20")
        await _tick(hass, entry)

        assert _positions(cover_calls) == [0]

    async def test_the_shutter_automation_switch_blocks_it(self, hass, cover_calls):
        hass.states.async_set(LUX, "500")  # hell beim Start
        entry, data = await _setup(
            hass,
            shutters=[_awning(**{CONF_SHUTTER_AUTOMATION_ENABLED: False})],
            cover_position=100,
        )
        cover_calls.clear()

        hass.states.async_set(LUX, "20")  # wird dunkel
        await _tick(hass, entry)

        assert len(cover_calls) == 0

    async def test_the_area_automation_switch_blocks_it(self, hass, cover_calls):
        hass.states.async_set(LUX, "500")  # hell beim Start
        entry, data = await _setup(hass, cover_position=100)
        cover_calls.clear()
        data["auto_modes"]["terrasse"] = False

        hass.states.async_set(LUX, "20")  # wird dunkel
        await _tick(hass, entry)

        assert len(cover_calls) == 0

    async def test_a_regular_roof_window_with_the_same_slot_is_not_touched(
        self, hass, cover_calls
    ):
        """Bewusst nur Markisen - ein Dachfenster bei Dunkelheit zuzufahren
        haette einen ganz anderen Anlass (nicht gefragt)."""
        window = _awning(**{
            CONF_DEVICE_KIND: KIND_WINDOW, CONF_COVER_ENTITY_ID: "cover.dachfenster",
        })
        hass.states.async_set("cover.dachfenster", "open", {"current_position": 100, "supported_features": 15})
        hass.states.async_set(LUX, "500")  # hell beim Start
        entry, data = await _setup(hass, shutters=[window], cover_position=100)
        cover_calls.clear()

        hass.states.async_set(LUX, "20")  # wird dunkel
        await _tick(hass, entry)

        assert len(cover_calls) == 0

    async def test_no_area_at_all_still_gets_evaluated(self, hass, cover_calls):
        """Ein Wunsch, der auf Bereichsebene nicht existiert, darf keine
        Voraussetzung fuer eine per-Markise-Funktion sein."""
        hass.states.async_set(LUX, "500")  # hell beim Start
        entry, data = await _setup(
            hass, areas=[], shutters=[_awning(**{CONF_AREA_DOWN_ID: ""})], cover_position=100
        )
        cover_calls.clear()

        hass.states.async_set(LUX, "20")  # wird dunkel
        await _tick(hass, entry)

        assert _positions(cover_calls) == [0]

    async def test_an_inverted_boolean_can_say_so(self, hass, cover_calls):
        """Ein Helfer, dessen "aus" eigentlich "dunkel" heisst - dieselbe
        Invertier-Checkbox wie bei Wind/Regen/Frost (2.21.5)."""
        dusk_helper = "input_boolean.es_ist_hell"
        hass.states.async_set(dusk_helper, "on")  # hell beim Start
        entry, data = await _setup(
            hass,
            shutters=[_awning(**{
                DUSK_ENTITY: dusk_helper,
                DUSK_ON: None,
                DUSK_OFF: None,
                sun_condition_invert_key(AWNING_DUSK_SLOT): True,
            })],
            cover_position=100,
        )
        cover_calls.clear()

        hass.states.async_set(dusk_helper, "off")  # heisst hier: dunkel
        await _tick(hass, entry)

        assert _positions(cover_calls) == [0]


def _shaded_awning(**overrides) -> dict:
    """Markise mit eigener Beschattungsbedingung (Slot 'a') plus Dusk-Slot."""
    return _awning(**{
        COND_A_ENTITY: TEMP,
        COND_A_ON: 25,
        COND_A_OFF: 20,
        **overrides,
    })


async def _tick_named(hass, data, name: str) -> None:
    """Genau einen benannten Minutentakt-Callback direkt auslösen."""
    cb = data["_minute_callbacks"][name]
    cb(None)
    await hass.async_block_till_done()


class TestDuskRetractDoesNotDefeatShading:
    """Die alleinige Loesung "beim Einfahren forget_shading_for_cover()"
    waere unvollstaendig gewesen: ohne eine Sperre in elevation.py haette
    dieselbe (unabhaengige) Beschattungsbedingung die Markise eine Minute
    spaeter sofort wieder ausgefahren, besonders wenn die Elevationspruefung
    abgeschaltet ist und nichts anderes den Merker natuerlich aufraeumt.
    """

    async def _setup_shaded(self, hass, *, elevation_enabled: bool = True):
        hass.states.async_set(
            AWNING, "closed", {"current_position": 0, "supported_features": 15}
        )
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 5.0, "azimuth": 180.0}
        )
        hass.states.async_set(TEMP, "30")  # "heiss": bleibt so, Tag und Nacht
        hass.states.async_set(LUX, "500")  # hell beim Start

        area = _area(**{
            CONF_AREA_SUN_PROTECT_ENABLED: True,
            CONF_AREA_ELEVATION_ENABLED: elevation_enabled,
            CONF_AREA_ELEVATION_MIN: 1,
            CONF_AREA_ELEVATION_MAX: 10,
            CONF_AREA_AZIMUTH_ENABLED: False,
        })
        entry, data = await _setup(hass, areas=[area], shutters=[_shaded_awning()])
        return entry, data

    async def test_retracting_at_dusk_clears_the_stale_shading_flag(
        self, hass, cover_calls
    ):
        entry, data = await self._setup_shaded(hass)

        # Tagsueber, heiss: die Beschattung faehrt aus.
        await _tick_named(hass, data, "elevation")
        assert _positions(cover_calls) == [100]
        assert is_cover_sun_protected(data, AWNING) is True
        cover_calls.clear()

        # Daemmerung: es wird dunkel, die Dusk-Funktion faehrt ein.
        hass.states.async_set(LUX, "20")
        await _tick_named(hass, data, "awning_dusk")

        assert _positions(cover_calls) == [0]
        assert is_dusk_retracted(data, AWNING) is True
        assert is_cover_sun_protected(data, AWNING) is False, (
            "BUG waere: die Beschattung glaubt weiterhin, die Markise sei "
            "noch auf Beschattungshoehe draussen"
        )

    async def test_several_more_minute_ticks_do_not_re_extend_it(
        self, hass, cover_calls
    ):
        entry, data = await self._setup_shaded(hass)
        await _tick_named(hass, data, "elevation")
        hass.states.async_set(LUX, "20")
        await _tick_named(hass, data, "awning_dusk")
        cover_calls.clear()

        # Die Temperatur bleibt unveraendert "heiss" - eine kaputte Loesung
        # wuerde die Markise hier sofort wieder ausfahren.
        for _ in range(3):
            await _tick_named(hass, data, "elevation")

        assert _positions(cover_calls) == [], (
            "die Beschattung darf die eingefahrene Markise nicht anfassen, "
            "solange die Daemmerungsfunktion sie haelt"
        )
        assert hass.states.get(AWNING).attributes.get("current_position") == 0

    async def test_it_may_re_extend_once_it_gets_bright_again(
        self, hass, cover_calls
    ):
        entry, data = await self._setup_shaded(hass)
        await _tick_named(hass, data, "elevation")
        hass.states.async_set(LUX, "20")
        await _tick_named(hass, data, "awning_dusk")
        cover_calls.clear()

        # Es wird wieder hell: die Daemmerungsfunktion gibt den Eintrag frei.
        hass.states.async_set(LUX, "500")
        await _tick_named(hass, data, "awning_dusk")
        assert is_dusk_retracted(data, AWNING) is False

        # Die Beschattungsbedingung gilt unveraendert (immer noch heiss) -
        # jetzt darf die Beschattung wieder entscheiden.
        await _tick_named(hass, data, "elevation")

        assert _positions(cover_calls) == [100], (
            "nach Freigabe durch die Daemmerungsfunktion muss die "
            "Beschattung wieder ausfahren duerfen"
        )

    async def test_it_also_works_with_elevation_checking_disabled(
        self, hass, cover_calls
    ):
        """Genau der Fall, fuer den die alleinige forget_shading_for_cover()
        -Loesung nicht gereicht haette: ohne Elevationspruefung gibt es
        keinen natuerlichen Moment, an dem elevation.py das Beschattungsflag
        von sich aus raeumt."""
        entry, data = await self._setup_shaded(hass, elevation_enabled=False)

        await _tick_named(hass, data, "elevation")
        assert _positions(cover_calls) == [100]
        cover_calls.clear()

        hass.states.async_set(LUX, "20")
        await _tick_named(hass, data, "awning_dusk")
        assert _positions(cover_calls) == [0]
        assert is_cover_sun_protected(data, AWNING) is False
        cover_calls.clear()

        # Mehrere weitere Takte bei unveraendert "heiss" und unveraendert
        # dunkel: die Markise bleibt eingefahren.
        for _ in range(3):
            await _tick_named(hass, data, "elevation")
        assert _positions(cover_calls) == []
        assert hass.states.get(AWNING).attributes.get("current_position") == 0

        # Hell werden lassen: jetzt darf wieder ausgefahren werden.
        hass.states.async_set(LUX, "500")
        await _tick_named(hass, data, "awning_dusk")
        await _tick_named(hass, data, "elevation")
        assert _positions(cover_calls) == [100]

    async def test_an_active_guard_still_prevents_extension_after_dusk_releases(
        self, hass, cover_calls
    ):
        """Wetter- und Frostschutz behalten hoechste Prioritaet: selbst wenn
        die Daemmerungsfunktion die Markise wieder freigibt (hell geworden,
        `_dusk_retracted` geleert) und die Beschattungsbedingung weiter
        zutrifft, darf ein aktiver Wind-Guard das Ausfahren weiterhin
        verhindern - dieselbe Pruefung, die auch ohne Daemmerungsfunktion in
        `_drive_sun_protect()` sitzt."""
        area = _area(**{
            CONF_AREA_SUN_PROTECT_ENABLED: True,
            CONF_AREA_ELEVATION_ENABLED: True,
            CONF_AREA_ELEVATION_MIN: 1,
            CONF_AREA_ELEVATION_MAX: 10,
            CONF_AREA_AZIMUTH_ENABLED: False,
        })
        shutter = _shaded_awning(**{
            WIND_ENTITY: WIND,
            WIND_ON: 15,
            WIND_OFF: 10,
        })
        hass.states.async_set(WIND, "2")  # ruhig beim Start
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 5.0, "azimuth": 180.0}
        )
        entry, data = await _setup(hass, areas=[area], shutters=[shutter])

        # Tagsueber, heiss, ruhig: faehrt aus.
        await _tick_named(hass, data, "elevation")
        assert _positions(cover_calls) == [100]
        cover_calls.clear()

        # Daemmerung faehrt ein, dann wird es wieder hell - die
        # Daemmerungsfunktion gibt die Markise wieder frei.
        hass.states.async_set(LUX, "20")
        await _tick_named(hass, data, "awning_dusk")
        assert _positions(cover_calls) == [0]
        cover_calls.clear()

        hass.states.async_set(LUX, "500")
        await _tick_named(hass, data, "awning_dusk")
        assert is_dusk_retracted(data, AWNING) is False
        cover_calls.clear()

        # Jetzt zieht Wind auf, bevor die Beschattung wieder entscheiden kann.
        hass.states.async_set(WIND, "25")

        await _tick_named(hass, data, "elevation")

        assert 100 not in _positions(cover_calls), (
            "der Wind-Guard muss das Ausfahren verhindern, auch nachdem die "
            "Daemmerungsfunktion die Markise freigegeben hat"
        )
        assert hass.states.get(AWNING).attributes.get("current_position") == 0
