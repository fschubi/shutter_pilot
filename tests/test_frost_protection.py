"""Frostschutz – Anregung von Linos aus dem Forum.

Bei erfüllter Bedingung soll der Rollladen nicht ganz schließen, damit die
Lamellen nicht am Fensterbrett festfrieren. Dieselbe Mechanik wie die
abweichende Schließposition für laue Abende, nur mit umgekehrter
Vergleichsrichtung: Frost heißt "kälter als", nicht "wärmer als".
"""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CLOSE_CONDITION_SLOT,
    CONF_AREA_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_CLOSED_ALT,
    CONF_POSITION_CLOSED_FROST,
    FROST_CONDITION_SLOT,
    ROLE_CLOSED,
    ROLE_CLOSED_ALT,
    ROLE_CLOSED_FROST,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    _condition_slot_met,
    condition_memory,
    frost_condition_met,
    get_position_for_role,
    has_frost_close_position,
    resolve_close_role,
)

TEMP = "sensor.forecast_low"


def _area(**overrides) -> dict:
    area = {CONF_AREA_ID: "living"}
    area.update(overrides)
    return area


def _frost_area(on_below: float = 2.0, off_above: float = 5.0) -> dict:
    """Ohne Invert-Flag: der Frost-Slot vergleicht von sich aus nach unten."""
    entity_key, on_key, off_key, _states = sun_condition_keys(FROST_CONDITION_SLOT)
    return _area(
        **{
            entity_key: TEMP,
            on_key: on_below,
            off_key: off_above,
        }
    )


def _shutter(**overrides) -> dict:
    shutter = {CONF_POSITION_CLOSED: 0}
    shutter.update(overrides)
    return shutter


def _temp(hass, value) -> None:
    hass.states.async_set(TEMP, value)


class TestInvertedComparison:
    """Ohne Invertierung liesse sich "unter X" nicht ausdrücken."""

    async def test_below_threshold_triggers(self, hass):
        _temp(hass, 1.0)
        assert frost_condition_met(hass, _frost_area(), {}) is True

    async def test_above_threshold_does_not(self, hass):
        _temp(hass, 8.0)
        assert frost_condition_met(hass, _frost_area(), {}) is False

    async def test_hysteresis_holds_until_it_is_warm_again(self, hass):
        """Zwischen 2 und 5 Grad bleibt der Frostschutz an, wenn er an war."""
        data: dict = {}
        area = _frost_area(on_below=2.0, off_above=5.0)

        _temp(hass, 1.0)
        assert frost_condition_met(hass, area, data) is True

        _temp(hass, 4.0)  # im Zwischenbereich
        assert frost_condition_met(hass, area, data) is True, "hält"

        _temp(hass, 6.0)
        assert frost_condition_met(hass, area, data) is False

        _temp(hass, 4.0)
        assert frost_condition_met(hass, area, data) is False, "greift nicht neu"

    async def test_swapped_thresholds_are_tolerated(self, hass):
        """off_above unter on_below wäre unsinnig – nicht durchrutschen lassen."""
        data: dict = {}
        area = _frost_area(on_below=2.0, off_above=-3.0)
        _temp(hass, 1.0)
        assert frost_condition_met(hass, area, data) is True
        _temp(hass, 1.9)
        assert frost_condition_met(hass, area, data) is True

    async def test_unconfigured_never_triggers(self, hass):
        """Fail closed: wer nichts einstellt, merkt nichts."""
        assert frost_condition_met(hass, _area(), {}) is False

    @pytest.mark.parametrize("state", ["unavailable", "unknown"])
    async def test_dead_sensor_does_not_trigger(self, hass, state):
        """Umgekehrt zur Beschattung: ein toter Sensor darf nicht jede Nacht
        einen Spalt offen lassen."""
        _temp(hass, state)
        assert frost_condition_met(hass, _frost_area(), {}) is False

    async def test_missing_entity_does_not_trigger(self, hass):
        assert frost_condition_met(hass, _frost_area(), {}) is False


