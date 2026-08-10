"""Die zweite Forum-Runde vom 08.08.2026 – heinzies Fensterkontakt.

Zwei getrennte Ursachen, beide für sich allein schon ausreichend, dass gar
nichts passiert:

* Im Formular ist „open" als Zustand für „offen" wählbar. Ein `binary_sensor`
  meldet aber nur `on` oder `off`, also traf das nie zu und der Kontakt galt
  dauerhaft als geschlossen.
* Selbst mit passendem Zustand reagierte der Fensterkontakt nicht, solange die
  Beschattung den Rollladen auf halber Höhe hielt: die Prüfung liess nur einen
  (nahezu) geschlossenen Rollladen durch. Die Rangfolge lautet aber
  Fensterkontakt > Beschattung > Lüften.
"""

from __future__ import annotations

from unittest.mock import patch

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
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_ENTITY_ID,
    CONF_WINDOW_TILTED_ENTITY_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import set_cover_sun_protected
from custom_components.shutter_pilot.window_helper import get_window_state

COVER = "cover.terrasse"
WINDOW = "binary_sensor.fensterkontakt_garage_geschlossen_contact"

AREA = {
    CONF_AREA_ID: "living",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
}


# --- 1: „open" an einem binary_sensor -----------------------------------------


class TestBinarySensorOpenSynonyms:
    """heinzies Einstellung: Zustand „offen" = `open`, Kontakt meldet `on`."""

    def _shutter(self, **overrides) -> dict:
        shutter = {
            CONF_WINDOW_ENTITY_ID: "binary_sensor.win",
            CONF_WINDOW_OPEN_STATE: "open",
            CONF_WINDOW_TILTED_STATE: "none",
        }
        shutter.update(overrides)
        return shutter

    @pytest.mark.parametrize("configured", ["open", "offen", "true", "1", "on"])
    async def test_open_words_all_match_on(self, hass, configured):
        hass.states.async_set("binary_sensor.win", "on")
        assert (
            get_window_state(
                hass, self._shutter(**{CONF_WINDOW_OPEN_STATE: configured})
            )
            == "open"
        )

    @pytest.mark.parametrize("configured", ["open", "on"])
    async def test_off_still_means_closed(self, hass, configured):
        hass.states.async_set("binary_sensor.win", "off")
        assert (
            get_window_state(
                hass, self._shutter(**{CONF_WINDOW_OPEN_STATE: configured})
            )
            == "closed"
        )

    async def test_inverted_contact_can_use_off(self, hass):
        """Ein „geschlossen"-Kontakt meldet `off`, wenn das Fenster offen ist."""
        hass.states.async_set("binary_sensor.win", "off")
        assert (
            get_window_state(hass, self._shutter(**{CONF_WINDOW_OPEN_STATE: "off"}))
            == "open"
        )
        hass.states.async_set("binary_sensor.win", "on")
        assert (
            get_window_state(hass, self._shutter(**{CONF_WINDOW_OPEN_STATE: "off"}))
            == "closed"
        )

    async def test_tilted_word_still_only_matches_itself(self, hass):
        """„tilted" ist kein Synonym von on/off und darf keins werden."""
        hass.states.async_set("binary_sensor.win", "on")
        assert (
            get_window_state(
                hass, self._shutter(**{CONF_WINDOW_TILTED_STATE: "tilted"})
            )
            == "open"
        )
        hass.states.async_set("binary_sensor.win", "tilted")
        assert (
            get_window_state(
                hass, self._shutter(**{CONF_WINDOW_TILTED_STATE: "tilted"})
            )
            == "tilted"
        )

    async def test_separate_tilt_contact_reads_open_too(self, hass):
        hass.states.async_set("binary_sensor.win", "on")
        hass.states.async_set("binary_sensor.win_tilt", "on")
        shutter = self._shutter(
            **{
                CONF_WINDOW_TILTED_ENTITY_ID: "binary_sensor.win_tilt",
                CONF_WINDOW_TILTED_ENTITY_STATE: "open",
            }
        )
        assert get_window_state(hass, shutter) == "tilted"


# --- 2: der Kontakt erreicht den beschatteten Rollladen ----------------------


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Terrasse",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "none",
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_WHEN_WINDOW_TILTED: 98,
        CONF_POSITION_WHEN_WINDOW_OPEN: 97,
    }
    shutter.update(overrides)
    return shutter


async def _setup(hass, cover_position: int, shutter: dict | None = None):
    hass.states.async_set(
        COVER, "open", {"current_position": cover_position, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "off")
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [AREA], CONF_SHUTTERS: [shutter or _shutter()]},
    )
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry, hass.data[DOMAIN][config_entry.entry_id]


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


class TestShadedShutterYieldsToTheWindow:
    """Der Rollladen steht auf Beschattung, das Fenster geht auf."""

    async def test_shaded_shutter_drives_to_the_window_position(
        self, hass, cover_calls
    ):
        _, data = await _setup(hass, cover_position=25)
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        # Ohne Kipp-Zustand ist der Kontakt zweiwertig, es gilt die
        # Lüftungsposition – nicht die 97 % aus dem Offen-Feld.
        assert [c.data["position"] for c in cover_calls] == [98]
        assert data["trigger_heights"][COVER] == 25

    async def test_closing_the_window_puts_the_shading_back(self, hass, cover_calls):
        _, data = await _setup(hass, cover_position=25)
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        hass.states.async_set(
            COVER, "open", {"current_position": 98, "supported_features": 15}
        )
        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()

        assert [c.data["position"] for c in cover_calls] == [98, 25]

    async def test_an_open_shutter_is_still_left_alone(self, hass, cover_calls):
        """Der Grund für die Prüfung bleibt bestehen: tagsüber nicht anfassen."""
        _, data = await _setup(hass, cover_position=100)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert cover_calls == []


# --- heinzies Konfiguration aus der Diagnose-Datei, unveraendert -------------


class TestHeinziesSetup:
    """`cover.buro`: beschattet auf 80 %, Kontakt „open" an einem binary_sensor.

    Beide Fehler treffen hier zusammen. Der Test faehrt seine Werte 1:1, damit
    die Antwort im Forum belegt ist und nicht geschaetzt.
    """

    def _buero(self) -> dict:
        return _shutter(
            **{
                CONF_NAME: "Buero",
                CONF_COVER_ENTITY_ID: COVER,
                CONF_WINDOW_ENTITY_ID: WINDOW,
                CONF_WINDOW_OPEN_STATE: "open",   # er hat „open" gewaehlt
                CONF_WINDOW_TILTED_STATE: "none",
                CONF_POSITION_WHEN_WINDOW_OPEN: 97,
                CONF_POSITION_WHEN_WINDOW_TILTED: 98,
                CONF_WINDOW_CLOSE_DEBOUNCE: 0,
            }
        )

    async def test_the_whole_cycle_runs(self, hass, cover_calls):
        hass.states.async_set(
            COVER, "open", {"current_position": 80, "supported_features": 15}
        )
        hass.states.async_set(WINDOW, "off")
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={CONF_AREAS: [AREA], CONF_SHUTTERS: [self._buero()]},
        )
        config_entry.add_to_hass(hass)
        with patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
        data = hass.data[DOMAIN][config_entry.entry_id]
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        hass.states.async_set(
            COVER, "open", {"current_position": 98, "supported_features": 15}
        )
        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()

        # 98, nicht 97: ohne Kipp-Zustand gilt die Kipp-Position fuer beides.
        # Danach zurueck auf die Beschattungsposition, von der er kam.
        assert [c.data["position"] for c in cover_calls] == [98, 80]


# --- Wolfs Terrassentuer, 10.08.2026 ----------------------------------------


class TestLockProtectionOnTheWindowTrigger:
    """Aussperrschutz an, Kipp-Position darunter – wer gewinnt?

    Der Fenstertrigger ist der einzige automatisierte Fahrweg, der
    ausschliesslich *bei offenem Fenster* faehrt, und ausgerechnet er fuhr
    seine Zielposition ungefiltert. Eine Kipp-Position unterhalb der
    Mindesthoehe schloss den Rollladen damit vor der offenen Terrassentuer –
    genau der Fall, fuer den es die Einstellung gibt.
    """

    def _terrassentuer(self, **overrides) -> dict:
        shutter = _shutter(
            **{
                CONF_POSITION_WHEN_WINDOW_TILTED: 0,
                CONF_POSITION_WHEN_WINDOW_OPEN: 100,
                CONF_LOCK_PROTECTION: True,
                CONF_MIN_POSITION_WHEN_OPEN: 90,
            }
        )
        shutter.update(overrides)
        return shutter

    async def test_position_below_the_minimum_is_capped(self, hass, cover_calls):
        _, data = await _setup(
            hass, cover_position=50, shutter=self._terrassentuer()
        )
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert [c.data["position"] for c in cover_calls] == [90]

    async def test_a_position_above_the_minimum_is_left_alone(
        self, hass, cover_calls
    ):
        _, data = await _setup(
            hass,
            cover_position=50,
            shutter=self._terrassentuer(**{CONF_POSITION_WHEN_WINDOW_TILTED: 95}),
        )
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert [c.data["position"] for c in cover_calls] == [95]

    async def test_without_lock_protection_nothing_changes(self, hass, cover_calls):
        """Ohne Aussperrschutz bleibt es beim eingestellten Wert."""
        _, data = await _setup(
            hass,
            cover_position=50,
            shutter=self._terrassentuer(**{CONF_LOCK_PROTECTION: False}),
        )
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert [c.data["position"] for c in cover_calls] == [0]

    async def test_the_restore_height_is_still_the_one_from_before(
        self, hass, cover_calls
    ):
        """Die Rueckfahrhoehe ist die Beschattungsposition, nicht die gekappte."""
        _, data = await _setup(
            hass, cover_position=50, shutter=self._terrassentuer()
        )
        set_cover_sun_protected(data, COVER, True)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        assert data["trigger_heights"][COVER] == 50

        hass.states.async_set(
            COVER, "open", {"current_position": 90, "supported_features": 15}
        )
        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()

        assert [c.data["position"] for c in cover_calls] == [90, 50]
