"""End-to-end setup tests: the integration must load with all platforms."""

from __future__ import annotations

from custom_components.shutter_pilot.const import DOMAIN


async def test_setup_succeeds(hass, entry):
    """All platforms load and runtime data is populated."""
    assert entry.entry_id in hass.data[DOMAIN]
    assert hass.data[DOMAIN][entry.entry_id]["master_enabled"] is True


async def test_switch_entities_created(hass, entry):
    """Master switch plus one auto switch per area."""
    states = [s for s in hass.states.async_all("switch") if "shutter_pilot" in s.entity_id]
    assert len(states) >= 2


async def test_next_action_sensor_created(hass, entry):
    """The next-action sensor exists and reports a direction."""
    sensors = [s for s in hass.states.async_all("sensor") if "shutter_pilot" in s.entity_id]
    assert len(sensors) == 1
    state = sensors[0]
    assert state.attributes["area_id"] == "living"
    assert state.attributes["direction"] in ("up", "down")


async def test_sun_protection_binary_sensor_created(hass, entry):
    """Only areas with shading enabled get a binary sensor."""
    sensors = [
        s for s in hass.states.async_all("binary_sensor") if "shutter_pilot" in s.entity_id
    ]
    assert len(sensors) == 1
    assert sensors[0].attributes["area_id"] == "living"


async def test_services_registered(hass, entry):
    for service in ("open_group", "close_group", "sun_protect_group"):
        assert hass.services.has_service(DOMAIN, service)


async def test_single_minute_ticker(hass, entry):
    """Scheduler and sun protection share one timer, not two."""
    data = hass.data[DOMAIN][entry.entry_id]
    assert data.get("_minute_ticker_unsub") is not None
    assert set(data.get("_minute_callbacks", {})) == {"scheduler", "elevation"}


async def test_diagnostics(hass, entry):
    from custom_components.shutter_pilot.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["sun"]["elevation"] == 30.0
    assert result["sun"]["azimuth"] == 180.0
    assert "living" in result["next_actions"]
    assert "cover.living_room" in result["covers"]
    assert result["runtime"]["minute_ticker_active"] is True


async def test_unload(hass, entry):
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data[DOMAIN]
