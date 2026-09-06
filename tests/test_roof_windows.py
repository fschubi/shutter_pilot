"""Dachfenster – die dritte Geraeteart.

hollizone im Forum: „Was ich mir noch wuenschen wuerde ist eine Regensteuerung
fuer die Dachfenster. Gerne ueber eine externe Wetterstation." Gebaut nicht als
zweites Datenmodell, sondern als dritter `device_kind` – dieselbe Ueberlegung
wie bei den Markisen in 2.12.0.

Die Maschine dahinter ist unveraendert: `guard_slot_danger()` kennt Binaersensor,
Zahlenschwelle mit Hysterese und Zustandsliste, dazu Sperrzeit und Karenz. Neu
ist genau eines – die sichere Stellung. Eine Markise ist sicher, wenn sie *drin*
ist, ein Dachfenster, wenn es *zu* ist.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.awning_guard import (
    clamp_to_rest,
    evaluate_guard,
    extends_upward,
    rest_position,
)
from custom_components.shutter_pilot.const import (
    CONF_AREA_DOWN_ID,
    CONF_AREA_UP_ID,
    CONF_AREA_ID,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
    KIND_AWNING,
    KIND_WINDOW,
    ROLE_CLOSED,
    ROLE_OPEN,
    ROLE_SUN_PROTECT,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    filter_shutters_by_area,
    get_position_for_role,
    rest_role,
    has_guard,
    is_awning,
    is_shutter,
    is_window,
    only_awnings,
    only_guarded,
    only_shutters,
    only_windows,
)

RAIN = "binary_sensor.ecowitt_rain_state"
WINDOW = {
    CONF_COVER_ENTITY_ID: "cover.dachfenster_bad",
    CONF_DEVICE_KIND: KIND_WINDOW,
    CONF_AREA_DOWN_ID: "bad",
    CONF_POSITION_CLOSED: 0,
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_SUN_PROTECT: 30,
}
AWNING = {
    CONF_COVER_ENTITY_ID: "cover.markise",
    CONF_DEVICE_KIND: KIND_AWNING,
    CONF_AREA_DOWN_ID: "bad",
    CONF_POSITION_OPEN: 0,
    CONF_POSITION_SUN_PROTECT: 100,
}
SHUTTER = {
    CONF_COVER_ENTITY_ID: "cover.rollladen",
    CONF_AREA_DOWN_ID: "bad",
    CONF_AREA_UP_ID: "bad",
}


@pytest.fixture
def entry(hass):
    e = MockConfigEntry(
        domain=DOMAIN,
        options={
            sun_condition_keys("rain")[0]: RAIN,
            "guard_rain_lockout": 10,
        },
    )
    e.add_to_hass(hass)
    return e


# --- Die Geraeteart wird positiv gefragt ------------------------------------


class TestKinds:
    def test_the_three_kinds_are_told_apart(self):
        assert (is_shutter(SHUTTER), is_awning(SHUTTER), is_window(SHUTTER)) == (True, False, False)
        assert (is_shutter(AWNING), is_awning(AWNING), is_window(AWNING)) == (False, True, False)
        assert (is_shutter(WINDOW), is_awning(WINDOW), is_window(WINDOW)) == (False, False, True)

    def test_a_missing_key_is_still_a_shutter(self):
        """Bestandsdaten tragen keinen `device_kind` – keine Migration."""
        assert is_shutter({}) is True

    def test_the_protection_covers_both_new_kinds(self):
        assert has_guard(SHUTTER) is False
        assert has_guard(AWNING) is True
        assert has_guard(WINDOW) is True

    def test_the_schedule_filter_keeps_only_shutters(self):
        """Der eigentliche Fund: `not is_awning` haette das Fenster mitgenommen."""
        allof = [SHUTTER, AWNING, WINDOW]
        assert only_shutters(allof) == [SHUTTER]
        assert only_awnings(allof) == [AWNING]
        assert only_windows(allof) == [WINDOW]
        assert only_guarded(allof) == [AWNING, WINDOW]

    def test_the_area_filter_leaves_windows_out_of_the_schedule(self):
        picked = filter_shutters_by_area(
            [SHUTTER, AWNING, WINDOW], "bad", use_up=False, shutters_only=True
        )
        assert [s[CONF_COVER_ENTITY_ID] for s in picked] == [SHUTTER[CONF_COVER_ENTITY_ID]]

    def test_the_group_services_keep_them(self):
        """„Zu" an einem Dachfenster heisst schliessen – ein Knopfdruck."""
        picked = filter_shutters_by_area([SHUTTER, AWNING, WINDOW], "bad", use_up=False)
        assert len(picked) == 3


