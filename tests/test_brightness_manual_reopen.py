"""Ein von Hand geoeffneter Rollladen bleibt im Helligkeitsmodus abends offen.

Linos (community.simon42.com/90112/167): alle Rollladen abends ordnungsgemaess
geschlossen, einer wird per Wandschalter geoeffnet, kurz darauf schliesst
Shutter Pilot ihn wieder. Nachgerechnet: die Handfahrt nimmt den Rollladen
ueber note_manual_position() aus `covers_driven_down` - richtig so, sonst
wuerde ein morgens nie gefahrener Rollladen abends uebersprungen (2.17.0).
Im Zeit- und Sonnenmodus ist die Abendfahrt danach vorbei, ein Ereignis.
Im Helligkeitsmodus ist sie ein Pegel: `_run_down` lief bei *jeder*
Sensormeldung unter der Schwelle erneut und fand den Rollladen wieder als
"nicht unten" vor.

Jetzt faehrt die Helligkeit einen Rollladen je Dunkel-Episode nur einmal zu.
Eine Episode beginnt, wenn die Schwelle unterschritten wird, und endet, wenn
sie wieder ueberschritten wird oder das Zeitfenster schliesst - genau das,
was `lux_hold` schon als "Frist von vorn" kennt. bjoergs Fall bleibt damit
erhalten: nach einem Ausreisser am Nachmittag (Episode 1) wird es wieder
hell, und die echte Daemmerung (Episode 2) faehrt die von Hand geoeffneten
Rollladen erneut zu.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.brightness import setup_brightness_listener
from custom_components.shutter_pilot.const import (
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_LUX_HOLD,
    CONF_AREA_MODE,
    CONF_AREA_UP_ID,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_DOWN_TO,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WE_UP_TO,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_SHUTTERS,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import note_manual_position

COVER = "cover.wohnzi_re"
COVER_B = "cover.wohnzi_li"
SENSOR = "sensor.lichtsensor_garten"

SHUTTER = {
    CONF_COVER_ENTITY_ID: COVER,
    CONF_AREA_UP_ID: "wohnzimmer",
    CONF_AREA_DOWN_ID: "wohnzimmer",
    CONF_POSITION_OPEN: 100,
    CONF_POSITION_CLOSED: 0,
}
SHUTTER_B = {**SHUTTER, CONF_COVER_ENTITY_ID: COVER_B}


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "wohnzimmer",
        CONF_AREA_MODE: AREA_MODE_BRIGHTNESS,
        CONF_AREA_BRIGHTNESS_SENSOR: SENSOR,
        CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD: 40,
        CONF_AREA_BRIGHTNESS_UP_THRESHOLD: 20,
        # Runter ganztags, damit die Wanduhr nicht mitspielt (wie in
        # test_brightness_lux_hold.py); hoch nur in einer Minute nachts, damit
        # die Hochfahrt hier nicht dazwischenfunkt - es geht um die Abendfahrt.
        CONF_AREA_W_UP_FROM: "03:00", CONF_AREA_W_UP_TO: "03:01",
        CONF_AREA_W_DOWN_FROM: "00:00", CONF_AREA_W_DOWN_TO: "23:59",
        CONF_AREA_WE_UP_FROM: "03:00", CONF_AREA_WE_UP_TO: "03:01",
        CONF_AREA_WE_DOWN_FROM: "00:00", CONF_AREA_WE_DOWN_TO: "23:59",
    }
    area.update(overrides)
    return area


async def _setup(hass, area: dict, shutters: list[dict] | None = None):
    hass.states.async_set(SENSOR, "5000")
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={CONF_AREAS: [area], CONF_SHUTTERS: shutters or [SHUTTER]},
    )
    entry.add_to_hass(hass)
    data: dict = hass.data.setdefault(DOMAIN, {}).setdefault(
        entry.entry_id, {"master_enabled": True}
    )
    await setup_brightness_listener(hass, entry)
    return entry, data


@pytest.fixture
def clock(monkeypatch):
    state = {"t": 1000.0}
    monkeypatch.setattr(
        "custom_components.shutter_pilot.brightness.time_mod.monotonic",
        lambda: state["t"],
    )
    return state


@pytest.fixture
def drive():
    with patch(
        "custom_components.shutter_pilot.brightness.set_cover_position",
        new=AsyncMock(return_value=True),
    ) as mock:
        yield mock


async def _lux(hass, value: float) -> None:
    hass.states.async_set(SENSOR, str(value))
    await hass.async_block_till_done()


def _drives(drive) -> list[tuple[str, float]]:
    return [(c.args[2], c.args[3]) for c in drive.await_args_list]


def _hand_open(data, shutter: dict) -> None:
    """Was cover_tracker bei einer erkannten Fremdfahrt auf 100 % verbucht."""
    note_manual_position(data, shutter, 100)


class TestHandOpenAfterTheEveningClose:
    async def test_stays_open_while_it_stays_dark(self, hass, drive, clock):
        """Linos: Wandschalter nach der Abendfahrt, naechste Lux-Meldung."""
        _, data = await _setup(hass, _area())
        await _lux(hass, 10)
        assert _drives(drive) == [(COVER, 0)], "die Abendfahrt selbst"

        _hand_open(data, SHUTTER)
        assert COVER not in data["covers_driven_down"], (
            "Vorbedingung: die Handfahrt hat den Unten-Merker aufgehoben"
        )

        clock["t"] += 90
        await _lux(hass, 8)
        clock["t"] += 90
        await _lux(hass, 12)
        assert _drives(drive) == [(COVER, 0)], (
            "BUG waere: jede weitere Meldung unter der Schwelle faehrt den von "
            "Hand geoeffneten Rollladen wieder zu"
        )

    async def test_a_new_dark_episode_closes_again(self, hass, drive, clock):
        """bjoerg: Ausreisser am Nachmittag, von Hand geoeffnet, echte
        Daemmerung spaeter - die muss wieder zufahren."""
        _, data = await _setup(hass, _area())
        await _lux(hass, 0)            # der 7-Sekunden-Ausreisser
        assert _drives(drive) == [(COVER, 0)]
        clock["t"] += 7
        await _lux(hass, 21963)        # hell wie zuvor
        _hand_open(data, SHUTTER)      # ueber das Dashboard wieder auf

        clock["t"] += 4 * 3600
        await _lux(hass, 15)           # echte Daemmerung
        assert _drives(drive) == [(COVER, 0), (COVER, 0)], (
            "eine neue Dunkel-Episode ist eine neue Abendfahrt"
        )

    async def test_with_a_hold_the_episode_starts_at_the_first_reading(
        self, hass, drive, clock
    ):
        """Mit lux_hold: die Frist und die Episode sind derselbe Zaehler."""
        _, data = await _setup(hass, _area(**{CONF_AREA_LUX_HOLD: 2}))
        await _lux(hass, 10)
        clock["t"] += 130
        await _lux(hass, 9)
        assert _drives(drive) == [(COVER, 0)], "nach der Frist: zu"

        _hand_open(data, SHUTTER)
        clock["t"] += 60
        await _lux(hass, 5)
        assert _drives(drive) == [(COVER, 0)], "bleibt offen, gleiche Episode"

        clock["t"] += 60
        await _lux(hass, 5000)         # Episode zu Ende
        clock["t"] += 60
        await _lux(hass, 10)
        clock["t"] += 130
        await _lux(hass, 9)
        assert _drives(drive) == [(COVER, 0), (COVER, 0)], (
            "neue Episode, neue Frist, neue Fahrt"
        )


class TestHandCloseInTheMorningWindow:
    """Spiegelbild: eine Handfahrt auf 0 % gilt laut manual_position_is_a_close()
    nicht als Uebersteuerung - im Hochfahr-Fenster oeffnete die naechste
    Lux-Meldung den eben von Hand geschlossenen Rollladen wieder."""

    def _morning(self) -> dict:
        return _area(**{
            CONF_AREA_W_UP_FROM: "00:00", CONF_AREA_W_UP_TO: "23:59",
            CONF_AREA_WE_UP_FROM: "00:00", CONF_AREA_WE_UP_TO: "23:59",
            CONF_AREA_W_DOWN_FROM: "03:00", CONF_AREA_W_DOWN_TO: "03:01",
            CONF_AREA_WE_DOWN_FROM: "03:00", CONF_AREA_WE_DOWN_TO: "03:01",
        })

    async def test_stays_closed_while_it_stays_bright(self, hass, drive, clock):
        _, data = await _setup(hass, self._morning())
        data["covers_driven_down"].add(COVER)
        await _lux(hass, 500)
        assert _drives(drive) == [(COVER, 100)], "die Morgenfahrt selbst"

        note_manual_position(data, SHUTTER, 0)   # laenger schlafen
        clock["t"] += 90
        await _lux(hass, 600)
        assert _drives(drive) == [(COVER, 100)], (
            "BUG waere: die naechste helle Meldung oeffnet den von Hand "
            "geschlossenen Rollladen wieder"
        )

    async def test_a_new_bright_episode_opens_again(self, hass, drive, clock):
        _, data = await _setup(hass, self._morning())
        data["covers_driven_down"].add(COVER)
        await _lux(hass, 500)
        note_manual_position(data, SHUTTER, 0)
        clock["t"] += 60
        await _lux(hass, 5)            # dunkel dazwischen: Episode zu Ende
        clock["t"] += 60
        await _lux(hass, 500)
        assert _drives(drive) == [(COVER, 100), (COVER, 100)]


class TestOnlyTheAlreadyClosedOnesAreSpared:
    async def test_a_shutter_enabled_later_still_closes_this_evening(
        self, hass, drive, clock, monkeypatch
    ):
        """Der Merker gilt je Rollladen, nicht je Bereich: was die Episode
        noch nie gefahren hat (Automatik war aus), faehrt beim naechsten
        Wert - wie bisher."""
        enabled = {COVER: True, COVER_B: False}
        monkeypatch.setattr(
            "custom_components.shutter_pilot.brightness.is_shutter_automation_enabled",
            lambda hass, entry, s: enabled[s[CONF_COVER_ENTITY_ID]],
        )
        _, data = await _setup(hass, _area(), [SHUTTER, SHUTTER_B])
        await _lux(hass, 10)
        assert _drives(drive) == [(COVER, 0)]

        enabled[COVER_B] = True
        clock["t"] += 60
        await _lux(hass, 9)
        assert _drives(drive) == [(COVER, 0), (COVER_B, 0)]

    async def test_a_hand_close_in_daylight_is_still_reclosed_at_dusk(
        self, hass, drive, clock
    ):
        """Von Hand zu um 14 Uhr, von Hand auf um 15 Uhr, Daemmerung um 19 Uhr:
        die Abendfahrt kennt diesen Rollladen noch nicht und faehrt ihn."""
        _, data = await _setup(hass, _area())
        note_manual_position(data, SHUTTER, 0)
        _hand_open(data, SHUTTER)
        await _lux(hass, 10)
        assert _drives(drive) == [(COVER, 0)]
