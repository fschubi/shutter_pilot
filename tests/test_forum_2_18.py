"""Forum-Runde vom 29.08.2026 – pcsv17, Smons/Linos, Wolf und bjoerg.

Vier Meldungen, ein gemeinsamer Kern: der Fensterkontakt erreichte nur den
(nahezu) geschlossenen Rollladen. Die Prüfung war richtungsblind – sie soll
verhindern, dass ein offenes Fenster einen offenen Rollladen herunterzieht,
sperrte damit aber auch den Aussperrschutz aus, der als einziger auf diesem
Weg nach *oben* fährt. Genau das ist der Haken, wegen dem jemand ihn setzt.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_AWNING_TRACK_ENABLED,
    CONF_BLIND_DRIVE,
    CONF_COVER_ENTITY_ID,
    CONF_DEVICE_KIND,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_MY_POSITION_ENTITY,
    CONF_MY_POSITION_PCT,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_WINDOW_VENT_WHILE_OPEN,
    DOMAIN,
    KIND_AWNING,
)

COVER = "cover.terrassentuer"
WINDOW = "binary_sensor.tuerkontakt_terrasse"

AREA = {
    CONF_AREA_ID: "living",
    CONF_AREA_NAME: "Wohnbereich",
    CONF_AREA_MODE: AREA_MODE_TIME,
    CONF_AREA_TIME_UP: "07:00",
    CONF_AREA_TIME_DOWN: "19:00",
    CONF_AREA_DRIVE_DELAY: 0,
}


def _shutter(**overrides) -> dict:
    """pcsv17s Balkontür: zweiwertiger Kontakt, Aussperrschutz auf 95 %."""
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Terrassentür",
        CONF_AREA_UP_ID: "living",
        CONF_AREA_DOWN_ID: "living",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "none",
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_WHEN_WINDOW_TILTED: 30,
        CONF_POSITION_WHEN_WINDOW_OPEN: 100,
        CONF_LOCK_PROTECTION: True,
        CONF_MIN_POSITION_WHEN_OPEN: 95,
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


# --- 1: pcsv17 – der Aussperrschutz erreicht den halb offenen Rollladen ------


class TestLockProtectionReachesAnOpenShutter:
    """„Wurde das Rollo manuell auf z. B. 45 % gefahren, passiert nichts."""

    async def test_partly_open_shutter_is_raised_to_the_minimum(
        self, hass, cover_calls
    ):
        await _setup(hass, cover_position=45)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        # 30 % Lüftungsposition, vom Aussperrschutz auf 95 % geklemmt – und 95
        # liegt über 45, die Fahrt öffnet also. Genau dafür ist der Haken da.
        assert [c.data["position"] for c in cover_calls] == [95]

    async def test_closing_the_window_restores_the_manual_height(
        self, hass, cover_calls
    ):
        await _setup(hass, cover_position=45)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        hass.states.async_set(COVER, "open", {"current_position": 95})
        hass.states.async_set(WINDOW, "off")
        await hass.async_block_till_done()

        assert [c.data["position"] for c in cover_calls] == [95, 45]

    async def test_open_shutter_is_still_left_alone_without_lock_protection(
        self, hass, cover_calls
    ):
        """Der eigentliche Zweck der Prüfung bleibt: mittags nicht zufahren."""
        await _setup(
            hass,
            cover_position=100,
            shutter=_shutter(**{CONF_LOCK_PROTECTION: False}),
        )

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert cover_calls == []

    async def test_lock_protection_does_not_lower_an_already_higher_shutter(
        self, hass, cover_calls
    ):
        """100 % offen, Mindesthöhe 95: nach unten fahren wäre falsch."""
        await _setup(hass, cover_position=100)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert cover_calls == []

    async def test_closed_shutter_keeps_going_to_the_capped_position(
        self, hass, cover_calls
    ):
        """Der bisherige Weg – aus dem geschlossenen Zustand – bleibt gleich."""
        await _setup(hass, cover_position=0)

        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()

        assert [c.data["position"] for c in cover_calls] == [95]


# --- 2: bjoerg – bei offenem Fenster passierte gar nichts --------------------


async def _tick(hass, entry, when) -> None:
    hass.data[DOMAIN][entry.entry_id]["_minute_callbacks"]["scheduler"](when)
    await hass.async_block_till_done()


class TestVentilationPositionWhileWaiting:
    """„Müsste dann aber nicht die Jalousie auf die Position für gekippt fahren?"""

    def _pending_shutter(self, **overrides) -> dict:
        return _shutter(
            **{
                CONF_DRIVE_AFTER_CLOSE: True,
                CONF_LOCK_PROTECTION: False,
                CONF_POSITION_WHEN_WINDOW_TILTED: 30,
                **overrides,
            }
        )

    async def test_without_the_option_nothing_moves(self, hass, cover_calls):
        entry, data = await _setup(
            hass, cover_position=100, shutter=self._pending_shutter()
        )
        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        # Der erste Tick holt die heute schon vergangene Morgenfahrt nach –
        # sie interessiert hier nicht.
        await _tick(hass, entry, datetime(2026, 8, 29, 7, 0))
        cover_calls.clear()

        await _tick(hass, entry, datetime(2026, 8, 29, 19, 0))
        assert cover_calls == []
        assert COVER in data["drive_after_close_pending"]

    async def test_with_the_option_it_goes_to_the_ventilation_position(
        self, hass, cover_calls
    ):
        entry, data = await _setup(
            hass,
            cover_position=100,
            shutter=self._pending_shutter(**{CONF_WINDOW_VENT_WHILE_OPEN: True}),
        )
        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        # Der erste Tick holt die heute schon vergangene Morgenfahrt nach –
        # sie interessiert hier nicht.
        await _tick(hass, entry, datetime(2026, 8, 29, 7, 0))
        cover_calls.clear()

        await _tick(hass, entry, datetime(2026, 8, 29, 19, 0))
        assert [c.data["position"] for c in cover_calls] == [30]
        # Die volle Fahrt bleibt vorgemerkt – sie ist nur aufgeschoben.
        assert data["drive_after_close_pending"][COVER]["position"] == 0

    async def test_the_lock_protection_still_caps_the_partial_drive(
        self, hass, cover_calls
    ):
        entry, _ = await _setup(
            hass,
            cover_position=100,
            shutter=self._pending_shutter(
                **{
                    CONF_WINDOW_VENT_WHILE_OPEN: True,
                    CONF_LOCK_PROTECTION: True,
                    CONF_MIN_POSITION_WHEN_OPEN: 60,
                }
            ),
        )
        hass.states.async_set(WINDOW, "on")
        await hass.async_block_till_done()
        # Der erste Tick holt die heute schon vergangene Morgenfahrt nach –
        # sie interessiert hier nicht.
        await _tick(hass, entry, datetime(2026, 8, 29, 7, 0))
        cover_calls.clear()

        await _tick(hass, entry, datetime(2026, 8, 29, 19, 0))
        assert [c.data["position"] for c in cover_calls] == [60]


# --- 3: Wolf – die angelernte „My"-Position ---------------------------------


AWNING = "cover.markise_terrasse"


def _awning(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: AWNING,
        CONF_NAME: "Markise",
        CONF_DEVICE_KIND: KIND_AWNING,
        CONF_AREA_DOWN_ID: "living",
        CONF_POSITION_OPEN: 0,
        CONF_POSITION_SUN_PROTECT: 100,
        CONF_BLIND_DRIVE: True,
    }
    shutter.update(overrides)
    return shutter


class TestMyPosition:
    """Somfy RTS über Overkiz: `button.<markise>_my_position` als dritte Stellung."""

    @pytest.fixture
    def calls(self, hass):
        return {
            "position": async_mock_service(hass, "cover", "set_cover_position"),
            "open": async_mock_service(hass, "cover", "open_cover"),
            "close": async_mock_service(hass, "cover", "close_cover"),
            "press": async_mock_service(hass, "button", "press"),
        }

    async def _drive(self, hass, position: float, features: int, **overrides):
        from custom_components.shutter_pilot.helpers import set_cover_position

        hass.states.async_set(AWNING, "open", {"supported_features": features})
        hass.states.async_set("button.markise_my_position", "unknown")
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={CONF_AREAS: [AREA], CONF_SHUTTERS: [_awning(**overrides)]},
        )
        config_entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {}
        await set_cover_position(hass, config_entry, AWNING, position, "Test")
        await hass.async_block_till_done()

    async def test_intermediate_position_presses_the_my_button(self, hass, calls):
        # supported_features ohne SET_POSITION (4): OPEN|CLOSE|STOP = 11
        await self._drive(
            hass,
            60,
            11,
            **{
                CONF_MY_POSITION_ENTITY: "button.markise_my_position",
                CONF_MY_POSITION_PCT: 50,
            },
        )
        assert len(calls["press"]) == 1
        assert not calls["open"] and not calls["close"]

    async def test_a_target_far_from_my_still_uses_the_end_stop(self, hass, calls):
        await self._drive(
            hass,
            100,
            11,
            **{
                CONF_MY_POSITION_ENTITY: "button.markise_my_position",
                CONF_MY_POSITION_PCT: 50,
            },
        )
        assert not calls["press"]
        assert len(calls["open"]) == 1

    async def test_without_a_my_entity_nothing_changes(self, hass, calls):
        await self._drive(hass, 60, 11)
        assert not calls["press"]
        assert len(calls["open"]) == 1

    async def test_a_drive_that_can_position_is_left_alone(self, hass, calls):
        """My wäre dort nur ungenauer – die Zahl ist die bessere Anweisung."""
        await self._drive(
            hass,
            60,
            15,
            **{
                CONF_MY_POSITION_ENTITY: "button.markise_my_position",
                CONF_MY_POSITION_PCT: 50,
            },
        )
        assert not calls["press"]
        assert [c.data["position"] for c in calls["position"]] == [60]


# --- 4: Smons/Linos – Dienste ohne Bereich und der Statussensor --------------


class TestHouseWideServices:
    """„Alle Rollläden hoch" soll ein Aufruf sein, nicht einer je Bereich."""

    async def _setup_two_areas(self, hass):
        areas = [
            {**AREA, CONF_AREA_ID: "living", CONF_AREA_NAME: "Wohnen"},
            {**AREA, CONF_AREA_ID: "sleep", CONF_AREA_NAME: "Schlafen"},
        ]
        shutters = [
            _shutter(
                **{
                    CONF_COVER_ENTITY_ID: "cover.a",
                    CONF_AREA_UP_ID: "living",
                    CONF_AREA_DOWN_ID: "living",
                    CONF_LOCK_PROTECTION: False,
                    CONF_WINDOW_ENTITY_ID: "",
                }
            ),
            _shutter(
                **{
                    CONF_COVER_ENTITY_ID: "cover.b",
                    CONF_AREA_UP_ID: "sleep",
                    CONF_AREA_DOWN_ID: "sleep",
                    CONF_LOCK_PROTECTION: False,
                    CONF_WINDOW_ENTITY_ID: "",
                }
            ),
        ]
        for cover in ("cover.a", "cover.b"):
            hass.states.async_set(
                cover, "closed", {"current_position": 0, "supported_features": 15}
            )
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={CONF_AREAS: areas, CONF_SHUTTERS: shutters},
        )
        config_entry.add_to_hass(hass)
        with patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
        return config_entry

    async def test_open_group_without_area_covers_every_area(self, hass, cover_calls):
        await self._setup_two_areas(hass)
        await hass.services.async_call(DOMAIN, "open_group", {}, blocking=True)
        await hass.async_block_till_done()
        assert sorted(c.data["entity_id"] for c in cover_calls) == ["cover.a", "cover.b"]

    async def test_open_group_with_area_still_covers_only_that_one(
        self, hass, cover_calls
    ):
        await self._setup_two_areas(hass)
        await hass.services.async_call(
            DOMAIN, "open_group", {"area_id": "sleep"}, blocking=True
        )
        await hass.async_block_till_done()
        assert [c.data["entity_id"] for c in cover_calls] == ["cover.b"]

    async def test_stop_group_stops_every_cover_once(self, hass):
        stops = async_mock_service(hass, "cover", "stop_cover")
        await self._setup_two_areas(hass)
        await hass.services.async_call(DOMAIN, "stop_group", {}, blocking=True)
        await hass.async_block_till_done()
        # Jeder Rollladen steht in beiden Richtungen im selben Bereich – er
        # darf trotzdem nur einmal angehalten werden.
        assert sorted(c.data["entity_id"] for c in stops) == ["cover.a", "cover.b"]