# --- Die sichere Stellung ---------------------------------------------------


class TestSafePosition:
    def test_the_rest_role_differs_by_kind(self):
        assert rest_role(AWNING) == ROLE_OPEN
        assert rest_role(WINDOW) == ROLE_CLOSED

    def test_rest_position_is_shut_for_a_window(self):
        assert rest_position(WINDOW) == 0
        assert rest_position(AWNING) == 0  # eingefahren, dieselbe Zahl anderer Sinn

    def test_the_clamp_points_the_right_way(self):
        """Gesperrt heisst: nicht weiter auf als die sichere Stellung."""
        assert extends_upward(WINDOW) is True
        assert clamp_to_rest(WINDOW, 30) == 0
        assert clamp_to_rest(WINDOW, 100) == 0
        assert clamp_to_rest(WINDOW, 0) == 0

    def test_window_roles_fall_back_sensibly(self):
        bare = {CONF_DEVICE_KIND: KIND_WINDOW}
        assert get_position_for_role(bare, ROLE_CLOSED) == 0
        assert get_position_for_role(bare, ROLE_OPEN) == 100
        assert get_position_for_role(bare, ROLE_SUN_PROTECT) == 30


# --- Der Regenschutz --------------------------------------------------------


class TestRainProtection:
    async def test_rain_shuts_it_and_the_lockout_holds(self, hass, entry):
        data = {}
        hass.states.async_set(RAIN, "off")
        state = evaluate_guard(hass, entry, data, WINDOW, now=0.0)
        assert state["retract"] is False and state["barred"] is False

        hass.states.async_set(RAIN, "on")
        state = evaluate_guard(hass, entry, data, WINDOW, now=10.0)
        assert state["retract"] is True
        assert "rain" in state["reasons"]

        # Regen vorbei – die Sperrzeit haelt das Fenster noch zu.
        hass.states.async_set(RAIN, "off")
        state = evaluate_guard(hass, entry, data, WINDOW, now=20.0)
        assert state["barred"] is True
        assert state["retract"] is False

        state = evaluate_guard(hass, entry, data, WINDOW, now=20.0 + 601)
        assert state["barred"] is False, "nach der Sperrzeit darf es wieder auf"

    async def test_a_dead_sensor_bars_at_once_and_shuts_after_the_grace(
        self, hass, entry
    ):
        """Kein Wert = Gefahr. Am Fenster ist das die richtige Richtung."""
        data = {}
        hass.states.async_set(RAIN, "unavailable")
        state = evaluate_guard(hass, entry, data, WINDOW, now=0.0)
        assert state["barred"] is True
        # Zufahren erst nach der Karenz, sonst zieht ein Neustart alles zu.
        assert state["retract"] is False
        state = evaluate_guard(hass, entry, data, WINDOW, now=3600.0)
        assert state["retract"] is True

    async def test_a_numeric_rain_rate_works_the_same(self, hass, entry):
        """Ecowitt liefert mm/h – Zahl mit Hysterese statt an/aus."""
        rate = "sensor.ecowitt_rain_rate"
        e = MockConfigEntry(
            domain=DOMAIN,
            options={
                sun_condition_keys("rain")[0]: rate,
                sun_condition_keys("rain")[1]: 0.2,
                sun_condition_keys("rain")[2]: 0.1,
                "guard_rain_lockout": 0,
            },
        )
        e.add_to_hass(hass)
        data = {}
        hass.states.async_set(rate, "0.0")
        assert evaluate_guard(hass, e, data, WINDOW, now=0.0)["retract"] is False
        hass.states.async_set(rate, "0.4")
        assert evaluate_guard(hass, e, data, WINDOW, now=1.0)["retract"] is True
        # Hysterese: zwischen den Schwellen bleibt es zu.
        hass.states.async_set(rate, "0.15")
        assert evaluate_guard(hass, e, data, WINDOW, now=2.0)["retract"] is True
        hass.states.async_set(rate, "0.05")
        assert evaluate_guard(hass, e, data, WINDOW, now=3.0)["retract"] is False


