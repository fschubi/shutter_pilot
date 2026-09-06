"""Der Fenstertrigger merkte sich nach einer nachgeholten Fahrt eine
veraltete Rueckfahrhoehe.

Ablauf, der den Fehler ausmacht:

1. Ein Rollladen wird beschattet.
2. Das Fenster geht auf, waehrend beschattet wird - der Fenstertrigger
   greift (er darf das, weil "beschattet" den Tagesschutz aushebelt) und
   merkt sich die Beschattungshoehe als Rueckfahrziel.
3. Der Abend kommt, das Fenster ist noch offen: die volle Abwaertsfahrt wird
   vorgemerkt (drive_after_close_pending), statt sofort zu fahren.
4. Das Fenster schliesst: die vorgemerkte Fahrt greift und faehrt korrekt
   ganz zu. `_apply_window_closed()` kehrte an dieser Stelle aber zurueck,
   *ohne* die Zyklus-Merker (trigger_actions/trigger_heights) zu loeschen.
5. Spaeter in der Nacht wird kurz gelueftet (Fenster auf, dann wieder zu) -
   ohne jeden Bezug zur Beschattung von vorhin. Weil der Zyklus faelschlich
   noch als aktiv galt, wurde die *alte* Beschattungshoehe nicht durch die
   aktuell richtige (geschlossene) Position ersetzt - der Rollladen fuhr
   beim zweiten Schliessen mitten in der Nacht auf die alte
   Beschattungshoehe zurueck, statt zu bleiben, wo er war.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import (
    remember_drive_after_close,
    set_cover_sun_protected,
)

COVER = "cover.schlafzimmer_stale"
WINDOW = "binary_sensor.schlafzimmer_fenster_stale"

SHADE_POS = 40  # Beschattungsposition
VENT_POS = 70   # Lueftungsposition bei offenem Fenster (2-Zustand-Kontakt)

AREA = {
    CONF_AREA_ID: "schlafzimmer",
    CONF_AREA_NAME: "Schlafzimmer",
    CONF_AREA_MODE: AREA_MODE_NONE,
}


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Schlafzimmer",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "none",  # 2-Zustand-Kontakt
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_SUN_PROTECT: SHADE_POS,
        CONF_POSITION_WHEN_WINDOW_TILTED: VENT_POS,
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
        CONF_DRIVE_AFTER_CLOSE: True,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture(autouse=True)
def _fast_startup(monkeypatch):
    from custom_components.shutter_pilot import cover_tracker

    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def cover_calls(hass):
    """Fahrten mitschreiben und die Position tatsaechlich im State nachziehen."""
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
    return [c.data["position"] for c in calls]


async def _setup(hass):
    hass.states.async_set(
        COVER, "open", {"current_position": SHADE_POS, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "off")  # Fenster zu

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [_shutter()]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


class TestDeferredCloseClearsTheWindowCycle:
    async def test_a_later_unrelated_airing_does_not_reopen_the_shutter(
        self, hass, cover_calls
    ):
        entry, data = await _setup(hass)

        # 1) Beschattet, dann geht das Fenster auf: der Trigger greift und
        #    merkt sich die Beschattungshoehe als Rueckfahrziel.
        set_cover_sun_protected(data, COVER, True)
        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert _positions(cover_calls) == [VENT_POS]
        assert data["trigger_actions"].get(COVER) == "triggered"
        assert data["trigger_heights"].get(COVER) == SHADE_POS
        cover_calls.clear()

        # 2) Abend, Fenster noch offen: die Abwaertsfahrt wird vorgemerkt.
        shutter = entry.options[CONF_SHUTTERS][0]
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=0, tilt=None, reason="Schedule down (test)", shutter=shutter,
        )
        assert COVER in data["drive_after_close_pending"]

        # 3) Fenster schliesst: die vorgemerkte Fahrt greift, Rollladen -> 0.
        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()

        assert _positions(cover_calls) == [0], "die nachgeholte Fahrt muss jetzt laufen"
        assert COVER not in data["drive_after_close_pending"]

        # Der Zyklus muss sauber abgeschlossen sein - die nachgeholte Fahrt
        # *ist* die Restaurierung.
        assert data["trigger_actions"].get(COVER) is None
        assert data["trigger_heights"].get(COVER) is None
        cover_calls.clear()

        # 4) Spaeter in der Nacht: kurz lueften, ohne Bezug zur Beschattung.
        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        cover_calls.clear()

        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()

        # Der Rollladen darf nicht auf die alte Beschattungshoehe
        # zurueckfahren - er muss auf seiner aktuellen, korrekten
        # (geschlossenen) Position bleiben.
        assert SHADE_POS not in _positions(cover_calls), (
            "Der Rollladen darf nicht auf die veraltete Beschattungshoehe zurueckfahren"
        )
        assert _positions(cover_calls) == [0]
