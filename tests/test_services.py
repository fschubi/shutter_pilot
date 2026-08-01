"""Tests for the group services.

Regression guard: open_group/close_group used to drive a hard-coded 100/0 and
sun_protect_group applied the first shutter's angle to every shutter in the
area, both ignoring the per-shutter configuration.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.shutter_pilot.const import DOMAIN, EVENT_COVER_MOVED


@pytest.fixture
def cover_calls(hass):
    return async_mock_service(hass, "cover", "set_cover_position")


def _positions(calls) -> dict[str, int]:
    out = {}
    for call in calls:
        out[call.data["entity_id"]] = call.data["position"]
    return out


async def test_open_group_uses_per_shutter_positions(hass, entry, cover_calls):
    await hass.services.async_call(
        DOMAIN, "open_group", {"area_id": "living"}, blocking=True
    )
    await hass.async_block_till_done()
    assert _positions(cover_calls) == {"cover.living_room": 90, "cover.kitchen": 80}


async def test_close_group_uses_per_shutter_positions(hass, entry, cover_calls):
    await hass.services.async_call(
        DOMAIN, "close_group", {"area_id": "living"}, blocking=True
    )
    await hass.async_block_till_done()
    assert _positions(cover_calls) == {"cover.living_room": 10, "cover.kitchen": 20}


async def test_sun_protect_group_uses_per_shutter_positions(hass, entry, cover_calls):
    """Each shutter gets its own shading angle, not the first one's."""
    await hass.services.async_call(
        DOMAIN, "sun_protect_group", {"area_id": "living"}, blocking=True
    )
    await hass.async_block_till_done()
    assert _positions(cover_calls) == {"cover.living_room": 40, "cover.kitchen": 60}


async def test_ventilate_group_uses_tilted_position(hass, entry, cover_calls):
    """Ventilation reuses the position configured for a tilted window."""
    await hass.services.async_call(
        DOMAIN, "ventilate_group", {"area_id": "living"}, blocking=True
    )
    await hass.async_block_till_done()
    # Defaults apply: no explicit position_when_window_tilted in the fixture.
    assert _positions(cover_calls) == {"cover.living_room": 50, "cover.kitchen": 50}


async def test_unknown_area_does_nothing(hass, entry, cover_calls):
    await hass.services.async_call(
        DOMAIN, "close_group", {"area_id": "does_not_exist"}, blocking=True
    )
    await hass.async_block_till_done()
    assert cover_calls == []


async def test_movement_fires_bus_event(hass, entry, cover_calls):
    """Users can hook their own automations onto the movement event."""
    events = []
    hass.bus.async_listen(EVENT_COVER_MOVED, events.append)

    await hass.services.async_call(
        DOMAIN, "open_group", {"area_id": "living"}, blocking=True
    )
    await hass.async_block_till_done()

    assert len(events) == 2
    payload = {e.data["entity_id"]: e.data for e in events}
    assert payload["cover.living_room"]["position"] == 90
    assert payload["cover.living_room"]["area_id"] == "living"
    assert payload["cover.living_room"]["source"] == "automation"
    assert "open_group" in payload["cover.living_room"]["reason"]
