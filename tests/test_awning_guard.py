"""Wind-, Regen- und Frostschutz der Markise.

Die Schutzebene ist der Teil der Markisensteuerung, der kein Komfort ist: eine
Markise, die im Sturm draussen bleibt, ist eine Reparatur. Entsprechend sitzen
die Tests auf den Entscheidungen, nicht auf der Fahrt.

Bewusst mit hingestelltem Laufzeit-Dict statt echtem Setup – wie
`test_export_notes.py`. Der Guard liest Optionen, `hass.states` und das Dict,
mehr braucht er nicht, und die schwere Fixture aus `test_forum_findings.py`
kostet vierzehn Sekunden je Test.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.awning_guard import (
    async_enforce_guard,
    clamp_to_rest,
    evaluate_guard,
    guard_status,
    is_barred,
    resolve_guard_config,
)
from custom_components.shutter_pilot.const import (
    AWNING_GUARD_ICE,
    AWNING_GUARD_RAIN,
    AWNING_GUARD_WIND,
    CONF_AWNING_SENSOR_GRACE,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_NAME,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
    EVENT_AWNING_RETRACTED,
    GUARD_REASON_UNAVAILABLE,
    KIND_AWNING,
    awning_lockout_key,
    sun_condition_keys,
)

AWNING = "cover.markise_terrasse"
WIND = "sensor.windgeschwindigkeit"
RAIN = "binary_sensor.regen"
TEMP = "sensor.aussentemperatur"

MINUTE = 60.0
# Zeitabhängige Tests stellen die Uhr durchgängig selbst, ab dem ersten Aufruf.
# Ein erster Aufruf ohne `now` nähme die echte monotone Uhr als Nullpunkt, und
# jeder danach übergebene Wert läge Jahre davor.
T0 = 0.0


def _slot(slot: str, **values):
    """Optionen für einen Schutz-Slot aufbauen."""
    entity, on_above, off_below, states = sun_condition_keys(slot)
    out = {}
    if "entity" in values:
        out[entity] = values["entity"]
    if "on_above" in values:
        out[on_above] = values["on_above"]
    if "off_below" in values:
        out[off_below] = values["off_below"]
    if "states" in values:
        out[states] = values["states"]
    if "lockout" in values:
        out[awning_lockout_key(slot)] = values["lockout"]
    return out


def _awning(**extra):
    return {
        CONF_COVER_ENTITY_ID: AWNING,
        CONF_NAME: "Markise Terrasse",
        CONF_DEVICE_KIND: KIND_AWNING,
        CONF_POSITION_OPEN: 0,
        CONF_POSITION_SUN_PROTECT: 100,
        **extra,
    }


@pytest.fixture
def make_entry(hass):
    """Entry plus Laufzeit-Dict, ohne die Integration zu starten."""

    def _make(options=None, shutter=None):
        opts = {
            # Ein globaler Windsensor, wie im Panel unter Einstellungen.
            **_slot(AWNING_GUARD_WIND, entity=WIND, on_above=30, off_below=15),
            CONF_SHUTTERS: [shutter or _awning()],
        }
        opts.update(options or {})
        entry = MockConfigEntry(domain=DOMAIN, title="Shutter Pilot", options=opts)
        entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            "master_enabled": True,
            "sun_protect_covers": set(),
        }
        return entry

    return _make


def _data(hass, entry):
    return hass.data[DOMAIN][entry.entry_id]


# --- Schwelle und Hysterese --------------------------------------------------


class TestThreshold:
    """Einfahren ab `on_above`, Freigabe erst unter `off_below`."""

    async def test_calm_wind_lets_the_awning_out(self, hass, make_entry):
        entry = make_entry()
        hass.states.async_set(WIND, "8")

        state = evaluate_guard(hass, entry, _data(hass, entry), _awning())

        assert state["barred"] is False
        assert state["retract"] is False

    async def test_above_the_threshold_bars_and_retracts(self, hass, make_entry):
        entry = make_entry()
        hass.states.async_set(WIND, "34.1")

        state = evaluate_guard(hass, entry, _data(hass, entry), _awning())

        assert state["barred"] is True
        assert state["retract"] is True
        assert AWNING_GUARD_WIND in state["reasons"]

    async def test_the_hysteresis_holds_between_the_two_values(
        self, hass, make_entry
    ):
        """22 km/h liegt unter der Einfahr- und ueber der Freigabeschwelle.

        Ohne Hysterese pendelte die Markise genau in diesem Band.
        """
        entry = make_entry()
        data = _data(hass, entry)
        hass.states.async_set(WIND, "34")
        evaluate_guard(hass, entry, data, _awning(), now=T0)

        hass.states.async_set(WIND, "22")
        state = evaluate_guard(hass, entry, data, _awning(), now=MINUTE)

        assert state["retract"] is True

    async def test_below_the_release_value_ends_the_danger(self, hass, make_entry):
        entry = make_entry(
            {**_slot(AWNING_GUARD_WIND, entity=WIND, on_above=30, off_below=15,
                     lockout=0)}
        )
        data = _data(hass, entry)
        hass.states.async_set(WIND, "34")
        evaluate_guard(hass, entry, data, _awning(), now=T0)

        hass.states.async_set(WIND, "9")
        state = evaluate_guard(hass, entry, data, _awning(), now=MINUTE)

        assert state["barred"] is False


# --- Sperrzeit ---------------------------------------------------------------


class TestLockout:
    """Eine Boe ist nach zwanzig Sekunden vorbei. Die Markise trotzdem nicht."""

    async def test_the_awning_stays_in_after_the_gust(self, hass, make_entry):
        entry = make_entry(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30, off_below=15,
                  lockout=20)
        )
        data = _data(hass, entry)
        hass.states.async_set(WIND, "41")
        evaluate_guard(hass, entry, data, _awning(), now=T0)

        hass.states.async_set(WIND, "6")
        state = evaluate_guard(hass, entry, data, _awning(), now=5 * MINUTE)

        assert state["barred"] is True
        assert state["retract"] is False, "eingefahren ist sie laengst"
        assert f"{AWNING_GUARD_WIND}:lockout" in state["reasons"]

    async def test_after_the_lockout_it_may_go_out_again(self, hass, make_entry):
        entry = make_entry(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30, off_below=15,
                  lockout=20)
        )
        data = _data(hass, entry)
        hass.states.async_set(WIND, "41")
        evaluate_guard(hass, entry, data, _awning(), now=T0)
        hass.states.async_set(WIND, "6")
        evaluate_guard(hass, entry, data, _awning(), now=MINUTE)

        state = evaluate_guard(hass, entry, data, _awning(), now=25 * MINUTE)

        assert state["barred"] is False

    async def test_a_second_gust_restarts_the_clock(self, hass, make_entry):
        """Eine Boenfront ist eine Reihe von Boen, keine einzelne."""
        entry = make_entry(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30, off_below=15,
                  lockout=20)
        )
        data = _data(hass, entry)
        hass.states.async_set(WIND, "41")
        evaluate_guard(hass, entry, data, _awning(), now=T0)
        hass.states.async_set(WIND, "6")
        evaluate_guard(hass, entry, data, _awning(), now=MINUTE)
        # Nachschlag nach fuenfzehn Minuten – die Sperrzeit lief fast ab.
        hass.states.async_set(WIND, "38")
        evaluate_guard(hass, entry, data, _awning(), now=15 * MINUTE)
        hass.states.async_set(WIND, "5")
        evaluate_guard(hass, entry, data, _awning(), now=16 * MINUTE)

        state = evaluate_guard(hass, entry, data, _awning(), now=30 * MINUTE)

        assert state["barred"] is True, "gerechnet wird ab der letzten Boe"

    async def test_a_sensor_that_was_always_calm_invents_no_lockout(
        self, hass, make_entry
    ):
        """Gegenprobe zum Fehler, der beim Schreiben drinstand.

        Wurde die Ruhe-Uhr beim ersten Blick auf einen ruhigen Sensor gestellt
        statt beim Uebergang von Gefahr auf Ruhe, sperrte jeder Neustart jede
        Markise zwanzig Minuten lang aus.
        """
        entry = make_entry(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30, off_below=15,
                  lockout=20)
        )
        data = _data(hass, entry)
        hass.states.async_set(WIND, "4")

        evaluate_guard(hass, entry, data, _awning(), now=T0)
        state = evaluate_guard(hass, entry, data, _awning(), now=MINUTE)

        assert state["barred"] is False


# --- Toter Sensor ------------------------------------------------------------


class TestDeadSensor:
    """Nicht eingerichtet ist nicht dasselbe wie kaputt."""

    async def test_no_sensor_means_no_protection(self, hass, make_entry):
        entry = make_entry({**_slot(AWNING_GUARD_WIND, entity="")})

        state = evaluate_guard(hass, entry, _data(hass, entry), _awning())

        assert state["barred"] is False

    async def test_an_unavailable_sensor_bars_at_once(self, hass, make_entry):
        entry = make_entry()
        hass.states.async_set(WIND, "unavailable")

        state = evaluate_guard(hass, entry, _data(hass, entry), _awning())

        assert state["barred"] is True
        assert f"{AWNING_GUARD_WIND}:{GUARD_REASON_UNAVAILABLE}" in state["reasons"]

    async def test_but_does_not_yank_it_in_during_the_grace(
        self, hass, make_entry
    ):
        """Ein Sensor, der beim Neustart kurz aussetzt, ist kein Sturm."""
        entry = make_entry({CONF_AWNING_SENSOR_GRACE: 10})
        hass.states.async_set(WIND, "unknown")

        state = evaluate_guard(hass, entry, _data(hass, entry), _awning())

        assert state["barred"] is True
        assert state["retract"] is False

    async def test_after_the_grace_it_comes_in(self, hass, make_entry):
        entry = make_entry({CONF_AWNING_SENSOR_GRACE: 10})
        data = _data(hass, entry)
        hass.states.async_set(WIND, "unavailable")
        evaluate_guard(hass, entry, data, _awning(), now=T0)

        state = evaluate_guard(hass, entry, data, _awning(), now=11 * MINUTE)

        assert state["retract"] is True

    async def test_a_recovered_sensor_clears_the_grace(self, hass, make_entry):
        entry = make_entry({CONF_AWNING_SENSOR_GRACE: 10})
        data = _data(hass, entry)
        hass.states.async_set(WIND, "unavailable")
        evaluate_guard(hass, entry, data, _awning(), now=T0)

        hass.states.async_set(WIND, "7")
        state = evaluate_guard(hass, entry, data, _awning(), now=5 * MINUTE)

        assert state["barred"] is False
        assert state["retract"] is False


# --- Regen und Frost ---------------------------------------------------------


class TestRainAndIce:
    async def test_a_binary_rain_sensor_reads_the_natural_way_round(
        self, hass, make_entry
    ):
        """„on" heisst Regen heisst Gefahr – ohne Invertierung."""
        entry = make_entry(
            {
                **_slot(AWNING_GUARD_WIND, entity=""),
                **_slot(AWNING_GUARD_RAIN, entity=RAIN, lockout=0),
            }
        )
        hass.states.async_set(RAIN, "on")

        state = evaluate_guard(hass, entry, _data(hass, entry), _awning())

        assert state["retract"] is True
        assert AWNING_GUARD_RAIN in state["reasons"]

    async def test_dry_weather_does_not_bar(self, hass, make_entry):
        entry = make_entry(
            {
                **_slot(AWNING_GUARD_WIND, entity=""),
                **_slot(AWNING_GUARD_RAIN, entity=RAIN, lockout=0),
            }
        )
        hass.states.async_set(RAIN, "off")

        assert evaluate_guard(hass, entry, _data(hass, entry), _awning())["barred"] is False

    async def test_ice_compares_downwards_without_being_told(
        self, hass, make_entry
    ):
        """Frost ist immer eine Frage nach unten – der Slot weiss das selbst."""
        entry = make_entry(
            {
                **_slot(AWNING_GUARD_WIND, entity=""),
                **_slot(AWNING_GUARD_ICE, entity=TEMP, on_above=-2, off_below=2,
                        lockout=0),
            }
        )
        hass.states.async_set(TEMP, "-4.5")

        state = evaluate_guard(hass, entry, _data(hass, entry), _awning())

        assert state["barred"] is True
        assert AWNING_GUARD_ICE in state["reasons"]

    async def test_a_mild_evening_is_no_ice(self, hass, make_entry):
        entry = make_entry(
            {
                **_slot(AWNING_GUARD_WIND, entity=""),
                **_slot(AWNING_GUARD_ICE, entity=TEMP, on_above=-2, off_below=2,
                        lockout=0),
            }
        )
        hass.states.async_set(TEMP, "14")

        assert evaluate_guard(hass, entry, _data(hass, entry), _awning())["barred"] is False


# --- Globaler Sensor und Ausnahme je Markise ---------------------------------


class TestConfigResolution:
    async def test_the_global_sensor_applies_without_an_override(self, hass):
        config = resolve_guard_config(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30), _awning()
        )

        assert config[sun_condition_keys(AWNING_GUARD_WIND)[0]] == WIND

    async def test_an_awning_may_name_its_own(self, hass):
        """Ein Balkon hinterm Haus sieht anderen Wind als die Terrasse."""
        own = "sensor.wind_balkon"
        config = resolve_guard_config(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30),
            _awning(**_slot(AWNING_GUARD_WIND, entity=own)),
        )

        assert config[sun_condition_keys(AWNING_GUARD_WIND)[0]] == own
        assert config[sun_condition_keys(AWNING_GUARD_WIND)[1]] == 30, (
            "die Schwelle bleibt global, wenn sie nicht mit ueberschrieben wird"
        )

    async def test_thresholds_alone_may_be_overridden(self, hass):
        """Ein kleiner Gelenkarm muss frueher rein als eine Kassette daneben."""
        config = resolve_guard_config(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30),
            _awning(**_slot(AWNING_GUARD_WIND, on_above=18)),
        )

        assert config[sun_condition_keys(AWNING_GUARD_WIND)[0]] == WIND
        assert config[sun_condition_keys(AWNING_GUARD_WIND)[1]] == 18

    async def test_an_empty_override_does_not_erase_the_global_value(self, hass):
        config = resolve_guard_config(
            _slot(AWNING_GUARD_WIND, entity=WIND, on_above=30),
            _awning(**_slot(AWNING_GUARD_WIND, entity="")),
        )

        assert config[sun_condition_keys(AWNING_GUARD_WIND)[0]] == WIND


