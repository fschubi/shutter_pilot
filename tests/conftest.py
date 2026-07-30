"""Shared fixtures for the Shutter Pilot test suite."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    AREA_MODE_TIME,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
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

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load custom_components/ during tests."""
    yield


# Two shutters with deliberately non-default positions, so any code path that
# hard-codes 100/0 instead of reading the configuration shows up immediately.
OPTIONS = {
    CONF_AREAS: [
        {
            CONF_AREA_ID: "living",
            CONF_AREA_NAME: "Wohnbereich",
            CONF_AREA_MODE: AREA_MODE_TIME,
            CONF_AREA_TIME_UP: "07:00",
            CONF_AREA_TIME_DOWN: "19:00",
            CONF_AREA_DRIVE_DELAY: 0,
            CONF_AREA_SUN_PROTECT_ENABLED: True,
        }
    ],
    CONF_SHUTTERS: [
        {
            CONF_COVER_ENTITY_ID: "cover.living_room",
            CONF_NAME: "Wohnzimmer",
            CONF_AREA_UP_ID: "living",
            CONF_AREA_DOWN_ID: "living",
            CONF_POSITION_OPEN: 90,
            CONF_POSITION_CLOSED: 10,
            CONF_POSITION_SUN_PROTECT: 40,
        },
        {
            CONF_COVER_ENTITY_ID: "cover.kitchen",
            CONF_NAME: "Küche",
            CONF_AREA_UP_ID: "living",
            CONF_AREA_DOWN_ID: "living",
            CONF_POSITION_OPEN: 80,
            CONF_POSITION_CLOSED: 20,
            CONF_POSITION_SUN_PROTECT: 60,
        },
    ],
}


@pytest.fixture
async def entry(hass):
    """Set up a Shutter Pilot config entry.

    The sidebar panel needs the real `hass_frontend` asset paths, which are not
    worth exercising here, so its registration is stubbed out. Everything else -
    platforms, services, listeners - runs for real.
    """
    for cover in ("cover.living_room", "cover.kitchen"):
        hass.states.async_set(
            cover, "open", {"current_position": 100, "supported_features": 15}
        )
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 30.0,
            "azimuth": 180.0,
            "next_rising": "2025-07-08T05:00:00+00:00",
            "next_setting": "2025-07-07T21:00:00+00:00",
        },
    )
    config_entry = MockConfigEntry(domain=DOMAIN, title="Shutter Pilot", options=OPTIONS)
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.shutter_pilot._async_register_panel",
        return_value=None,
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry
