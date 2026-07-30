"""Config flow for Shutter Pilot integration.

All real configuration happens in the Shutter Pilot sidebar panel, which talks
to the WebSocket API in __init__.py. The options flow therefore only points
users at the panel instead of duplicating every field in a second UI.
"""

from __future__ import annotations

import logging
from copy import deepcopy

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    AREA_MODE_BRIGHTNESS,
    AREA_MODE_SUN,
    AREA_MODE_TIME,
    CONF_AREA_AUTO_ENTITY_ID,
    CONF_AREA_AZIMUTH_ENABLED,
    CONF_AREA_AZIMUTH_MAX,
    CONF_AREA_AZIMUTH_MIN,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    CONF_AREA_DOWN_LIGHT_BRIGHTNESS,
    CONF_AREA_DOWN_LIGHT_ENTITY,
    CONF_AREA_DRIVE_DELAY,
    CONF_AREA_ELEVATION_MAX,
    CONF_AREA_ELEVATION_MIN,
    CONF_AREA_ID,
    CONF_AREA_MANUAL_OVERRIDE,
    CONF_AREA_MODE,
    CONF_AREA_NAME,
    CONF_AREA_RANDOM_OFFSET,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_SUNRISE_OFFSET,
    CONF_AREA_SUNSET_OFFSET,
    CONF_AREA_TIME_DOWN,
    CONF_AREA_TIME_UP,
    CONF_AREA_TIME_WE_DOWN,
    CONF_AREA_TIME_WE_UP,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_DOWN_TO,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WE_UP_TO,
    CONF_AREA_WORKDAY_SENSOR,
    CONF_AREAS,
    CONF_SHUTTERS,
    DEFAULT_AREA_AZIMUTH_MAX,
    DEFAULT_AREA_AZIMUTH_MIN,
    DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD,
    DEFAULT_AREA_DOWN_LIGHT_BRIGHTNESS,
    DEFAULT_AREA_DRIVE_DELAY,
    DEFAULT_AREA_ELEVATION_MAX,
    DEFAULT_AREA_ELEVATION_MIN,
    DEFAULT_AREA_MANUAL_OVERRIDE,
    DEFAULT_AREA_RANDOM_OFFSET,
    DEFAULT_AREA_SUNRISE_OFFSET,
    DEFAULT_AREA_SUNSET_OFFSET,
    DEFAULT_AREA_TIME_DOWN,
    DEFAULT_AREA_TIME_UP,
    DEFAULT_AREA_TIME_WE_DOWN,
    DEFAULT_AREA_TIME_WE_UP,
    DEFAULT_AREA_W_DOWN_FROM,
    DEFAULT_AREA_W_DOWN_TO,
    DEFAULT_AREA_W_UP_FROM,
    DEFAULT_AREA_W_UP_TO,
    DEFAULT_AREA_WE_DOWN_FROM,
    DEFAULT_AREA_WE_DOWN_TO,
    DEFAULT_AREA_WE_UP_FROM,
    DEFAULT_AREA_WE_UP_TO,
)

_LOGGER = logging.getLogger(__name__)