# --- Die Fahrt ---------------------------------------------------------------


class TestEnforce:
    async def test_the_awning_is_driven_to_its_rest_position(
        self, hass, make_entry, monkeypatch
    ):
        entry = make_entry()
        hass.states.async_set(WIND, "44")
        driven: list[tuple] = []

        async def _fake(hass_, entry_, cover, position, reason, **kw):
            driven.append((cover, position, kw.get("urgent")))
            return True

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _fake
        )

        await async_enforce_guard(hass, entry)

        assert driven == [(AWNING, 0.0, True)], "und ohne den Mindestabstand"

    async def test_it_fires_an_event_with_the_reason(
        self, hass, make_entry, monkeypatch
    ):
        entry = make_entry()
        hass.states.async_set(WIND, "44")
        events = []
        hass.bus.async_listen(EVENT_AWNING_RETRACTED, lambda e: events.append(e.data))

        async def _fake(*a, **kw):
            return True

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _fake
        )

        await async_enforce_guard(hass, entry)
        await hass.async_block_till_done()

        assert events and events[0]["entity_id"] == AWNING
        assert AWNING_GUARD_WIND in events[0]["reasons"]

    async def test_it_does_not_drive_again_every_minute(
        self, hass, make_entry, monkeypatch
    ):
        entry = make_entry()
        hass.states.async_set(WIND, "44")
        calls = []

        async def _fake(*a, **kw):
            calls.append(a)
            return True

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _fake
        )

        await async_enforce_guard(hass, entry)
        await async_enforce_guard(hass, entry)

        assert len(calls) == 1

    async def test_but_a_failed_retraction_is_tried_again(
        self, hass, make_entry, monkeypatch
    ):
        """Der Merker gehoert an die Fahrt, nicht an die Absicht.

        Genau diese Verwechslung liess vor 2.8.0 eine gescheiterte
        Beschattungsfahrt als erledigt gelten – und sie wurde nie wiederholt.
        """
        entry = make_entry()
        hass.states.async_set(WIND, "44")
        calls = []

        async def _failing(*a, **kw):
            calls.append(a)
            return False

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _failing
        )

        await async_enforce_guard(hass, entry)
        await async_enforce_guard(hass, entry)

        assert len(calls) == 2

    async def test_the_shading_flag_is_dropped_on_retraction(
        self, hass, make_entry, monkeypatch
    ):
        """Sonst gilt die Markise weiter als beschattet und faehrt nie wieder."""
        entry = make_entry()
        data = _data(hass, entry)
        data["sun_protect_covers"] = {AWNING}
        hass.states.async_set(WIND, "44")

        async def _fake(*a, **kw):
            return True

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _fake
        )

        await async_enforce_guard(hass, entry)

        assert AWNING not in data["sun_protect_covers"]

    async def test_a_shutter_is_none_of_the_guard_s_business(
        self, hass, make_entry, monkeypatch
    ):
        entry = make_entry(
            shutter={
                CONF_COVER_ENTITY_ID: "cover.wohnzimmer",
                CONF_NAME: "Wohnzimmer",
            }
        )
        hass.states.async_set(WIND, "80")
        calls = []

        async def _fake(*a, **kw):
            calls.append(a)
            return True

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _fake
        )

        await async_enforce_guard(hass, entry)

        assert calls == []