# --- Die Verdrahtung, nicht nur die Funktion --------------------------------


class TestTheGuardLoopActuallyReachesWindows:
    """Die Gegenprobe, die zuerst nicht fiel.

    `evaluate_guard()` allein zu pruefen genuegt nicht: die Schleife in
    `async_enforce_guard()` ist die einzige Stelle, die entscheidet, *welche*
    Eintraege der Schutz ueberhaupt ansieht. Genau derselbe blinde Fleck wie
    bei `note_manual_position` in 2.17.0 – dort blieben 648 Tests gruen,
    waehrend die Verdrahtung fehlte.
    """

    async def test_rain_drives_the_window_shut(self, hass):
        from unittest.mock import patch

        from custom_components.shutter_pilot.awning_guard import async_enforce_guard
        from custom_components.shutter_pilot.const import CONF_SHUTTERS

        entry = MockConfigEntry(
            domain=DOMAIN,
            options={
                CONF_SHUTTERS: [WINDOW, AWNING, SHUTTER],
                sun_condition_keys("rain")[0]: RAIN,
                "guard_rain_lockout": 10,
            },
        )
        entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"shutters": []}
        hass.states.async_set(RAIN, "on")

        driven: list[tuple[str, float]] = []

        async def _fake_drive(_hass, _entry, entity_id, position, reason, **kw):
            driven.append((entity_id, position))
            return True

        with patch(
            "custom_components.shutter_pilot.awning_guard.set_cover_position",
            new=_fake_drive,
        ):
            await async_enforce_guard(hass, entry)

        by_cover = dict(driven)
        assert WINDOW[CONF_COVER_ENTITY_ID] in by_cover, (
            "der Schutz hat das Dachfenster gar nicht angesehen"
        )
        assert by_cover[WINDOW[CONF_COVER_ENTITY_ID]] == 0, "es muss zufahren"
        assert by_cover[AWNING[CONF_COVER_ENTITY_ID]] == 0, "die Markise faehrt ein"
        assert SHUTTER[CONF_COVER_ENTITY_ID] not in by_cover, (
            "ein Rollladen hat mit dem Schutz nichts zu tun"
        )

    async def test_a_window_without_danger_is_left_alone(self, hass):
        from unittest.mock import patch

        from custom_components.shutter_pilot.awning_guard import async_enforce_guard
        from custom_components.shutter_pilot.const import CONF_SHUTTERS

        entry = MockConfigEntry(
            domain=DOMAIN,
            options={
                CONF_SHUTTERS: [WINDOW],
                sun_condition_keys("rain")[0]: RAIN,
                "guard_rain_lockout": 10,
            },
        )
        entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"shutters": []}
        hass.states.async_set(RAIN, "off")

        driven: list[str] = []

        async def _fake_drive(_hass, _entry, entity_id, position, reason, **kw):
            driven.append(entity_id)
            return True

        with patch(
            "custom_components.shutter_pilot.awning_guard.set_cover_position",
            new=_fake_drive,
        ):
            await async_enforce_guard(hass, entry)

        assert driven == []


