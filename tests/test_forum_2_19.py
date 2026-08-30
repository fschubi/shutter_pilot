"""Forum 2.19.0 – der Aufhebepunkt, der aus einem leeren Feld entstand.

bjoerg im Forum: waehrend eines Gewitters fiel die Helligkeit auf rund 6000 lx,
die Beschattung blieb trotzdem unten. Sein Export zeigt `sun_cond_a_on_above:
60000` und `sun_cond_a_off_below: 0` – er selbst sagt, beim zweiten Wert habe
er "nichts eingetragen", und sein Screenshot zeigt das Feld leer.

Beides stimmt: der Feld-Helfer des Panels machte aus `Number("")` eine 0. Leer
haette laut Hinweis "gleicher Wert wie Beschatten ab" bedeutet, 0 bedeutet an
einem Lux-Sensor "nie wieder aufheben". Die Auswertung hier ist korrekt und
bleibt unveraendert – diese Tests halten fest, was die beiden Werte tun, und
dass der Export den Fall benennt.
"""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_AREA_ID,
    sun_condition_invert_key,
    sun_condition_keys,
)
from custom_components.shutter_pilot.export import _condition_note
from custom_components.shutter_pilot.helpers import sun_extra_conditions_met

A_ENTITY, A_ON, A_OFF, A_STATES = sun_condition_keys("a")
LUX = "sensor.wetterstation_illuminance"


def _area(**overrides) -> dict:
    area = {CONF_AREA_ID: "living", A_ENTITY: LUX}
    area.update(overrides)
    return area


@pytest.fixture
def data() -> dict:
    return {}


class TestEmptyReleasePoint:
    """Ein leeres Feld faellt auf den Einschaltpunkt zurueck."""

    async def test_empty_string_falls_back_to_on_above(self, hass, data):
        area = _area(**{A_ON: 60000, A_OFF: ""})
        hass.states.async_set(LUX, "70000")
        assert sun_extra_conditions_met(hass, area, data) is True
        # Unter dem Einschaltpunkt faellt sie wieder weg, weil der
        # Aufhebepunkt derselbe Wert ist.
        hass.states.async_set(LUX, "25769")
        assert sun_extra_conditions_met(hass, area, data) is False

    async def test_missing_key_falls_back_to_on_above(self, hass, data):
        area = _area(**{A_ON: 60000})
        hass.states.async_set(LUX, "70000")
        assert sun_extra_conditions_met(hass, area, data) is True
        hass.states.async_set(LUX, "25769")
        assert sun_extra_conditions_met(hass, area, data) is False


class TestZeroReleasePoint:
    """bjoergs Fall: 0 ist eine echte Schranke, kein "leer"."""

    async def test_zero_keeps_the_condition_met(self, hass, data):
        area = _area(**{A_ON: 60000, A_OFF: 0})
        hass.states.async_set(LUX, "70000")
        assert sun_extra_conditions_met(hass, area, data) is True
        # Das Gewitter: 6000 lx liegen weit unter dem Einschaltpunkt, aber
        # ueber dem Aufhebepunkt 0 – die Bedingung bleibt erfuellt.
        hass.states.async_set(LUX, "6000")
        assert sun_extra_conditions_met(hass, area, data) is True
        # Auch bei voelliger Dunkelheit nicht: verglichen wird `value >=
        # off_below`, und 0 >= 0 ist wahr. Ein Helligkeitssensor kommt also
        # gar nicht mehr aus der Bedingung heraus – nur ein Neustart leert
        # den Merker.
        hass.states.async_set(LUX, "0")
        assert sun_extra_conditions_met(hass, area, data) is True

    async def test_zero_still_needs_the_switch_on_point_first(self, hass, data):
        """Nach einem Neustart ist der Merker leer – dann gilt on_above."""
        area = _area(**{A_ON: 60000, A_OFF: 0})
        hass.states.async_set(LUX, "25769")
        assert sun_extra_conditions_met(hass, area, data) is False


class TestExportNote:
    """Der Export benennt den Fall, denn Bestandsdaten tragen die 0 weiter."""

    async def test_note_for_zero_release_point(self, hass):
        hass.states.async_set(LUX, "25769")
        note = _condition_note(hass, _area(**{A_ON: 60000, A_OFF: 0}), "a", LUX)
        assert "Aufhebepunkt 0" in note
        assert "60000" in note

    async def test_no_note_for_a_real_hysteresis(self, hass):
        hass.states.async_set(LUX, "25769")
        note = _condition_note(hass, _area(**{A_ON: 60000, A_OFF: 50000}), "a", LUX)
        assert note == ""

    async def test_no_note_when_the_field_is_empty(self, hass):
        hass.states.async_set(LUX, "25769")
        note = _condition_note(hass, _area(**{A_ON: 60000, A_OFF: ""}), "a", LUX)
        assert note == ""

    async def test_no_note_for_an_inverted_slot(self, hass):
        """Frost fragt "kaelter als" – dort ist 0 als Aufhebepunkt normal."""
        temp = "sensor.wetterstation_temperature"
        hass.states.async_set(temp, "3.5")
        area = {
            CONF_AREA_ID: "living",
            A_ENTITY: temp,
            A_ON: -2,
            A_OFF: 0,
            sun_condition_invert_key("a"): True,
        }
        assert _condition_note(hass, area, "a", temp) == ""