# --- Der Schutz kennt die Schalter nicht -------------------------------------


class TestGuardIgnoresSwitches:
    """Bewusste Abweichung von der Rangfolge Haupt- > Bereichs- > Rollladenschalter.

    Ein Schutz, der sich versehentlich abschalten laesst, ist keiner. Abschalten
    geht absichtlich: den Sensor entfernen.
    """

    async def test_the_master_switch_being_off_changes_nothing(
        self, hass, make_entry, monkeypatch
    ):
        entry = make_entry()
        data = _data(hass, entry)
        data["master_enabled"] = False
        hass.states.async_set(WIND, "44")
        calls = []

        async def _fake(*a, **kw):
            calls.append(a)
            return True

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _fake
        )

        await async_enforce_guard(hass, entry)

        assert len(calls) == 1

    async def test_nor_does_the_awning_s_own_automation_switch(
        self, hass, make_entry, monkeypatch
    ):
        entry = make_entry(shutter=_awning(automation_enabled=False))
        data = _data(hass, entry)
        data["shutter_automation"] = {AWNING: False}
        hass.states.async_set(WIND, "44")
        calls = []

        async def _fake(*a, **kw):
            calls.append(a)
            return True

        monkeypatch.setattr(
            "custom_components.shutter_pilot.awning_guard.set_cover_position", _fake
        )

        await async_enforce_guard(hass, entry)

        assert len(calls) == 1


