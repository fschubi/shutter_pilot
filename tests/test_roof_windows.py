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
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
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
    guard_rest_role,
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
        assert guard_rest_role(AWNING) == ROLE_OPEN
        assert guard_rest_role(WINDOW) == ROLE_CLOSED

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