def default_area(area_id: str, name: str, mode: str) -> dict:
    """Build a fully populated area definition with sensible defaults."""
    base = {
        CONF_AREA_ID: area_id,
        CONF_AREA_NAME: name,
        CONF_AREA_MODE: mode,
        CONF_AREA_DRIVE_DELAY: DEFAULT_AREA_DRIVE_DELAY,
        CONF_AREA_AUTO_ENTITY_ID: "",
        CONF_AREA_WORKDAY_SENSOR: "",
        CONF_AREA_RANDOM_OFFSET: DEFAULT_AREA_RANDOM_OFFSET,
        CONF_AREA_MANUAL_OVERRIDE: DEFAULT_AREA_MANUAL_OVERRIDE,
        CONF_AREA_SUN_PROTECT_ENABLED: False,
        CONF_AREA_ELEVATION_MIN: DEFAULT_AREA_ELEVATION_MIN,
        CONF_AREA_ELEVATION_MAX: DEFAULT_AREA_ELEVATION_MAX,
        CONF_AREA_AZIMUTH_ENABLED: False,
        CONF_AREA_AZIMUTH_MIN: DEFAULT_AREA_AZIMUTH_MIN,
        CONF_AREA_AZIMUTH_MAX: DEFAULT_AREA_AZIMUTH_MAX,
        CONF_AREA_DOWN_LIGHT_ENTITY: "",
        CONF_AREA_DOWN_LIGHT_BRIGHTNESS: DEFAULT_AREA_DOWN_LIGHT_BRIGHTNESS,
    }
    if mode == AREA_MODE_TIME:
        base.update(
            {
                CONF_AREA_TIME_UP: DEFAULT_AREA_TIME_UP,
                CONF_AREA_TIME_DOWN: DEFAULT_AREA_TIME_DOWN,
                CONF_AREA_TIME_WE_UP: DEFAULT_AREA_TIME_WE_UP,
                CONF_AREA_TIME_WE_DOWN: DEFAULT_AREA_TIME_WE_DOWN,
            }
        )
    elif mode == AREA_MODE_SUN:
        base.update(
            {
                CONF_AREA_SUNRISE_OFFSET: DEFAULT_AREA_SUNRISE_OFFSET,
                CONF_AREA_SUNSET_OFFSET: DEFAULT_AREA_SUNSET_OFFSET,
            }
        )
    elif mode == AREA_MODE_BRIGHTNESS:
        base.update(
            {
                CONF_AREA_BRIGHTNESS_SENSOR: "",
                CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD: DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD,
                CONF_AREA_BRIGHTNESS_UP_THRESHOLD: DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD,
                CONF_AREA_W_UP_FROM: DEFAULT_AREA_W_UP_FROM,
                CONF_AREA_W_UP_TO: DEFAULT_AREA_W_UP_TO,
                CONF_AREA_W_DOWN_FROM: DEFAULT_AREA_W_DOWN_FROM,
                CONF_AREA_W_DOWN_TO: DEFAULT_AREA_W_DOWN_TO,
                CONF_AREA_WE_UP_FROM: DEFAULT_AREA_WE_UP_FROM,
                CONF_AREA_WE_UP_TO: DEFAULT_AREA_WE_UP_TO,
                CONF_AREA_WE_DOWN_FROM: DEFAULT_AREA_WE_DOWN_FROM,
                CONF_AREA_WE_DOWN_TO: DEFAULT_AREA_WE_DOWN_TO,
            }
        )
    return base


DEFAULT_OPTIONS = {
    CONF_AREAS: [
        default_area("living", "Wohnbereich", AREA_MODE_TIME),
        default_area("sleep", "Schlafbereich", AREA_MODE_TIME),
        default_area("children", "Kinderbereich", AREA_MODE_TIME),
    ],
    CONF_SHUTTERS: [],
}

# Backwards compatible alias – older code imported the private name.
_default_area = default_area


class ShutterPilotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Shutter Pilot."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step. Location is taken from Home Assistant."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Shutter Pilot",
                data={
                    CONF_LATITUDE: self.hass.config.latitude,
                    CONF_LONGITUDE: self.hass.config.longitude,
                },
                options=deepcopy(DEFAULT_OPTIONS),
            )

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ShutterPilotOptionsFlow:
        """Return the options flow handler."""
        return ShutterPilotOptionsFlow()


class ShutterPilotOptionsFlow(config_entries.OptionsFlow):
    """Minimal options flow – configuration lives in the sidebar panel."""

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Point the user to the panel and keep options untouched."""
        if user_input is not None:
            return self.async_create_entry(title="", data=dict(self.config_entry.options))

        options = self.config_entry.options or {}
        areas = options.get(CONF_AREAS, [])
        shutters = options.get(CONF_SHUTTERS, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={
                "area_count": str(len(areas) if isinstance(areas, list) else 0),
                "shutter_count": str(len(shutters) if isinstance(shutters, list) else 0),
            },
        )
