"""Frostschutz und Eisschutz fragen bei Zahlen immer „kälter als".

eurofinder (simon42 #262) sah im Bereich unter „Frostschutz" den Haken
„Bedeutung umkehren" – angehakt – und fragte, wozu er da ist. Für einen
Temperatursensor gibt es keine sinnvolle Antwort: angehakt ist er die
Vorgabe, abgewählt macht er aus dem Frostschutz einen Wärmeschalter, und der
Rollladen schließt an jedem warmen Abend nur bis zur Frostschutz-Position.
Am Eisschutz der Markise wäre es noch schlimmer: Gefahr bei Wärme, die
Markise bleibt den ganzen Sommer eingefahren.

Dieselbe Falle hatte 2.38.2 schon für die Frostsperre geschlossen. Jetzt gilt
das für alle drei Slots (FORCED_BELOW_SLOTS), und zwar auch für einen Haken,
der in einer älteren Version abgewählt gespeichert wurde. Binärsensor und
Zustandsliste behalten die Umkehr – dort beschreibt sie das Gerät, nicht die
Richtung.
"""

from __future__ import annotations

from custom_components.shutter_pilot.const import (
    AWNING_GUARD_ICE,
    CONF_AREA_ID,
    FORCED_BELOW_SLOTS,
    FROST_CONDITION_SLOT,
    FROST_LOCK_SLOT,
    sun_condition_invert_key,
    sun_condition_keys,
)
from custom_components.shutter_pilot.helpers import (
    _slot_reading,
    frost_condition_met,
    numeric_inverted,
)

TEMP = "sensor.aussen"


def _cfg(slot: str, on: float, off: float, invert=None) -> dict:
    entity_key, on_key, off_key, _states = sun_condition_keys(slot)
    cfg = {CONF_AREA_ID: "diele", entity_key: TEMP, on_key: on, off_key: off}
    if invert is not None:
        cfg[sun_condition_invert_key(slot)] = invert
    return cfg


class TestFrostSlot:
    async def test_an_unticked_box_no_longer_turns_frost_into_heat(self, hass):
        """eurofinders Werte: einschalten unter 2, ausschalten über 3."""
        area = _cfg(FROST_CONDITION_SLOT, 2, 3, invert=False)

        hass.states.async_set(TEMP, "18.0")
        assert frost_condition_met(hass, area, {}) is False

        hass.states.async_set(TEMP, "1.0")
        assert frost_condition_met(hass, area, {}) is True

    async def test_ticked_and_untouched_behave_the_same(self, hass):
        for invert in (True, None):
            area = _cfg(FROST_CONDITION_SLOT, 2, 3, invert=invert)
            hass.states.async_set(TEMP, "1.0")
            assert frost_condition_met(hass, area, {}) is True
            hass.states.async_set(TEMP, "18.0")
            assert frost_condition_met(hass, area, {}) is False

    async def test_the_hysteresis_still_holds_until_the_second_value(self, hass):
        area = _cfg(FROST_CONDITION_SLOT, 2, 3, invert=False)
        memory: dict = {}
        hass.states.async_set(TEMP, "1.0")
        assert frost_condition_met(hass, area, memory) is True
        hass.states.async_set(TEMP, "2.5")
        assert frost_condition_met(hass, area, memory) is True
        hass.states.async_set(TEMP, "3.5")
        assert frost_condition_met(hass, area, memory) is False

    async def test_an_inverted_binary_sensor_still_works(self, hass):
        """Bei einem Kontakt beschreibt der Haken das Gerät – der bleibt."""
        entity_key, _on, _off, _states = sun_condition_keys(FROST_CONDITION_SLOT)
        area = {
            CONF_AREA_ID: "diele",
            entity_key: "binary_sensor.warm",
            sun_condition_invert_key(FROST_CONDITION_SLOT): True,
        }
        hass.states.async_set("binary_sensor.warm", "off")
        assert frost_condition_met(hass, area, {}) is True


class TestIceSlot:
    async def test_an_unticked_box_no_longer_means_danger_when_warm(self, hass):
        cfg = _cfg(AWNING_GUARD_ICE, -2, 2, invert=False)

        hass.states.async_set(TEMP, "25.0")
        assert _slot_reading(hass, cfg, AWNING_GUARD_ICE, {}) is False

        hass.states.async_set(TEMP, "-5.0")
        assert _slot_reading(hass, cfg, AWNING_GUARD_ICE, {}) is True


class TestSharedRule:
    def test_the_three_slots_are_forced(self):
        assert set(FORCED_BELOW_SLOTS) == {
            FROST_CONDITION_SLOT,
            AWNING_GUARD_ICE,
            FROST_LOCK_SLOT,
        }
        for slot in FORCED_BELOW_SLOTS:
            assert numeric_inverted({sun_condition_invert_key(slot): False}, slot)

    def test_other_slots_still_follow_the_box(self):
        assert numeric_inverted({sun_condition_invert_key("a"): True}, "a") is True
        assert numeric_inverted({}, "a") is False
        assert numeric_inverted({sun_condition_invert_key("wind"): True}, "wind") is True
