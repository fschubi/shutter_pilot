"""Die Automatik nach einem Eingriff von aussen wieder uebernehmen lassen.

pcsv17 im Forum: „Ich moechte tagsueber mein Baby hinlegen. Dafuer habe ich mir
einen Schalter gebaut, damit das Rollo auf circa 20 % runterfaehrt. Wenn ich
den Schalter deaktiviere, faehrt das Rollo wieder hoch. Danach macht die
Automatik aber leider nicht mehr weiter."

Erst nachgerechnet: die Beschattung fragt die manuelle Uebersteuerung
nirgends ab – daran liegt es also nicht. Der Grund steht in `elevation.py`:
solange der Merker „ist beschattet" steht, faehrt sie nur nach, wenn sich die
*Zielposition* aendert. Dass der Rollladen laengst woanders steht, weil ihn
jemand von aussen gefahren hat, sieht sie nicht.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)
from homeassistant.util import dt as dt_util

from custom_components.shutter_pilot.const import (
    CONF_AREA_ID,
    AREA_MODE_TIME,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
    KIND_AWNING,
    KIND_WINDOW,
    sun_condition_keys,
)
from custom_components.shutter_pilot.awning_guard import evaluate_guard, is_barred
from custom_components.shutter_pilot.helpers import is_cover_sun_protected

COVER = "cover.kinderzimmer"
SHADE_POS = 40


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


@pytest.fixture(autouse=True)
def _fast_startup(monkeypatch):
    """Der Startup-Restore wartet sonst fuenf Sekunden je Test."""
    from custom_components.shutter_pilot import cover_tracker

    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


def _in(minutes: int) -> str:
    """Uhrzeit in N Minuten, als HH:MM.

    Der Zeitplan entscheidet, in welcher Tageshaelfte ein Rollladen steht –
    also entscheidet die Wanduhr, was `scheduled_role_now()` antwortet. Feste
    07:00/19:00 machten den Test damit von der Startzeit abhaengig: zwischen
    19 und 7 Uhr faellt er. Die Zeiten liegen deshalb relativ zu jetzt.
    """
    moment = dt_util.now() + timedelta(minutes=minutes)
    return moment.strftime("%H:%M")


async def _setup(hass, position: int = 100):
    hass.states.async_set(
        COVER, "open", {"current_position": position, "supported_features": 15}
    )
    hass.states.async_set(
        "sun.sun", "above_horizon", {"elevation": 42.0, "azimuth": 180.0}
    )
    area = {
        CONF_AREA_ID: "og",
        CONF_AREA_NAME: "Obergeschoss",
        CONF_AREA_MODE: AREA_MODE_TIME,
        # Als Naechstes steht eine Abwaertsfahrt an: der Rollladen gehoert
        # bis dahin nach oben, zu jeder Tageszeit.
        CONF_AREA_TIME_DOWN: _in(60),
        CONF_AREA_TIME_UP: _in(120),
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_MIN: 0,
        CONF_AREA_ELEVATION_MAX: 90,
        CONF_AREA_AZIMUTH_ENABLED: False,
    }
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Kinderzimmer",
        CONF_AREA_UP_ID: "og",
        CONF_AREA_DOWN_ID: "og",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_SUN_PROTECT: SHADE_POS,
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


async def _drive_from_outside(hass, position: int) -> None:
    """Was pcsv17s eigener Schalter tut: den Cover von aussen verstellen."""
    hass.states.async_set(
        COVER, "open", {"current_position": position, "supported_features": 15}
    )
    await hass.async_block_till_done()


class TestTheCaseAsReported:
    async def test_shading_does_not_come_back_after_an_outside_drive(
        self, hass, cover_calls
    ):
        """Genau sein Ablauf, gegen die echte Beschattung gefahren."""
        _entry, data = await _setup(hass)
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER), "Ausgangslage: beschattet"
        assert SHADE_POS in [c.data["position"] for c in cover_calls]

        # Baby hingelegt: sein Schalter faehrt auf 20 %.
        await _drive_from_outside(hass, 20)
        cover_calls.clear()
        await _ticks(hass, data)
        assert not [c.data["position"] for c in cover_calls], (
            "waehrend das Baby schlaeft darf nichts zurueckfahren"
        )

        # Schalter aus: sein Schalter faehrt wieder hoch.
        await _drive_from_outside(hass, 100)
        cover_calls.clear()
        await _ticks(hass, data)

        # Hier steht der Rollladen offen in der Sonne, und der Merker sagt
        # weiterhin "beschattet" – deshalb faehrt nichts nach.
        assert is_cover_sun_protected(data, COVER)
        assert SHADE_POS not in [c.data["position"] for c in cover_calls], (
            "Ist-Zustand: die Beschattung holt ihn nicht zurueck"
        )


class TestTheService:
    """`shutter_pilot.resume_automation` – genau der Trigger, den er wollte."""

    async def test_it_brings_the_shading_back(self, hass, cover_calls):
        _entry, data = await _setup(hass)
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)

        await _drive_from_outside(hass, 20)   # Baby schlaeft
        await _ticks(hass, data)
        await _drive_from_outside(hass, 100)  # Schalter aus, Rollo hoch
        await _ticks(hass, data)
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "resume_automation", {"entity_id": COVER}, blocking=True
        )
        await hass.async_block_till_done()

        assert SHADE_POS in [c.data["position"] for c in cover_calls], (
            "die Automatik muss ihn zurueck auf Beschattungshoehe holen"
        )
        assert is_cover_sun_protected(data, COVER)

    async def test_without_shading_it_drives_the_half_of_the_day(
        self, hass, cover_calls
    ):
        """Keine Beschattung faellig: dann gilt offen bzw. zu."""
        _entry, data = await _setup(hass)
        # Sonne weg – die Beschattung hat nichts zu melden.
        hass.states.async_set(
            "sun.sun", "below_horizon", {"elevation": -20.0, "azimuth": 10.0}
        )
        await _ticks(hass, data)
        await _drive_from_outside(hass, 20)
        await _ticks(hass, data)
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "resume_automation", {"entity_id": COVER}, blocking=True
        )
        await hass.async_block_till_done()

        positions = [c.data["position"] for c in cover_calls]
        assert positions, "es muss etwas gefahren werden"
        assert 100 in positions, "er gilt als oben, also faehrt er auf offen"

    async def test_it_clears_the_manual_override_even_without_a_drive(
        self, hass, cover_calls
    ):
        """Die Uebersteuerung wird geloescht, nicht nebenbei ueberschrieben.

        Jede gelungene Fahrt schreibt die Quelle ohnehin auf `automation` –
        ein Test, der nur das Ergebnis prueft, faellt deshalb auch dann nicht
        um, wenn das Loeschen fehlt. Hier faehrt bewusst nichts: bleibt die
        Uebersteuerung stehen, ist das naechste automatische Hochfahren
        gesperrt, ohne dass es jemandem auffiele.
        """
        from custom_components.shutter_pilot.helpers import (
            get_position_store,
            SOURCE_MANUAL,
        )

        entry, data = await _setup(hass)
        await _ticks(hass, data)
        store = get_position_store(hass, entry.entry_id)
        await store.async_set_position(COVER, 20.0, SOURCE_MANUAL)
        assert store.get_record(COVER)["source"] == SOURCE_MANUAL

        async def _no_drive(*_a, **_kw):
            return True

        with patch(
            "custom_components.shutter_pilot.services.set_cover_position",
            new=_no_drive,
        ), patch.dict(data, {"_elevation_evaluate": None}):
            await hass.services.async_call(
                DOMAIN, "resume_automation", {"entity_id": COVER}, blocking=True
            )
            await hass.async_block_till_done()

        assert store.get_record(COVER)["source"] != SOURCE_MANUAL

    async def test_an_unknown_entity_matches_nothing(self, hass, cover_calls):
        _entry, data = await _setup(hass)
        await _ticks(hass, data)
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "resume_automation", {"entity_id": "cover.gibt_es_nicht"},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert not cover_calls

    async def test_without_arguments_it_covers_the_whole_house(
        self, hass, cover_calls
    ):
        _entry, data = await _setup(hass)
        await _ticks(hass, data)
        await _drive_from_outside(hass, 100)
        await _ticks(hass, data)
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "resume_automation", {}, blocking=True
        )
        await hass.async_block_till_done()
        assert SHADE_POS in [c.data["position"] for c in cover_calls]


class TestTheClosedShutterCase:
    """pcsv17, Rueckmeldung zu 2.21.0.

    „Wenn man das Rollo aber auf 0 % gefahren hat und die Beschattung gerade
    nicht greift, dann faehrt das Rollo beim Aktivieren der resume-Funktion
    nicht mehr nach oben. Das zweite Rollo, das nicht bei 0 % war, faehrt nach
    oben, genau wie es sein soll."

    Ursache: der Dienst fragte `covers_driven_down` – und da landet jeder
    Rollladen, den jemand zufaehrt. Damit las sich „von Hand geschlossen" als
    „die Automatik will ihn unten haben", und resume zementierte genau die
    Uebersteuerung, die es aufheben soll.
    """

    async def test_a_closed_shutter_comes_back_up_at_midday(
        self, hass, cover_calls
    ):
        _entry, data = await _setup(hass)
        # Sonne weg: die Beschattung hat nichts zu melden, es zaehlt allein
        # der Zeitplan – und der sagt tagsueber "oben" (07:00 bis 19:00).
        hass.states.async_set(
            "sun.sun", "below_horizon", {"elevation": -20.0, "azimuth": 10.0}
        )
        await _ticks(hass, data)

        await _drive_from_outside(hass, 0)   # von Hand ganz zu
        await _ticks(hass, data)
        # Der Fehlerzustand, hergestellt statt erhofft: genau dieser Merker
        # war es, den der Dienst frueher gelesen hat.
        data.setdefault("covers_driven_down", set()).add(COVER)
        cover_calls.clear()

        with patch(
            "custom_components.shutter_pilot.services.scheduled_role_now",
            return_value="open",
        ):
            await hass.services.async_call(
                DOMAIN, "resume_automation", {"entity_id": COVER}, blocking=True
            )
            await hass.async_block_till_done()

        assert 100 in [c.data["position"] for c in cover_calls], (
            "tagsueber muss er hochfahren, auch aus 0 %"
        )

    async def test_at_night_it_stays_closed(self, hass, cover_calls):
        """Die Gegenrichtung: nachts ist unten richtig."""
        _entry, data = await _setup(hass)
        hass.states.async_set(
            "sun.sun", "below_horizon", {"elevation": -20.0, "azimuth": 10.0}
        )
        await _ticks(hass, data)
        await _drive_from_outside(hass, 60)
        await _ticks(hass, data)
        cover_calls.clear()

        with patch(
            "custom_components.shutter_pilot.services.scheduled_role_now",
            return_value="closed",
        ):
            await hass.services.async_call(
                DOMAIN, "resume_automation", {"entity_id": COVER}, blocking=True
            )
            await hass.async_block_till_done()

        assert 0 in [c.data["position"] for c in cover_calls]

    async def test_without_a_schedule_nothing_is_invented(
        self, hass, cover_calls
    ):
        """Modus „ohne Zeitplan": es gibt keine Position zu raten."""
        _entry, data = await _setup(hass)
        hass.states.async_set(
            "sun.sun", "below_horizon", {"elevation": -20.0, "azimuth": 10.0}
        )
        await _ticks(hass, data)
        await _drive_from_outside(hass, 60)
        await _ticks(hass, data)
        cover_calls.clear()

        with patch(
            "custom_components.shutter_pilot.services.scheduled_role_now",
            return_value=None,
        ):
            await hass.services.async_call(
                DOMAIN, "resume_automation", {"entity_id": COVER}, blocking=True
            )
            await hass.async_block_till_done()

        assert not cover_calls, "ohne Zeitplan wird keine Endlage erfunden"


