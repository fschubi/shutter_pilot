"""Die Beschattungs-Logzeile behauptete auch dann einen Elevationsbereich,
wenn die Elevationspruefung fuer genau diesen Rollladen/dieses Cover gar
nicht entschied (`elevation_enabled=False`) - irrefuehrend beim Debuggen
genau der Konfiguration, die den Merker aus 2.22.x (is_dusk_retracted)
ueberhaupt erst braucht: "elev=5.0 in [1.0-4.0]" liest sich wie ein
bestandener Bereichs-Check, obwohl der Bereich fuer die Entscheidung
komplett irrelevant war.
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shutter_pilot.const import (
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_ELEVATION_ENABLED,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREAS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_POSITION_OPEN,
    CONF_POSITION_SUN_PROTECT,
    CONF_SHUTTERS,
    DOMAIN,
)

COVER = "cover.log_test"
AREA_ID = "log_area"


@pytest.fixture(autouse=True)
def _fast_startup(monkeypatch):
    from custom_components.shutter_pilot import cover_tracker

    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_DELAY_SEC", 0)
    monkeypatch.setattr(cover_tracker, "STARTUP_RESTORE_RETRY_SEC", 0)


@pytest.fixture
def cover_calls(hass):
    async def _handler(call):
        position = call.data["position"]
        entity_id = call.data["entity_id"]
        for eid in [entity_id] if isinstance(entity_id, str) else entity_id:
            hass.states.async_set(
                eid,
                "closed" if position <= 0 else "open",
                {"current_position": position, "supported_features": 15},
            )

    hass.services.async_register("cover", "set_cover_position", _handler)


async def _setup(hass, *, elevation_enabled: bool):
    hass.states.async_set(
        COVER, "closed", {"current_position": 0, "supported_features": 15}
    )
    hass.states.async_set(
        "sun.sun", "above_horizon", {"elevation": 5.0, "azimuth": 180.0}
    )
    area = {
        CONF_AREA_ID: AREA_ID,
        CONF_AREA_NAME: "Logtest",
        CONF_AREA_SUN_PROTECT_ENABLED: True,
        CONF_AREA_ELEVATION_ENABLED: elevation_enabled,
        CONF_AREA_ELEVATION_MIN: 1,
        CONF_AREA_ELEVATION_MAX: 10,
        CONF_AREA_AZIMUTH_ENABLED: False,
    }
    shutter = {
        CONF_COVER_ENTITY_ID: COVER,
        CONF_NAME: "Logtest Rollladen",
        "area_down_id": AREA_ID,
        CONF_POSITION_OPEN: 100,
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


async def _tick_elevation(hass, data) -> None:
    data["_minute_callbacks"]["elevation"](None)
    await hass.async_block_till_done()


class TestElevationLogReflectsWhetherItDecided:
    async def test_enabled_shows_the_range(self, hass, cover_calls, caplog):
        with caplog.at_level(
            logging.INFO, logger="custom_components.shutter_pilot.elevation"
        ):
            entry, data = await _setup(hass, elevation_enabled=True)
            await _tick_elevation(hass, data)

        assert hass.states.get(COVER).attributes.get("current_position") == 40
        messages = "\n".join(caplog.messages)
        assert "elev=5.0 in [1.0" in messages
        assert "elevation check disabled" not in messages

    async def test_disabled_says_so_instead_of_claiming_a_range(
        self, hass, cover_calls, caplog
    ):
        with caplog.at_level(
            logging.INFO, logger="custom_components.shutter_pilot.elevation"
        ):
            entry, data = await _setup(hass, elevation_enabled=False)
            await _tick_elevation(hass, data)

        # Beschattung lief trotzdem (Elevation blockiert nicht, wenn
        # abgeschaltet) - das ist nicht der Punkt dieses Tests.
        assert hass.states.get(COVER).attributes.get("current_position") == 40
        messages = "\n".join(caplog.messages)
        assert "elevation check disabled" in messages
        assert "elev=5.0 in" not in messages, (
            "BUG waere: die Elevation wird als geprueften Bereich behauptet, "
            "obwohl elevation_enabled=False sie fuer diese Fahrt gar nicht "
            "entschieden hat"
        )