# --- Der Fahrweg, den 2.20.0 ungetestet gelassen hat -------------------------


class TestOpeningAndClosingByConditions:
    """hollizone: „nachdem ich ein Rollo zu Dachfenster importiert hatte gab es
    leider keinerlei Funktion."

    2.20.0 hatte den Schutz getestet, aber nicht den Weg, auf dem ein
    Dachfenster ueberhaupt oeffnet – und genau dort steckte ein Fehler, der
    schlimmer ist als keine Funktion: die Freigabe fuhr auf `position_open`.
    Bei einer Markise heisst das „eingefahren", bei einem Dachfenster „weit
    auf". Sobald der Raum abkuehlte, riss es das Fenster auf, statt es zu
    schliessen.
    """

    @staticmethod
    async def _setup(hass, temp: str, rain: str | None = None):
        from unittest.mock import patch as _patch

        from custom_components.shutter_pilot import cover_tracker
        from custom_components.shutter_pilot.const import (
            AREA_MODE_NONE,
            CONF_AREA_AZIMUTH_ENABLED,
            CONF_AREA_DRIVE_DELAY,
            CONF_AREA_ELEVATION_ENABLED,
            CONF_AREA_MODE,
            CONF_AREA_NAME,
            CONF_AREA_SUN_PROTECT_ENABLED,
            CONF_AREAS,
            CONF_NAME,
        )

        cover_tracker.STARTUP_RESTORE_DELAY_SEC = 0
        cover_tracker.STARTUP_RESTORE_RETRY_SEC = 0
        temp_sensor = "sensor.innentemperatur"
        hass.states.async_set(
            "cover.dachfenster_bad",
            "closed",
            {"current_position": 0, "supported_features": 15},
        )
        hass.states.async_set(temp_sensor, temp, {"unit_of_measurement": "°C"})
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 30.0, "azimuth": 180.0}
        )
        # Ein Regensensor ist optional, damit die beiden bestehenden Tests
        # (ohne Wetterschutz konfiguriert) unveraendert bleiben.
        if rain is not None:
            hass.states.async_set(RAIN, rain)
        e_key, on_key, off_key, _ = sun_condition_keys("a")
        area = {
            CONF_AREA_ID: "bad",
            CONF_AREA_NAME: "Bad",
            CONF_AREA_MODE: AREA_MODE_NONE,
            CONF_AREA_DRIVE_DELAY: 0,
            CONF_AREA_SUN_PROTECT_ENABLED: True,
            CONF_AREA_ELEVATION_ENABLED: False,
            CONF_AREA_AZIMUTH_ENABLED: False,
            e_key: temp_sensor,
            on_key: 24,
            off_key: 22,
        }
        options = {
            CONF_AREAS: [area],
            CONF_SHUTTERS: [{**WINDOW, CONF_NAME: "Dachfenster"}],
        }
        if rain is not None:
            options[sun_condition_keys("rain")[0]] = RAIN
            options["guard_rain_lockout"] = 10
        entry = MockConfigEntry(domain=DOMAIN, options=options)
        entry.add_to_hass(hass)
        with _patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
        return entry, hass.data[DOMAIN][entry.entry_id], temp_sensor

    @staticmethod
    async def _ticks(hass, data, count: int = 2):
        from homeassistant.util import dt as dt_util

        for _ in range(count):
            now = dt_util.now()
            for cb in list(data.get("_minute_callbacks", {}).values()):
                cb(now)
            await hass.async_block_till_done()

    async def test_a_warm_room_opens_it_to_the_airing_gap(self, hass):
        from pytest_homeassistant_custom_component.common import async_mock_service

        calls = async_mock_service(hass, "cover", "set_cover_position")
        _entry, data, _temp = await self._setup(hass, "26.0")
        await self._ticks(hass, data)

        assert 30 in [c.data["position"] for c in calls], (
            "ohne diesen Fahrweg hat ein Dachfenster keinerlei Funktion"
        )

    async def test_cooling_down_shuts_it_rather_than_throwing_it_open(self, hass):
        from pytest_homeassistant_custom_component.common import async_mock_service

        calls = async_mock_service(hass, "cover", "set_cover_position")
        _entry, data, temp = await self._setup(hass, "26.0")
        await self._ticks(hass, data)
        calls.clear()

        hass.states.async_set(temp, "20.0", {"unit_of_measurement": "°C"})
        await self._ticks(hass, data)

        positions = [c.data["position"] for c in calls]
        assert 0 in positions, f"muss schliessen, gefahren wurde: {positions}"
        assert 100 not in positions, (
            "die Freigabe darf das Fenster nicht aufreissen"
        )


