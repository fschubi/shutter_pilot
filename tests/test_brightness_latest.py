"""Feste Uhrzeit im Helligkeitsmodus, unabhaengig vom Lux-Wert.

Forum, hollizone: in der dunklen Jahreszeit wird die Hoch-Schwelle nie
erreicht. Die Zeitfenster oben erlauben eine Fahrt nur, sie loesen keine aus –
es fehlte also eine Frist.

Bewusst ohne das schwere Fixture aus test_forum_findings.py: der
Helligkeitsmodus laesst sich mit Optionen am Entry und einem hingestellten
hass.data[DOMAIN][entry_id] aufsetzen, die Fahrt selbst wird gepatcht. Dass
set_cover_position() faehrt, haelt die uebrige Suite fest.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.brightness import (
    _latest_deadline,
    setup_brightness_listener,
)
from custom_components.shutter_pilot.const import (
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_B_LATEST_DOWN,
    CONF_AREA_B_LATEST_DOWN_ENABLED,
    CONF_AREA_B_LATEST_UP,
    CONF_AREA_B_LATEST_UP_ENABLED,
    CONF_AREA_B_WE_LATEST_DOWN,
    CONF_AREA_B_WE_LATEST_UP,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_DOWN_ID,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_OPEN,
    CONF_SHUTTERS,
    DOMAIN,
)

COVER = "cover.wohnzimmer"
SENSOR = "sensor.lux"


def _monday(hour: int, minute: int = 0) -> datetime:
    return datetime(2025, 7, 7, hour, minute)


def _saturday(hour: int, minute: int = 0) -> datetime:
    return datetime(2025, 7, 12, hour, minute)


def _area(**overrides) -> dict:
    area = {
        CONF_AREA_ID: "living",
        CONF_AREA_MODE: AREA_MODE_BRIGHTNESS,
        CONF_AREA_BRIGHTNESS_SENSOR: SENSOR,
    }
    area.update(overrides)
    return area


# --- Welche Uhrzeit gilt ------------------------------------------------------


class TestDeadlineResolution:
    def test_off_by_default(self):
        """Ohne Haken gibt es keine Frist – die Vorgabe bewegt nichts."""
        assert _latest_deadline(None, _area(), _monday(12), "up") is None
        assert _latest_deadline(None, _area(), _monday(12), "down") is None

    def test_time_is_set_but_switch_is_off(self):
        area = _area(**{CONF_AREA_B_LATEST_UP: "09:00"})
        assert _latest_deadline(None, area, _monday(12), "up") is None

    def test_weekday_value(self):
        area = _area(
            **{CONF_AREA_B_LATEST_UP_ENABLED: True, CONF_AREA_B_LATEST_UP: "08:30"}
        )
        assert _latest_deadline(None, area, _monday(12), "up").strftime("%H:%M") == "08:30"

    def test_weekend_falls_back_to_the_weekday_value(self):
        """Wie ueberall: leerer Wochenendwert heisst 'wie in der Woche'."""
        area = _area(
            **{
                CONF_AREA_B_LATEST_UP_ENABLED: True,
                CONF_AREA_B_LATEST_UP: "08:30",
                CONF_AREA_B_WE_LATEST_UP: "",
            }
        )
        assert _latest_deadline(None, area, _saturday(12), "up").strftime("%H:%M") == "08:30"

    def test_weekend_value_wins_when_set(self):
        area = _area(
            **{
                CONF_AREA_B_LATEST_UP_ENABLED: True,
                CONF_AREA_B_LATEST_UP: "08:30",
                CONF_AREA_B_WE_LATEST_UP: "10:00",
            }
        )
        assert _latest_deadline(None, area, _saturday(12), "up").strftime("%H:%M") == "10:00"

    def test_down_has_its_own_pair(self):
        area = _area(
            **{
                CONF_AREA_B_LATEST_DOWN_ENABLED: True,
                CONF_AREA_B_LATEST_DOWN: "17:45",
                CONF_AREA_B_WE_LATEST_DOWN: "19:00",
            }
        )
        assert _latest_deadline(None, area, _monday(12), "down").strftime("%H:%M") == "17:45"
        assert _latest_deadline(None, area, _saturday(12), "down").strftime("%H:%M") == "19:00"

    def test_unparsable_time_falls_back_to_the_default(self):
        area = _area(
            **{CONF_AREA_B_LATEST_UP_ENABLED: True, CONF_AREA_B_LATEST_UP: "kaputt"}
        )
        assert _latest_deadline(None, area, _monday(12), "up").strftime("%H:%M") == "09:00"


# --- Was der Minutentakt daraus macht ----------------------------------------


async def _setup(hass, area: dict) -> tuple[MockConfigEntry, dict]:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_AREAS: [area],
            CONF_SHUTTERS: [
                {
                    CONF_COVER_ENTITY_ID: COVER,
                    CONF_AREA_UP_ID: "living",
                    CONF_AREA_DOWN_ID: "living",
                    CONF_POSITION_OPEN: 100,
                    CONF_POSITION_CLOSED: 0,
                }
            ],
        },
    )
    entry.add_to_hass(hass)
    # Nicht leer lassen: setup_brightness_listener steigt bei einem falsy
    # Laufzeit-Dict sofort aus, und {} ist falsy.
    data: dict = hass.data.setdefault(DOMAIN, {}).setdefault(
        entry.entry_id, {"master_enabled": True}
    )
    await setup_brightness_listener(hass, entry)
    return entry, data


def _tick(data: dict):
    return data.get("_minute_callbacks", {}).get("brightness")


class TestMinuteTick:
    """Der Helligkeitsmodus haengt sonst allein am State-Change des Sensors."""

    async def test_no_ticker_without_a_deadline(self, hass):
        _, data = await _setup(hass, _area())
        assert _tick(data) is None

    async def test_deadline_drives_up_without_any_lux_value(self, hass):
        _, data = await _setup(
            hass,
            _area(
                **{CONF_AREA_B_LATEST_UP_ENABLED: True, CONF_AREA_B_LATEST_UP: "09:00"}
            ),
        )
        tick = _tick(data)
        assert tick is not None

        with patch(
            "custom_components.shutter_pilot.brightness.set_cover_position",
            new=AsyncMock(return_value=True),
        ) as drive:
            tick(_monday(8, 59))
            await hass.async_block_till_done()
            assert drive.await_count == 0, "vor der Frist faehrt nichts"

            tick(_monday(9, 0))
            await hass.async_block_till_done()
            assert drive.await_count == 1
            assert drive.await_args.args[3] == 100

    async def test_the_deadline_runs_once_a_day(self, hass):
        """Sonst faehrt sie den Rollladen wieder hoch, den der Lux-Wert schloss."""
        _, data = await _setup(
            hass,
            _area(
                **{CONF_AREA_B_LATEST_UP_ENABLED: True, CONF_AREA_B_LATEST_UP: "09:00"}
            ),
        )
        tick = _tick(data)
        with patch(
            "custom_components.shutter_pilot.brightness.set_cover_position",
            new=AsyncMock(return_value=True),
        ) as drive:
            tick(_monday(9, 0))
            await hass.async_block_till_done()
            # Der Lux-Wert schliesst am Abend, die Buchfuehrung dreht sich um.
            data["covers_driven_up"].discard(COVER)
            data["covers_driven_down"].add(COVER)
            tick(_monday(17, 0))
            await hass.async_block_till_done()
            assert drive.await_count == 1

    async def test_a_passed_deadline_does_not_catch_up_after_a_restart(self, hass):
        """Ein Reload um 23 Uhr darf nicht 'spaetestens 09:00' nachholen."""
        with patch(
            "homeassistant.util.dt.now", return_value=_as_local(hass, _monday(23, 0))
        ):
            _, data = await _setup(
                hass,
                _area(
                    **{
                        CONF_AREA_B_LATEST_UP_ENABLED: True,
                        CONF_AREA_B_LATEST_UP: "09:00",
                    }
                ),
            )
            tick = _tick(data)
            with patch(
                "custom_components.shutter_pilot.brightness.set_cover_position",
                new=AsyncMock(return_value=True),
            ) as drive:
                tick(_monday(23, 1))
                await hass.async_block_till_done()
                assert drive.await_count == 0

    async def test_down_deadline_closes(self, hass):
        _, data = await _setup(
            hass,
            _area(
                **{
                    CONF_AREA_B_LATEST_DOWN_ENABLED: True,
                    CONF_AREA_B_LATEST_DOWN: "18:00",
                }
            ),
        )
        tick = _tick(data)
        with patch(
            "custom_components.shutter_pilot.brightness.set_cover_position",
            new=AsyncMock(return_value=True),
        ) as drive:
            tick(_monday(18, 0))
            await hass.async_block_till_done()
            assert drive.await_count == 1
            assert drive.await_args.args[3] == 0

    async def test_a_switched_off_area_stays_put(self, hass):
        _, data = await _setup(
            hass,
            _area(
                **{CONF_AREA_B_LATEST_UP_ENABLED: True, CONF_AREA_B_LATEST_UP: "09:00"}
            ),
        )
        data["auto_modes"] = {"living": False}
        tick = _tick(data)
        with patch(
            "custom_components.shutter_pilot.brightness.set_cover_position",
            new=AsyncMock(return_value=True),
        ) as drive:
            tick(_monday(9, 0))
            await hass.async_block_till_done()
            assert drive.await_count == 0


def _as_local(hass, moment: datetime) -> datetime:
    from homeassistant.util import dt as dt_util

    return moment.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)


@pytest.fixture(autouse=True)
def _berlin():
    """Ortszeit festnageln – die Frist ist eine Wanduhrzeit."""
    from homeassistant.util import dt as dt_util

    previous = dt_util.DEFAULT_TIME_ZONE
    dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Berlin"))
    yield
    dt_util.set_default_time_zone(previous)