class TestStatusSensor:
    """Linos: eine Entität fürs HA-Dashboard, Primär- und Sekundärstatus."""

    async def test_open_house_reads_open(self, hass, cover_calls):
        await _setup(hass, cover_position=100)
        state = hass.states.get("sensor.shutter_pilot_status")
        assert state.state == "open"
        assert state.attributes["open"] == 1
        assert state.attributes["closed"] == 0
        assert state.attributes["shading_active"] is False

    async def test_closed_house_reads_closed(self, hass, cover_calls):
        await _setup(hass, cover_position=0)
        assert hass.states.get("sensor.shutter_pilot_status").state == "closed"

    async def test_shading_names_the_area(self, hass, cover_calls):
        """Der Sekundärstatus: welche Bereiche gerade beschattet werden."""
        from custom_components.shutter_pilot.helpers import set_cover_sun_protected

        entry, data = await _setup(hass, cover_position=40)
        set_cover_sun_protected(data, COVER, True)

        sensor = next(
            e
            for e in hass.data["entity_components"]["sensor"].entities
            if e.unique_id == f"{entry.entry_id}_status"
        )
        attrs = sensor.extra_state_attributes
        assert sensor.native_value == "partial"
        assert attrs["shading_active"] is True
        assert attrs["shading_areas"] == ["Wohnbereich"]
        assert attrs["shading_covers"] == [COVER]

    async def test_a_retracted_awning_is_not_counted_as_closed(self, hass):
        """Eine eingefahrene Markise ist in Ruhe, nicht "das Haus ist zu"."""
        hass.states.async_set(
            AWNING, "closed", {"current_position": 0, "supported_features": 15}
        )
        hass.states.async_set(
            COVER, "open", {"current_position": 100, "supported_features": 15}
        )
        hass.states.async_set(WINDOW, "off")
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Shutter Pilot",
            options={
                CONF_AREAS: [AREA],
                CONF_SHUTTERS: [_shutter(**{CONF_LOCK_PROTECTION: False}), _awning()],
            },
        )
        config_entry.add_to_hass(hass)
        with patch(
            "custom_components.shutter_pilot._async_register_panel", return_value=None
        ):
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()

        state = hass.states.get("sensor.shutter_pilot_status")
        assert state.state == "open"
        assert state.attributes["closed"] == 0
        assert state.attributes["awnings_retracted"] == 1