class TestScheduledRoleNow:
    """Die Ableitung selbst – ohne Setup, deshalb schnell."""

    def test_the_next_move_tells_which_half_we_are_in(self, hass):
        from custom_components.shutter_pilot.schedule_times import (
            scheduled_role_now,
        )
        from custom_components.shutter_pilot.const import (
            AREA_MODE_TIME,
            CONF_AREA_MODE,
            CONF_AREA_TIME_DOWN,
            CONF_AREA_TIME_UP,
        )

        area = {
            CONF_AREA_ID: "og",
            CONF_AREA_MODE: AREA_MODE_TIME,
            CONF_AREA_TIME_UP: "07:00",
            CONF_AREA_TIME_DOWN: "19:00",
        }
        midday = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
        night = dt_util.now().replace(hour=23, minute=0, second=0, microsecond=0)
        assert scheduled_role_now(hass, area, area, midday) == "open"
        assert scheduled_role_now(hass, area, area, night) == "closed"

    def test_an_area_without_a_schedule_has_no_answer(self, hass):
        from custom_components.shutter_pilot.schedule_times import (
            scheduled_role_now,
        )
        from custom_components.shutter_pilot.const import (
            AREA_MODE_NONE,
            CONF_AREA_MODE,
        )

        area = {CONF_AREA_ID: "x", CONF_AREA_MODE: AREA_MODE_NONE}
        assert scheduled_role_now(hass, area, area) is None
        assert scheduled_role_now(hass, None, None) is None


