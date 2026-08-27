"""malleYay: Shutter Pilot nur fuer den Sonnenschutz.

„Gibt es eine Moeglichkeit, keinen der 3 Steuerungsmodi zu verwenden, sondern
nur den Sonnenschutz zu aktivieren?" – bis 2.15.0 nicht. Die Bereichsautomatik
auszuschalten nimmt die Beschattung mit (`elevation.py` fragt
`is_auto_enabled`), und ein Bereich ohne gewaehlten Modus faellt auf `time`
zurueck und faehrt um 07:00 und 19:00.

Denselben Fall hat Wolf, nur anders erzaehlt: sein Bereich „Wohnbereich Seite"
steht auf Automatik *aus* bei eingeschaltetem Sonnenschutz – und beschattet
deshalb nicht.

Der vierte Modus braucht in den Fahrwegen keine Zeile: alle filtern positiv auf
ihren eigenen Modus. Getestet wird deshalb genau das, was *nicht* von selbst
stimmt – der naechste-Fahrt-Sensor und die Freigabe am Abend.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot import cover_tracker
from custom_components.shutter_pilot.const import (
    AREA_MODE_BRIGHTNESS,
    AREA_MODE_NONE,
    AREA_MODE_SUN,
    AREA_MODE_TIME,
    AREA_MODES,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_SHADE_RELEASE_OPENS,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
)
from custom_components.shutter_pilot.helpers import (
    is_cover_sun_protected,
    shade_release_opens,
)
from custom_components.shutter_pilot.schedule_times import get_next_action

COVER = "cover.wohnzimmer"


# --- Reine Funktionen -------------------------------------------------------


class TestNextActionWithoutASchedule:
    """Der Sensor „naechste Fahrt" darf nichts versprechen.

    Das ist die eine Stelle, die ein unbekannter Modus *nicht* von selbst
    richtig macht: der Zweig am Ende faellt auf die Zeitmodus-Zeiten zurueck.
    """

    NOW = datetime(2026, 8, 27, 12, 0)

    def _area(self, mode):
        return {
            CONF_AREA_ID: "og",
            CONF_AREA_MODE: mode,
            CONF_AREA_TIME_UP: "07:00",
            CONF_AREA_TIME_DOWN: "19:00",
        }

    async def test_none_reports_nothing(self, hass):
        when, direction = get_next_action(
            hass, self._area(AREA_MODE_NONE), dt_util.as_local(self.NOW)
        )

        assert when is None
        assert direction is None

    async def test_time_mode_still_reports(self, hass):
        """Gegenprobe: dieselben Zeiten, nur mit Modus."""
        when, direction = get_next_action(
            hass, self._area(AREA_MODE_TIME), dt_util.as_local(self.NOW)
        )

        assert when is not None
        assert direction == "down"


class TestShadeReleaseIsImplied:
    """Ohne Zeitplan gibt es keinen Abendplan, der die Beschattung abloest."""

    def test_the_flag_still_wins_where_it_is_set(self):
        area = {CONF_AREA_MODE: AREA_MODE_TIME, CONF_AREA_SHADE_RELEASE_OPENS: True}

        assert shade_release_opens(area) is True

    def test_a_scheduled_area_keeps_the_old_default(self):
        assert shade_release_opens({CONF_AREA_MODE: AREA_MODE_TIME}) is False
        assert shade_release_opens({CONF_AREA_MODE: AREA_MODE_SUN}) is False
        assert shade_release_opens({CONF_AREA_MODE: AREA_MODE_BRIGHTNESS}) is False

    def test_without_a_schedule_it_is_on(self):
        assert shade_release_opens({CONF_AREA_MODE: AREA_MODE_NONE}) is True


def test_the_mode_is_offered():
    assert AREA_MODE_NONE in AREA_MODES


# --- Gegen den echten Aufbau ------------------------------------------------


@pytest.fixture(autouse=True)
def _fast_startup_restore(monkeypatch):
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


async def _setup(hass, mode, area_extra=None, position=100, elevation=42.0):
    hass.states.async_set(
        COVER, "open", {"current_position": position, "supported_features": 15}
    )
    hass.states.async_set(
        "sun.sun", "above_horizon", {"elevation": elevation, "azimuth": 180.0}
    )
    area = {
        CONF_AREA_ID: "og",
        CONF_AREA_NAME: "Wohnbereich",
        CONF_AREA_MODE: mode,
        # Beide Zeiten liegen hinter uns – im Zeitmodus faehrt das beim ersten
        # Tick, sobald die Tagesmerker geleert sind. Genau darum geht es hier.
        CONF_AREA_TIME_UP: "00:01",
        CONF_AREA_TIME_DOWN: "00:02",
        CONF_AREA_DRIVE_DELAY: 0,
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_MIN: 10,
        CONF_AREA_ELEVATION_MAX: 90,
        CONF_AREA_AZIMUTH_ENABLED: False,
        **(area_extra or {}),
    }
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Wohnzimmer",
        CONF_AREA_UP_ID: "og",
        CONF_AREA_DOWN_ID: "og",
        CONF_POSITION_OPEN: 100,
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_SUN_PROTECT: 40,
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


def _rearm_scheduler(data) -> None:
    """Vergangene Uhrzeiten gelten beim Aufbau als erledigt – sonst holte ein
    Reload um 23 Uhr den ganzen Tag nach. Im Test faehrt sonst nie etwas."""
    data.get("_scheduler_fired", {}).clear()


async def _ticks(hass, data, count: int = 2) -> None:
    for _ in range(count):
        now = dt_util.now()
        for cb in list(data.get("_minute_callbacks", {}).values()):
            cb(now)
        await hass.async_block_till_done()


class TestNothingIsDrivenBySchedule:
    async def test_time_mode_drives_the_stored_times(self, hass, cover_calls):
        """Gegenprobe: dieselben Zeiten, nur mit Modus."""
        _entry, data = await _setup(hass, AREA_MODE_TIME, position=100)
        _rearm_scheduler(data)
        await _ticks(hass, data)

        assert 0 in [c.data["position"] for c in cover_calls]

    async def test_without_a_mode_they_are_ignored(self, hass, cover_calls):
        _entry, data = await _setup(hass, AREA_MODE_NONE, position=100)
        _rearm_scheduler(data)
        await _ticks(hass, data)

        assert 0 not in [c.data["position"] for c in cover_calls]


class TestShadingStillRuns:
    """Der Punkt der ganzen Uebung."""

    async def test_it_shades(self, hass, cover_calls):
        _entry, data = await _setup(hass, AREA_MODE_NONE, elevation=42.0)
        await _ticks(hass, data)

        assert 40 in [c.data["position"] for c in cover_calls]
        assert is_cover_sun_protected(data, COVER)

    async def test_the_evening_opens_it_again(self, hass, cover_calls):
        """Ohne Zeitplan holt niemand den Rollladen von der halben Hoehe.

        Im Zeitmodus faehrt der Abendplan; hier gibt es keinen, also muss die
        Freigabe selbst oeffnen – ohne dass jemand einen Haken setzt.
        """
        _entry, data = await _setup(hass, AREA_MODE_NONE, elevation=42.0)
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)

        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 2.0, "azimuth": 180.0}
        )
        cover_calls.clear()
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
        assert 100 in [c.data["position"] for c in cover_calls]

    async def test_a_scheduled_area_is_unchanged(self, hass, cover_calls):
        """Gegenprobe zur vorigen: im Zeitmodus bleibt er stehen wie bisher."""
        _entry, data = await _setup(hass, AREA_MODE_TIME, elevation=42.0)
        await _ticks(hass, data)
        assert is_cover_sun_protected(data, COVER)

        hass.states.async_set(
            "sun.sun", "above_horizon", {"elevation": 2.0, "azimuth": 180.0}
        )
        cover_calls.clear()
        await _ticks(hass, data)

        assert not is_cover_sun_protected(data, COVER)
        assert 100 not in [c.data["position"] for c in cover_calls]