# --- Der Wetterschutz muss die Fahrt kennen, nicht nur die Markise ----------


class TestGuardBeatsShadingForAWindow:
    """Derselbe Fall wie `TestGuardBeatsShading` in test_awning_shading.py,
    nur an der Geraeteart, fuer die der Schutz vor der Fahrt bisher nie
    gefragt wurde: `_drive_sun_protect()` in elevation.py prüfte den
    Wetterschutz nur unter `if awning:` – ein Dachfenster lief an dieser
    Pruefung vorbei und konnte trotz aktivem Regenschutz auf die
    Lueftungsspalt-Position hinausgefahren werden.

    Der schwerere Teil steckt in der zweiten und dritten Pruefung: der Schutz
    faehrt pro Gefahrenepisode nur *einmal* zu (`state["retracted"]` in
    awning_guard.py, damit er nicht gegen eine manuelle Korrektur ankaempft).
    Ohne den Fix in elevation.py haette die Beschattung genau diese Sperre
    ausgenutzt und das Fenster waehrend anhaltendem Regen beliebig oft wieder
    aufreissen koennen, weil sie den Schutz gar nicht erst fragte.
    """

    # Dieselben Helfer wie oben, per Referenz statt per Vererbung – eine
    # Test-Unterklasse wuerde pytest sonst auch die beiden geerbten Tests aus
    # TestOpeningAndClosingByConditions ein zweites Mal einsammeln lassen.
    _setup = staticmethod(TestOpeningAndClosingByConditions._setup)
    _ticks = staticmethod(TestOpeningAndClosingByConditions._ticks)

    async def test_rain_suppresses_the_airing_gap(self, hass):
        from pytest_homeassistant_custom_component.common import async_mock_service

        calls = async_mock_service(hass, "cover", "set_cover_position")
        _entry, data, _temp = await self._setup(hass, "26.0", rain="on")
        await self._ticks(hass, data)

        assert 30 not in [c.data["position"] for c in calls], (
            "die Beschattung darf ein Dachfenster nicht bei aktivem "
            "Regenschutz oeffnen"
        )

    async def test_it_stays_shut_across_further_ticks(self, hass):
        from pytest_homeassistant_custom_component.common import async_mock_service

        calls = async_mock_service(hass, "cover", "set_cover_position")
        _entry, data, _temp = await self._setup(hass, "26.0", rain="on")
        await self._ticks(hass, data, count=5)

        assert 30 not in [c.data["position"] for c in calls], (
            "auch ueber mehrere Minutentakte darf es nicht aufgehen, "
            "solange es weiterregnet"
        )

    async def test_the_once_per_episode_lockout_does_not_let_shading_reopen_it(
        self, hass
    ):
        """Erst auf (trocken), dann Regen – der Schutz faehrt genau einmal
        zu. Die Beschattung darf die zweite Fahrt nicht selbst uebernehmen,
        nur weil der Schutz sich fuer diese Gefahrenepisode schon erledigt
        haelt.
        """
        from pytest_homeassistant_custom_component.common import async_mock_service

        calls = async_mock_service(hass, "cover", "set_cover_position")
        _entry, data, _temp = await self._setup(hass, "26.0", rain="off")
        await self._ticks(hass, data)
        assert 30 in [c.data["position"] for c in calls], (
            "Vorbedingung: trocken und warm oeffnet wie gewohnt"
        )
        hass.states.async_set(
            "cover.dachfenster_bad",
            "open",
            {"current_position": 30, "supported_features": 15},
        )
        calls.clear()

        # Regen setzt ein - der Schutz greift ueber den Sensor-Listener
        # sofort, nicht erst beim naechsten Minutentakt, und merkt sich diese
        # Fahrt als "Gefahrenepisode erledigt" (state["retracted"]).
        hass.states.async_set(RAIN, "on")
        await hass.async_block_till_done()
        assert 0 in [c.data["position"] for c in calls], (
            "der Schutz muss sofort zufahren"
        )
        hass.states.async_set(
            "cover.dachfenster_bad",
            "closed",
            {"current_position": 0, "supported_features": 15},
        )
        calls.clear()

        # Es regnet weiter unveraendert - ohne den Fix wuerde die
        # Beschattung (Temperatur weiterhin ueber der Schwelle) das Fenster
        # jetzt erneut oeffnen, weil sie den Schutz fuer Nicht-Markisen nie
        # gefragt hat.
        await self._ticks(hass, data, count=3)

        assert 30 not in [c.data["position"] for c in calls], (
            "die einmal-pro-Gefahrenepisode-Sperre des Schutzes darf die "
            "Beschattung nicht dazu bringen, das Fenster waehrend "
            "anhaltendem Regen erneut zu oeffnen"
        )


