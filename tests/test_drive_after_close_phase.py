"""heinzies dritte Meldung: der nachgeholte Rollladen blieb morgens unten.

Sein Ablauf, Schritt für Schritt:

1. abends fahren alle Rollläden runter
2. einer bleibt oben, weil sein Fenster offen ist – die Fahrt wird vorgemerkt
3. Fenster zu, der Rollladen holt die Fahrt nach
4. am nächsten Morgen fahren alle hoch – **nur dieser nicht**

Die Ursache liegt in Schritt 2. Der Nachhol-Zweig verlässt die Schleife mit
`continue`, *bevor* die Phasensperren gesetzt werden. Der Rollladen bleibt
damit in `covers_driven_up` vom Morgen stehen, und `_run_up_async` filtert
genau danach. Dass die Fahrt in Schritt 3 tatsächlich stattfand, sieht der
Scheduler nicht – der Fensterkontakt pflegt diese Merker nicht.

`clear_covers_driven_for_direction()` würde das auffangen, tut es aber nicht:
die Funktion **ersetzt** das Set in `data`, während Scheduler und
Helligkeitsmodus eine Referenz auf das ursprüngliche Set halten.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)

OFFEN = "cover.buero"          # Fenster auf, wird vorgemerkt
NORMAL = "cover.flur"          # Vergleichsrollladen ohne Fenster
WINDOW = "binary_sensor.buero_fenster"

AREA = {
    CONF_AREA_ID: "living",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
}


def _shutter(cover: str, **overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: cover,
        CONF_NAME: cover.split(".")[-1],
        "area_up_id": "living",
        "area_down_id": "living",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


@pytest.fixture
async def entry(hass, cover_calls):
    for cover in (OFFEN, NORMAL):
        hass.states.async_set(
            cover, "open", {"current_position": 100, "supported_features": 15}
        )
    hass.states.async_set(WINDOW, "on")  # Fenster steht offen
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={
            CONF_AREAS: [AREA],
            CONF_SHUTTERS: [
                _shutter(
                    OFFEN,
                    **{
                        CONF_DRIVE_AFTER_CLOSE: True,
                        CONF_WINDOW_ENTITY_ID: WINDOW,
                        CONF_WINDOW_OPEN_STATE: "on",
                        CONF_WINDOW_TILTED_STATE: "none",
                    },
                ),
                _shutter(NORMAL),
            ],
        },
    )
    config_entry.add_to_hass(hass)
    from unittest.mock import patch

    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry


async def _tick(hass, entry, when: datetime) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    data["_minute_callbacks"]["scheduler"](when)
    await hass.async_block_till_done()


def _driven(calls) -> list[tuple[str, int]]:
    return [(c.data["entity_id"], c.data["position"]) for c in calls]


class TestCatchUpKeepsThePhaseLocks:
    async def test_the_full_two_day_cycle(self, hass, entry, cover_calls):
        """Genau heinzies Ablauf, vier Schritte."""
        data = hass.data[DOMAIN][entry.entry_id]

        # 1) Morgens hoch – beide fahren.
        await _tick(hass, entry, datetime(2026, 8, 8, 7, 0))
        assert sorted(c for c, _ in _driven(cover_calls)) == sorted([NORMAL, OFFEN])
        assert data["covers_driven_up"] == {OFFEN, NORMAL}
        cover_calls.clear()

        # 2) Abends runter – der mit dem offenen Fenster wird vorgemerkt.
        await _tick(hass, entry, datetime(2026, 8, 8, 19, 0))
        assert _driven(cover_calls) == [(NORMAL, 0)], "nur der ohne Fenster fährt"
        assert OFFEN in data["drive_after_close_pending"]
        assert OFFEN not in data["covers_driven_up"], (
            "Die Abwärtsfahrt ist beschlossen – sie steht nur noch aus. "
            "Bleibt der Rollladen als 'heute hochgefahren' vermerkt, "
            "überspringt ihn der nächste Morgen."
        )
        cover_calls.clear()

        # 3) Fenster zu – die Fahrt wird nachgeholt.
        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()
        assert _driven(cover_calls) == [(OFFEN, 0)]
        hass.states.async_set(
            OFFEN, "closed", {"current_position": 0, "supported_features": 15}
        )
        cover_calls.clear()

        # 4) Am nächsten Morgen müssen beide hochfahren.
        await _tick(hass, entry, datetime(2026, 8, 9, 7, 0))
        assert sorted(c for c, _ in _driven(cover_calls)) == sorted([NORMAL, OFFEN])

    async def test_pending_drive_is_not_rewritten_every_tick(self, hass, entry):
        """Der Merker darf nicht bei jedem Durchlauf neu geschrieben werden."""
        data = hass.data[DOMAIN][entry.entry_id]
        await _tick(hass, entry, datetime(2026, 8, 8, 19, 0))
        first = data["drive_after_close_pending"][OFFEN]

        await _tick(hass, entry, datetime(2026, 8, 8, 19, 0))
        assert data["drive_after_close_pending"][OFFEN] is first