AWNING = "cover.markise_resume_test"
WINDOW = "cover.dachfenster_resume_test"
RAIN = "binary_sensor.regen_resume_test"


class TestGuardedKindsAreLeftAlone:
    """resume_automation ist laut README/services.yaml/CLAUDE.md nur fuer
    Rollladen gedacht - eine Markise oder ein Dachfenster durfte trotzdem
    hindurchrutschen und dabei den Wetterschutz umgehen (kein
    `shutters_only=True` bei filter_shutters_by_area, keine Guard-Pruefung
    vor der finalen Fahrt). Beide Luecken sind geschlossen: die Geraeteart
    wird schon beim Sammeln der Ziele ausgefiltert, eine zweite, defensive
    Guard-Pruefung sitzt zusaetzlich direkt vor der Fahrt.
    """

    async def _setup(self, hass):
        # Regen: alle geschuetzten Geraetearten (Markise, Dachfenster)
        # sperren sich global auf denselben Sensor.
        hass.states.async_set(RAIN, "on")
        hass.states.async_set(
            COVER, "open", {"current_position": 20, "supported_features": 15}
        )
        hass.states.async_set(
            AWNING, "open", {"current_position": 100, "supported_features": 15}
        )
        hass.states.async_set(
            WINDOW, "open", {"current_position": 100, "supported_features": 15}
        )
        hass.states.async_set(
            "sun.sun", "below_horizon", {"elevation": -20.0, "azimuth": 10.0}
        )
        area = {
            CONF_AREA_ID: "og",
            CONF_AREA_NAME: "Obergeschoss",
            CONF_AREA_MODE: AREA_MODE_TIME,
            CONF_AREA_TIME_DOWN: _in(60),
            CONF_AREA_TIME_UP: _in(120),
            CONF_AREA_DRIVE_DELAY: 0,
        }
        shutters = [
            {
                CONF_COVER_ENTITY_ID: COVER,
                CONF_NAME: "Kinderzimmer",
                CONF_AREA_UP_ID: "og",
                CONF_AREA_DOWN_ID: "og",
                CONF_POSITION_OPEN: 100,
                CONF_POSITION_CLOSED: 0,
            },
            {
                CONF_COVER_ENTITY_ID: AWNING,
                CONF_NAME: "Markise",
                CONF_DEVICE_KIND: KIND_AWNING,
                CONF_AREA_DOWN_ID: "og",
                CONF_POSITION_OPEN: 0,
                CONF_POSITION_SUN_PROTECT: 100,
            },
            {
                CONF_COVER_ENTITY_ID: WINDOW,
                CONF_NAME: "Dachfenster",
                CONF_DEVICE_KIND: KIND_WINDOW,
                CONF_AREA_DOWN_ID: "og",
                CONF_POSITION_OPEN: 100,
                CONF_POSITION_CLOSED: 0,
            },
        ]
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={
                CONF_AREAS: [area],
                CONF_SHUTTERS: shutters,
                sun_condition_keys("rain")[0]: RAIN,
            },
        )
        entry.add_to_hass(hass)
        with patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
        return entry, hass.data[DOMAIN][entry.entry_id]

    async def test_a_barred_awning_is_not_touched(self, hass, cover_calls):
        entry, data = await self._setup(hass)
        awning_cfg = entry.options[CONF_SHUTTERS][1]
        assert evaluate_guard(hass, entry, data, awning_cfg).get("barred") is True
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "resume_automation", {"entity_id": AWNING}, blocking=True
        )
        await hass.async_block_till_done()

        assert not [c for c in cover_calls if c.data["entity_id"] == AWNING], (
            "eine gesperrte Markise darf resume_automation nicht erreichen"
        )
        assert is_barred(data, AWNING) is True, "der Schutz bleibt unveraendert aktiv"

    async def test_a_barred_roof_window_is_not_touched(self, hass, cover_calls):
        entry, data = await self._setup(hass)
        window_cfg = entry.options[CONF_SHUTTERS][2]
        assert evaluate_guard(hass, entry, data, window_cfg).get("barred") is True
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "resume_automation", {"entity_id": WINDOW}, blocking=True
        )
        await hass.async_block_till_done()

        assert not [c for c in cover_calls if c.data["entity_id"] == WINDOW], (
            "ein gesperrtes Dachfenster darf resume_automation nicht erreichen"
        )
        assert is_barred(data, WINDOW) is True, "der Schutz bleibt unveraendert aktiv"

    async def test_a_regular_shutter_still_resumes_normally(self, hass, cover_calls):
        """Dieselbe Anfrage ohne entity_id (ganzes Haus): der Rollladen
        verhaelt sich unveraendert, waehrend Markise und Dachfenster
        aussen vor bleiben."""
        _entry, data = await self._setup(hass)
        cover_calls.clear()

        await hass.services.async_call(
            DOMAIN, "resume_automation", {}, blocking=True
        )
        await hass.async_block_till_done()

        driven = {c.data["entity_id"]: c.data["position"] for c in cover_calls}
        assert driven.get(COVER) == 100, (
            "der normale Rollladen gehoert tagsueber (naechste Aktion: runter) nach oben"
        )
        assert AWNING not in driven
        assert WINDOW not in driven
