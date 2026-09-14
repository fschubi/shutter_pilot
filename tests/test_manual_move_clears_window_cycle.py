"""Der Rueckfahr-Merker des Fenstertriggers darf keine manuelle Fahrt
ueberleben - und eine Zustandsmeldung ohne Positionswechsel ist keine Fahrt.

c.radi (community.simon42.com/90112/150), zwei Tage nacheinander beobachtet:
Tag 1 faehrt die Automatik den Schlafzimmer-Rollladen morgens hoch, danach
reagiert der Fensterkontakt nicht mehr (richtig). Tag 2 faehrt er ihn von Hand
hoch - und beim Umstellen des Fensters von gekippt auf geschlossen faehrt der
Rollladen wieder herunter. Der Unterschied liegt in
`clear_stale_window_cycle_after_automated_up()`: die automatische Hochfahrt
raeumt den nachts begonnenen Fensterzyklus (`trigger_actions`/
`trigger_heights`, Rueckfahrhoehe 26 %) auf, die erkannte Handfahrt in
`cover_tracker.py` tat das nicht. Dieselbe Fehlerklasse wie 2.22.3
(`forget_drive_after_close` an derselben Stelle): ein Merker, der eine
Handlung ueberlebt, fuer die er nicht gedacht war.

Der zweite Test schuetzt die Stelle selbst: der Bus meldet jede Aenderung am
Zustandsobjekt, etwa einen Funkpegel bei Homematic. Ohne Positionswechsel darf
das weder als Handfahrt gebucht werden noch eine Vormerkung oder den
Fensterzyklus loeschen - sonst wuerde ein zufaelliger RSSI-Wert genau die
Aufraeumarbeiten ausloesen, die hier fuer eine echte Fahrt gebaut sind."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AREA_MODE_NONE,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import remember_drive_after_close
from custom_components.shutter_pilot.position_store import (
    SOURCE_AUTOMATION,
    get_position_store,
)

COVER = "cover.cradi_schlafzimmer_links"
WINDOW = "sensor.cradi_schlafzimmer_fenster_links"

# c.radis Werte: geschlossen ist 26 %, Lueften und Kippen ebenso.
CLOSED = 26


@pytest.fixture(autouse=True)
def _fast_startup(monkeypatch):
    from custom_components.shutter_pilot import cover_tracker

    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def cover_calls(hass):
    calls: list = []

    async def _handler(call):
        calls.append(call)
        position = call.data["position"]
        hass.states.async_set(
            call.data["entity_id"],
            "closed" if position <= 0 else "open",
            {"current_position": position, "supported_features": 15},
        )

    hass.services.async_register("cover", "set_cover_position", _handler)
    return calls


def _positions(calls) -> list[float]:
    return [c.data["position"] for c in calls]


async def _setup(hass):
    hass.states.async_set(
        COVER, "open", {"current_position": CLOSED, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "closed")
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Schlafzimmer Links",
        CONF_AREA_UP_ID: "schlafen",
        CONF_AREA_DOWN_ID: "schlafen",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "open",
        CONF_WINDOW_TILTED_STATE: "tilted",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: CLOSED,
        CONF_POSITION_WHEN_WINDOW_OPEN: CLOSED,
        CONF_POSITION_WHEN_WINDOW_TILTED: CLOSED,
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
    }
    area = {
        CONF_AREA_ID: "schlafen",
        CONF_AREA_NAME: "Schlafen",
        CONF_AREA_MODE: AREA_MODE_NONE,
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


def _hours_pass(data) -> None:
    """Die Karenz der eigenen Fahrt (90 s) ist am Morgen laengst vorbei."""
    data.get("recent_automation_covers", {}).clear()
    data.get("pending_automation_covers", set()).clear()


async def _report(hass, position: float, **extra) -> None:
    hass.states.async_set(
        COVER,
        "open",
        {"current_position": position, "supported_features": 15, **extra},
    )
    await hass.async_block_till_done()


class TestManualUpEndsTheWindowCycle:
    async def test_the_two_days_as_reported(self, hass, cover_calls):
        _entry, data = await _setup(hass)

        # Nacht: Fenster gekippt, Rollladen steht auf 26 (zu) - der
        # Fenstertrigger beginnt einen Zyklus und merkt sich 26 als
        # Rueckfahrhoehe.
        hass.states.async_set(WINDOW, "tilted")
        await hass.async_block_till_done()
        assert data["trigger_actions"].get(COVER) == "triggered"
        assert data["trigger_heights"].get(COVER) == CLOSED

        # Tag 2: morgens von Hand ganz hoch (Taster, HA-Karte).
        _hours_pass(data)
        await _report(hass, 100)
        cover_calls.clear()

        # Fenster von gekippt auf geschlossen.
        hass.states.async_set(WINDOW, "closed")
        await hass.async_block_till_done()

        assert _positions(cover_calls) == [], (
            "der von Hand geoeffnete Rollladen darf beim Schliessen des "
            f"Fensters nicht auf die Nachthoehe zurueck: {_positions(cover_calls)}"
        )
        assert COVER not in data["trigger_actions"]
        assert COVER not in data["trigger_heights"]

    async def test_an_automated_up_still_ends_it_too(self, hass, cover_calls):
        """Tag 1 aus c.radis Bericht - war schon richtig, bleibt es."""
        entry, data = await _setup(hass)
        hass.states.async_set(WINDOW, "tilted")
        await hass.async_block_till_done()
        assert data["trigger_actions"].get(COVER) == "triggered"

        from custom_components.shutter_pilot.helpers import (
            clear_stale_window_cycle_after_automated_up,
            set_cover_position,
        )

        await set_cover_position(hass, entry, COVER, 100, "Brightness up")
        clear_stale_window_cycle_after_automated_up(data, COVER)
        await hass.async_block_till_done()
        cover_calls.clear()

        hass.states.async_set(WINDOW, "closed")
        await hass.async_block_till_done()
        assert _positions(cover_calls) == []


class TestAStateUpdateWithoutAMoveIsNotAManualMove:
    async def test_it_keeps_the_pending_drive_and_the_window_cycle(
        self, hass, cover_calls
    ):
        entry, data = await _setup(hass)
        shutter = entry.options[CONF_SHUTTERS][0]

        # Nacht wie oben: Fensterzyklus laeuft, dazu eine vorgemerkte
        # Nachhol-Fahrt (so hinterlaesst brightness.py::_run_down ein offenes
        # Fenster zur Schliesszeit).
        hass.states.async_set(WINDOW, "tilted")
        await hass.async_block_till_done()
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=CLOSED, tilt=None, reason="Brightness down", shutter=shutter,
        )
        assert COVER in data["drive_after_close_pending"]
        assert data["trigger_actions"].get(COVER) == "triggered"
        store = get_position_store(hass, entry.entry_id)
        await hass.async_block_till_done()
        assert (store.get_record(COVER) or {}).get("source") == SOURCE_AUTOMATION

        # Stunden spaeter meldet der Antrieb sich - mit demselben Stand, nur
        # ein Attribut hat sich geaendert (Funkpegel, Batterie, ...).
        _hours_pass(data)
        await _report(hass, CLOSED, rssi_device_value=-71)

        assert COVER in data["drive_after_close_pending"], (
            "ohne Positionswechsel gab es keine Handfahrt, die die Vormerkung "
            "ueberholt haette"
        )
        assert data["trigger_actions"].get(COVER) == "triggered"
        assert (store.get_record(COVER) or {}).get("source") == SOURCE_AUTOMATION, (
            "die Quelle im Speicher darf nicht auf 'manual' kippen - die "
            "naechste Automatikfahrt laese das als Uebersteuerung"
        )

    async def test_a_real_move_still_counts(self, hass, cover_calls):
        """Gegenprobe: dieselbe Meldung mit neuer Position ist eine Handfahrt."""
        entry, data = await _setup(hass)
        shutter = entry.options[CONF_SHUTTERS][0]
        hass.states.async_set(WINDOW, "tilted")
        await hass.async_block_till_done()
        remember_drive_after_close(
            hass, entry, data, COVER,
            position=CLOSED, tilt=None, reason="Brightness down", shutter=shutter,
        )
        _hours_pass(data)
        await _report(hass, 100, rssi_device_value=-71)
        assert COVER not in data["drive_after_close_pending"]
        assert COVER not in data["trigger_actions"]