class TestNormalDirectionUnchanged:
    """Die bestehenden Bedingungen dürfen sich nicht verändert haben."""

    async def test_without_invert_it_still_compares_upwards(self, hass):
        entity_key, on_key, off_key, _s = sun_condition_keys("a")
        area = _area(**{entity_key: TEMP, on_key: 20.0, off_key: 18.0})
        memory: dict = {}

        _temp(hass, 25.0)
        assert _condition_slot_met(hass, area, "a", memory) is True
        _temp(hass, 19.0)
        assert _condition_slot_met(hass, area, "a", memory) is True, "Hysterese"
        _temp(hass, 17.0)
        assert _condition_slot_met(hass, area, "a", memory) is False


class TestCloseRole:
    async def test_frost_wins_over_the_mild_evening_position(self, hass):
        """Schutz schlägt Komfort, wenn beide Bedingungen zugleich gelten."""
        close_entity, close_on, _off, _s = sun_condition_keys(CLOSE_CONDITION_SLOT)
        area = _frost_area()
        area[close_entity] = TEMP
        area[close_on] = -50.0  # gilt immer

        _temp(hass, 1.0)  # Frost gilt ebenfalls
        shutter = _shutter(
            **{CONF_POSITION_CLOSED_ALT: 50, CONF_POSITION_CLOSED_FROST: 10}
        )
        assert resolve_close_role(hass, area, shutter, {}) == ROLE_CLOSED_FROST

    async def test_falls_back_to_alt_when_it_is_warm(self, hass):
        close_entity, close_on, _off, _s = sun_condition_keys(CLOSE_CONDITION_SLOT)
        area = _frost_area()
        area[close_entity] = TEMP
        area[close_on] = -50.0

        _temp(hass, 20.0)
        shutter = _shutter(
            **{CONF_POSITION_CLOSED_ALT: 50, CONF_POSITION_CLOSED_FROST: 10}
        )
        assert resolve_close_role(hass, area, shutter, {}) == ROLE_CLOSED_ALT

    async def test_without_a_frost_position_nothing_changes(self, hass):
        """Die Bereichsbedingung allein reicht nicht – der Rollladen entscheidet."""
        _temp(hass, 1.0)
        assert resolve_close_role(hass, _frost_area(), _shutter(), {}) == ROLE_CLOSED

    async def test_empty_frost_position_counts_as_unset(self, hass):
        _temp(hass, 1.0)
        shutter = _shutter(**{CONF_POSITION_CLOSED_FROST: ""})
        assert resolve_close_role(hass, _frost_area(), shutter, {}) == ROLE_CLOSED

    async def test_no_area_means_plain_closed(self, hass):
        assert resolve_close_role(hass, None, _shutter(), {}) == ROLE_CLOSED


class TestPosition:
    def test_role_resolves_to_the_configured_gap(self):
        shutter = _shutter(**{CONF_POSITION_CLOSED_FROST: 12})
        assert get_position_for_role(shutter, ROLE_CLOSED_FROST) == 12

    def test_a_gap_is_higher_than_closed(self):
        """0 = zu. "Nicht ganz zu" heisst deshalb ein grösserer Wert."""
        shutter = _shutter(**{CONF_POSITION_CLOSED: 0, CONF_POSITION_CLOSED_FROST: 10})
        assert get_position_for_role(
            shutter, ROLE_CLOSED_FROST
        ) > get_position_for_role(shutter, ROLE_CLOSED)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(10, True), (0, True), ("", False), (None, False), ("abc", False)],
    )
    def test_has_frost_close_position(self, value, expected):
        assert has_frost_close_position({CONF_POSITION_CLOSED_FROST: value}) is expected

    def test_missing_key_is_false(self):
        assert has_frost_close_position({}) is False


class TestMemoryIsolation:
    async def test_frost_and_close_do_not_share_hysteresis(self, hass):
        """Beide Slots liegen im selben Bereichs-Speicher, getrennt nach Namen."""
        data: dict = {}
        area = _frost_area()
        _temp(hass, 1.0)
        frost_condition_met(hass, area, data)
        memory = condition_memory(data, "living")
        assert memory.get(FROST_CONDITION_SLOT) is True
        assert CLOSE_CONDITION_SLOT not in memory