class TestGuardGateAppliesByHasGuardNotByAwning:
    """Die Unterscheidung, um die es in diesem Fix geht: `has_guard(shutter)`
    entscheidet, ob der Wetterschutz gefragt wird, nicht `is_awning(shutter)`
    und nicht die Art, wie die Zielposition berechnet wird. Ein Rollladen
    ohne Schutz muss von alledem unberuehrt bleiben, auch wenn im selben
    Bereich zur selben Zeit eine Markise und ein Dachfenster wegen Regen
    gesperrt sind.
    """

    async def test_the_shutter_is_untouched_while_the_awning_and_window_are_barred(
        self, hass
    ):
        from unittest.mock import patch as _patch

        from pytest_homeassistant_custom_component.common import async_mock_service

        from custom_components.shutter_pilot import cover_tracker
        from custom_components.shutter_pilot.const import (
            AREA_MODE_NONE,
            CONF_AREA_AZIMUTH_ENABLED,
            CONF_AREA_DRIVE_DELAY,
            CONF_AREA_ELEVATION_ENABLED,
            CONF_AREA_MODE,
            CONF_AREA_NAME,
            CONF_AREA_SUN_PROTECT_ENABLED,
            CONF_AREAS,
            CONF_NAME,
        )

        cover_tracker.STARTUP_RESTORE_DELAY_SEC = 0
        cover_tracker.STARTUP_RESTORE_RETRY_SEC = 0

        for cover in (
            SHUTTER[CONF_COVER_ENTITY_ID],
            AWNING[CONF_COVER_ENTITY_ID],
            WINDOW[CONF_COVER_ENTITY_ID],
        ):
            hass.states.async_set(
                cover, "closed", {"current_position": 0, "supported_features": 15}
            )
        temp_sensor = "sensor.innentemperatur"
        hass.states.async_set(temp_sensor, "26.0", {"unit_of_measurement": "°C"})
        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 30.0, "azimuth": 180.0}
        )
        hass.states.async_set(RAIN, "on")

        e_key, on_key, off_key, _ = sun_condition_keys("a")
        area = {
            CONF_AREA_ID: "bad",
            CONF_AREA_NAME: "Bad",
            CONF_AREA_MODE: AREA_MODE_NONE,
            CONF_AREA_DRIVE_DELAY: 0,
            CONF_AREA_SUN_PROTECT_ENABLED: True,
            CONF_AREA_ELEVATION_ENABLED: False,
            CONF_AREA_AZIMUTH_ENABLED: False,
            e_key: temp_sensor,
            on_key: 24,
            off_key: 22,
        }
        entry = MockConfigEntry(
            domain=DOMAIN,
            options={
                CONF_AREAS: [area],
                CONF_SHUTTERS: [
                    {**SHUTTER, CONF_NAME: "Rollladen"},
                    {**AWNING, CONF_NAME: "Markise"},
                    {**WINDOW, CONF_NAME: "Dachfenster"},
                ],
                sun_condition_keys("rain")[0]: RAIN,
                "guard_rain_lockout": 10,
            },
        )
        entry.add_to_hass(hass)
        calls = async_mock_service(hass, "cover", "set_cover_position")
        with _patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
        data = hass.data[DOMAIN][entry.entry_id]

        from homeassistant.util import dt as dt_util

        for _ in range(2):
            now = dt_util.now()
            for cb in list(data.get("_minute_callbacks", {}).values()):
                cb(now)
            await hass.async_block_till_done()

        by_entity: dict[str, list[int]] = {}
        for c in calls:
            by_entity.setdefault(c.data["entity_id"], []).append(c.data["position"])

        assert 50 in by_entity.get(SHUTTER[CONF_COVER_ENTITY_ID], []), (
            "ein ungeschuetzter Rollladen muss trotz Regen ganz normal "
            "beschatten"
        )
        assert 100 not in by_entity.get(AWNING[CONF_COVER_ENTITY_ID], []), (
            "die Markise darf bei Regen nicht ausfahren"
        )
        assert 30 not in by_entity.get(WINDOW[CONF_COVER_ENTITY_ID], []), (
            "das Dachfenster darf bei Regen nicht auf die "
            "Lueftungsspalt-Position fahren"
        )


