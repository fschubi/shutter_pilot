"""Der Aussperrschutz und das gekippte Fenster.

bjoerg im Forum, nachdem er seinen Fenstergriff auf eine Entitaet mit drei
echten Zustaenden umgestellt hatte: „Aber die Position für tilted wird nicht
angefahren."

Nachgerechnet mit seinen Werten – Mindesthoehe 95, Kipp-Position 30 – kam
heraus: der Zustand wird richtig erkannt und die Kipp-Position richtig
bestimmt, und dann klemmt der Aussperrschutz sie auf 95 hoch. Eine
Kipp-Position unterhalb der Mindesthoehe war damit grundsaetzlich
unerreichbar: gespeichert, im Formular sichtbar, wirkungslos.

Der Schutz gilt jetzt nur noch bei *offenem* Fenster. Durch einen Kippspalt
steigt niemand – dort gibt es den Fall nicht, gegen den er schuetzt.
"""

from __future__ import annotations

import pytest

from custom_components.shutter_pilot.const import (
    CONF_COVER_ENTITY_ID,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
)
from custom_components.shutter_pilot.window_helper import (
    get_effective_close_position,
    get_position_for_window_state,
    get_window_state,
)

GRIFF = "sensor.fenstergriff_balkon"
KONTAKT = "binary_sensor.fensterkontakt"


def _three_state(**over) -> dict:
    """bjoergs Aufbau: ein Griff mit open / tilted / closed."""
    shutter = {
        CONF_COVER_ENTITY_ID: "cover.rollladen_schlafzimmer_og",
        CONF_WINDOW_ENTITY_ID: GRIFF,
        CONF_WINDOW_OPEN_STATE: "open",
        CONF_WINDOW_TILTED_STATE: "tilted",
        CONF_LOCK_PROTECTION: True,
        CONF_MIN_POSITION_WHEN_OPEN: 95,
        CONF_POSITION_WHEN_WINDOW_OPEN: 95,
        CONF_POSITION_WHEN_WINDOW_TILTED: 30,
    }
    shutter.update(over)
    return shutter


def _two_state(**over) -> dict:
    """Wolfs Aufbau aus 2.10.2: zweiwertiger Kontakt, kein Kipp-Zustand."""
    shutter = {
        CONF_COVER_ENTITY_ID: "cover.kueche_vorne",
        CONF_WINDOW_ENTITY_ID: KONTAKT,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "none",
        CONF_LOCK_PROTECTION: True,
        CONF_MIN_POSITION_WHEN_OPEN: 90,
        CONF_POSITION_WHEN_WINDOW_TILTED: 0,
    }
    shutter.update(over)
    return shutter


class TestTiltedWindow:
    async def test_the_tilt_position_is_actually_driven(self, hass):
        """bjoergs Fall: 30 % muessen 30 % bleiben."""
        shutter = _three_state()
        hass.states.async_set(GRIFF, "tilted")

        assert get_window_state(hass, shutter) == "tilted"
        target = get_position_for_window_state(shutter, "tilted")
        assert target == 30
        assert get_effective_close_position(hass, shutter, target) == 30

    async def test_a_wide_open_window_is_still_capped(self, hass):
        """Die Gegenrichtung – dafuer ist der Aussperrschutz da."""
        shutter = _three_state()
        hass.states.async_set(GRIFF, "open")

        assert get_window_state(hass, shutter) == "open"
        assert get_effective_close_position(hass, shutter, 0) == 95

    async def test_a_closed_window_is_never_capped(self, hass):
        shutter = _three_state()
        hass.states.async_set(GRIFF, "closed")
        assert get_effective_close_position(hass, shutter, 0) == 0

    async def test_a_tilt_position_above_the_minimum_is_untouched(self, hass):
        """Wer die Kipp-Position hoeher legt, merkt von der Aenderung nichts."""
        shutter = _three_state(**{CONF_POSITION_WHEN_WINDOW_TILTED: 98})
        hass.states.async_set(GRIFF, "tilted")
        assert get_effective_close_position(hass, shutter, 98) == 98


class TestTheTwoStateContactKeepsItsCap:
    """Wolfs Fall aus 2.10.2 darf sich nicht aendern.

    Ein zweiwertiger Kontakt meldet „open", nie „tilted" – die Klemme greift
    dort also weiter, und die Terrassentuer bleibt frei.
    """

    async def test_an_open_two_state_contact_is_capped(self, hass):
        shutter = _two_state()
        hass.states.async_set(KONTAKT, "on")

        assert get_window_state(hass, shutter) == "open"
        target = get_position_for_window_state(shutter, "open")
        assert target == 0, "zweiwertig: gefahren wird die Kipp-Position"
        assert get_effective_close_position(hass, shutter, target) == 90

    async def test_a_closed_two_state_contact_is_free(self, hass):
        shutter = _two_state()
        hass.states.async_set(KONTAKT, "off")
        assert get_effective_close_position(hass, shutter, 0) == 0


class TestWithoutLockProtection:
    async def test_nothing_is_capped_at_all(self, hass):
        shutter = _three_state(**{CONF_LOCK_PROTECTION: False})
        for state in ("open", "tilted", "closed"):
            hass.states.async_set(GRIFF, state)
            assert get_effective_close_position(hass, shutter, 0) == 0