# --- Lesen ohne Anfassen -----------------------------------------------------


class TestReadOnlyStatus:
    async def test_guard_status_does_not_create_state(self, hass, make_entry):
        """Wie `_memory_copy()` im Export: der Bericht darf nichts verschieben."""
        entry = make_entry()
        data = _data(hass, entry)

        assert guard_status(data, AWNING) == {}
        assert is_barred(data, AWNING) is False
        assert "_awning_guard" not in data

    async def test_the_returned_status_is_a_copy(self, hass, make_entry):
        entry = make_entry()
        data = _data(hass, entry)
        hass.states.async_set(WIND, "44")
        evaluate_guard(hass, entry, data, _awning())

        guard_status(data, AWNING)["barred"] = False

        assert is_barred(data, AWNING) is True


# --- Richtung ----------------------------------------------------------------


class TestClamp:
    async def test_the_extended_target_is_capped_at_rest(self, hass):
        assert clamp_to_rest(_awning(), 100) == 0

    async def test_retracting_is_never_blocked(self, hass):
        """Sonst verweigerte der Schutz genau die Fahrt, fuer die er da ist."""
        assert clamp_to_rest(_awning(), 0) == 0

    async def test_an_actuator_wired_the_other_way_round_is_handled(self, hass):
        inverted = _awning(**{CONF_POSITION_OPEN: 100, CONF_POSITION_SUN_PROTECT: 0})

        assert clamp_to_rest(inverted, 0) == 100
        assert clamp_to_rest(inverted, 100) == 100