class TestTheExportExplainsAQuietWindow:
    """Damit „keinerlei Funktion" nicht wieder als Fehler gemeldet wird."""

    @staticmethod
    def _notes(shutter, area):
        from custom_components.shutter_pilot.export import _window_silent_notes

        return "\n".join(_window_silent_notes(shutter, area))

    def test_an_area_without_sun_protection_is_named(self):
        from custom_components.shutter_pilot.const import (
            CONF_AREA_SUN_PROTECT_ENABLED,
        )

        notes = self._notes(WINDOW, {CONF_AREA_ID: "bad", CONF_AREA_SUN_PROTECT_ENABLED: False})
        assert "Sonnenschutz aus" in notes

    def test_a_missing_area_is_named(self):
        assert "kein Bereich" in self._notes(WINDOW, None)

    def test_an_area_without_conditions_gets_a_hint(self):
        from custom_components.shutter_pilot.const import (
            CONF_AREA_SUN_PROTECT_ENABLED,
        )

        notes = self._notes(WINDOW, {CONF_AREA_ID: "bad", CONF_AREA_SUN_PROTECT_ENABLED: True})
        assert "keine Bedingung" in notes

    def test_a_properly_configured_window_stays_quiet(self):
        from custom_components.shutter_pilot.const import (
            CONF_AREA_SUN_PROTECT_ENABLED,
        )

        area = {
            CONF_AREA_ID: "bad",
            CONF_AREA_SUN_PROTECT_ENABLED: True,
            sun_condition_keys("a")[0]: "sensor.innentemperatur",
        }
        assert self._notes(WINDOW, area) == ""

    def test_leftover_shutter_keys_are_named(self):
        from custom_components.shutter_pilot.const import (
            CONF_AREA_SUN_PROTECT_ENABLED,
            CONF_LOCK_PROTECTION,
        )

        area = {
            CONF_AREA_ID: "bad",
            CONF_AREA_SUN_PROTECT_ENABLED: True,
            sun_condition_keys("a")[0]: "sensor.innentemperatur",
        }
        notes = self._notes({**WINDOW, CONF_LOCK_PROTECTION: True}, area)
        assert "lock_protection" in notes
