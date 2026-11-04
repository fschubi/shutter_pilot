"""Fenster zu kurz vor der Hochfahrt: der Rollladen bleibt oben (Horst, #233).

Morgens vor dem Sonnenaufgang das Bad gelüftet: das Fenster fuhr den Rollladen
hoch und beim Schließen wieder zu, obwohl er Minuten später ohnehin geöffnet
wird. `window_keep_open_minutes` spart diese Rückfahrt.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.shutter_pilot import window_trigger
from custom_components.shutter_pilot.const import (
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_UP_ID,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_CLOSED,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_SHUTTERS,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_KEEP_OPEN_MINUTES,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    DOMAIN,
)
from tests.test_window_debounce import AREA, COVER, WINDOW, _positions

# Ein Mittwoch, Hochfahrt laut AREA um 07:00.
def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 11, 4, hour, minute, tzinfo=dt_util.DEFAULT_TIME_ZONE)


def _shutter(**overrides) -> dict:
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Bad",
        CONF_AREA_UP_ID: "living",
        CONF_WINDOW_ENTITY_ID: WINDOW,
        CONF_WINDOW_OPEN_STATE: "on",
        CONF_WINDOW_TILTED_STATE: "tilted",
        CONF_POSITION_CLOSED: 0,
        CONF_POSITION_WHEN_WINDOW_TILTED: 50,
        CONF_POSITION_WHEN_WINDOW_OPEN: 100,
        CONF_WINDOW_CLOSE_DEBOUNCE: 0,
        CONF_WINDOW_KEEP_OPEN_MINUTES: 30,
    }
    shutter.update(overrides)
    return shutter


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


async def _cycle(hass, shutter: dict, now: datetime, area: dict = AREA):
    """Fenster kippen, Rollladen steht dann auf 50 %, Fenster schließen."""
    hass.states.async_set(
        COVER, "closed", {"current_position": 0, "supported_features": 15}
    )
    hass.states.async_set(WINDOW, "closed")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Shutter Pilot",
        options={CONF_AREAS: [area], CONF_SHUTTERS: [shutter]},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel", return_value=None
    ), patch.object(window_trigger.dt_util, "now", return_value=now):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        hass.states.async_set(WINDOW, "tilted")
        await hass.async_block_till_done()
        hass.states.async_set(
            COVER, "open", {"current_position": 50, "supported_features": 15}
        )
        hass.states.async_set(WINDOW, "closed")
        await hass.async_block_till_done()
    return hass.data[DOMAIN][entry.entry_id]


async def test_stays_open_when_opening_is_close(hass, cover_calls):
    data = await _cycle(hass, _shutter(), _at(6, 40))
    assert _positions(cover_calls) == [50], "keine Rückfahrt auf 0"
    assert COVER not in data["trigger_actions"]
    assert COVER not in data["trigger_heights"]


async def test_restores_when_opening_is_far(hass, cover_calls):
    await _cycle(hass, _shutter(), _at(6, 0))
    assert _positions(cover_calls) == [50, 0]


async def test_restores_when_opening_already_passed(hass, cover_calls):
    """Nach 07:00 ist die nächste Hochfahrt erst morgen."""
    await _cycle(hass, _shutter(), _at(7, 5))
    assert _positions(cover_calls) == [50, 0]


async def test_off_by_default(hass, cover_calls):
    shutter = _shutter()
    del shutter[CONF_WINDOW_KEEP_OPEN_MINUTES]
    await _cycle(hass, shutter, _at(6, 40))
    assert _positions(cover_calls) == [50, 0]


async def test_blocked_opening_does_not_count(hass, cover_calls):
    """Wochenendhaken: nichts öffnet ihn später, also fährt er zurück."""
    with patch.object(window_trigger, "automated_up_blocked", return_value="weekend"):
        await _cycle(hass, _shutter(), _at(6, 40))
    assert _positions(cover_calls) == [50, 0]


async def test_brightness_area_never_qualifies(hass, cover_calls):
    area = {**AREA, CONF_AREA_MODE: AREA_MODE_BRIGHTNESS}
    await _cycle(hass, _shutter(), _at(6, 40), area=area)
    assert _positions(cover_calls) == [50, 0]


async def test_other_area_down_is_not_asked(hass, cover_calls):
    """Maßgeblich ist der Up-Bereich; ein unbekannter bedeutet Rückfahrt."""
    await _cycle(hass, _shutter(**{CONF_AREA_UP_ID: "gibt_es_nicht"}), _at(6, 40))
    assert _positions(cover_calls) == [50, 0]
