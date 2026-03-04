"""Config flow for Shutter Pilot integration."""

from __future__ import annotations

import logging
from copy import deepcopy

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_NAME,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_TRIGGER_MODE,
    CONF_GROUP_UP,
    CONF_GROUP_DOWN,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_POSITION_SUN_PROTECT,
    CONF_BRIGHTNESS_TRIGGER,
    TRIGGER_MODE_OFF,
    TRIGGER_MODE_ONLY_UP,
    TRIGGER_MODE_ONLY_DOWN,
    TRIGGER_MODE_UP_DOWN,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
    BRIGHTNESS_OFF,
    BRIGHTNESS_UP,
    BRIGHTNESS_DOWN,
    BRIGHTNESS_BOTH,
    CONF_BRIGHTNESS_ENTITY_ID,
    CONF_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_BRIGHTNESS_UP_THRESHOLD,
    CONF_BRIGHTNESS_DOWN_TIME,
    CONF_BRIGHTNESS_UP_TIME,
    CONF_BRIGHTNESS_IGNORE_TIME,
    CONF_DRIVE_DELAY,
    DEFAULT_POSITION_OPEN,
    DEFAULT_POSITION_CLOSED,
    DEFAULT_POSITION_SUN_PROTECT,
    DEFAULT_POSITION_WHEN_WINDOW_OPEN,
    DEFAULT_POSITION_WHEN_WINDOW_TILTED,
    DEFAULT_WINDOW_OPEN_STATE,
    DEFAULT_WINDOW_TILTED_STATE,
    DEFAULT_MIN_POSITION_WHEN_OPEN,
    DEFAULT_BRIGHTNESS_DOWN_THRESHOLD,
    DEFAULT_BRIGHTNESS_UP_THRESHOLD,
    DEFAULT_BRIGHTNESS_DOWN_TIME,
    DEFAULT_BRIGHTNESS_UP_TIME,
    CONF_USE_ELEVATION,
    CONF_ELEVATION_THRESHOLD,
    CONF_W_SHUTTER_UP_MIN,
    CONF_W_SHUTTER_UP_MAX,
    CONF_W_SHUTTER_DOWN,
    CONF_WE_SHUTTER_UP_MIN,
    CONF_WE_SHUTTER_UP_MAX,
    CONF_WE_SHUTTER_DOWN,
    DEFAULT_DRIVE_DELAY,
    DEFAULT_ELEVATION_THRESHOLD,
    GROUPS,
    TIME_TYPE_FIXED,
    TIME_TYPE_SUNRISE,
    TIME_TYPE_SUNSET,
    CONF_LIVING_TYPE_UP,
    CONF_LIVING_TYPE_DOWN,
    CONF_LIVING_W_UP_MIN,
    CONF_LIVING_W_UP_MAX,
    CONF_LIVING_W_DOWN,
    CONF_LIVING_WE_UP_MIN,
    CONF_LIVING_WE_UP_MAX,
    CONF_LIVING_WE_DOWN,
    CONF_SLEEP_TYPE_UP,
    CONF_SLEEP_TYPE_DOWN,
    CONF_SLEEP_W_UP_MIN,
    CONF_SLEEP_W_UP_MAX,
    CONF_SLEEP_W_DOWN,
    CONF_SLEEP_WE_UP_MIN,
    CONF_SLEEP_WE_UP_MAX,
    CONF_SLEEP_WE_DOWN,
    CONF_CHILDREN_TYPE_UP,
    CONF_CHILDREN_TYPE_DOWN,
    CONF_CHILDREN_W_UP_MIN,
    CONF_CHILDREN_W_UP_MAX,
    CONF_CHILDREN_W_DOWN,
    CONF_CHILDREN_WE_UP_MIN,
    CONF_CHILDREN_WE_UP_MAX,
    CONF_CHILDREN_WE_DOWN,
    CONF_AUTO_LIVING,
    CONF_AUTO_SLEEP,
    CONF_AUTO_CHILDREN,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_LIVING_SUNRISE_OFFSET,
    CONF_LIVING_SUNSET_OFFSET,
    CONF_SLEEP_SUNRISE_OFFSET,
    CONF_SLEEP_SUNSET_OFFSET,
    CONF_CHILDREN_SUNRISE_OFFSET,
    CONF_CHILDREN_SUNSET_OFFSET,
)

_LOGGER = logging.getLogger(__name__)

# Vollständige Standard-Optionen für Migration und sichere Optionen-Zugriffe
DEFAULT_OPTIONS = {
    CONF_SHUTTERS: [],
    CONF_DRIVE_DELAY: DEFAULT_DRIVE_DELAY,
    CONF_BRIGHTNESS_ENTITY_ID: "",
    CONF_BRIGHTNESS_DOWN_THRESHOLD: DEFAULT_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_BRIGHTNESS_UP_THRESHOLD: DEFAULT_BRIGHTNESS_UP_THRESHOLD,
    CONF_BRIGHTNESS_DOWN_TIME: DEFAULT_BRIGHTNESS_DOWN_TIME,
    CONF_BRIGHTNESS_UP_TIME: DEFAULT_BRIGHTNESS_UP_TIME,
    CONF_BRIGHTNESS_IGNORE_TIME: True,
    CONF_USE_ELEVATION: False,
    CONF_ELEVATION_THRESHOLD: DEFAULT_ELEVATION_THRESHOLD,
    CONF_W_SHUTTER_UP_MIN: "05:00",
    CONF_W_SHUTTER_UP_MAX: "06:00",
    CONF_W_SHUTTER_DOWN: "22:00",
    CONF_WE_SHUTTER_UP_MIN: "05:00",
    CONF_WE_SHUTTER_UP_MAX: "06:00",
    CONF_WE_SHUTTER_DOWN: "22:00",
    CONF_AUTO_LIVING: "",
    CONF_AUTO_SLEEP: "",
    CONF_AUTO_CHILDREN: "",
    CONF_LIVING_TYPE_UP: TIME_TYPE_FIXED,
    CONF_LIVING_TYPE_DOWN: TIME_TYPE_FIXED,
    CONF_LIVING_W_UP_MIN: "05:00",
    CONF_LIVING_W_UP_MAX: "06:00",
    CONF_LIVING_W_DOWN: "22:00",
    CONF_LIVING_WE_UP_MIN: "05:00",
    CONF_LIVING_WE_UP_MAX: "06:00",
    CONF_LIVING_WE_DOWN: "22:00",
    CONF_SLEEP_TYPE_UP: TIME_TYPE_FIXED,
    CONF_SLEEP_TYPE_DOWN: TIME_TYPE_FIXED,
    CONF_SLEEP_W_UP_MIN: "05:00",
    CONF_SLEEP_W_UP_MAX: "06:00",
    CONF_SLEEP_W_DOWN: "22:00",
    CONF_SLEEP_WE_UP_MIN: "05:00",
    CONF_SLEEP_WE_UP_MAX: "06:00",
    CONF_SLEEP_WE_DOWN: "22:00",
    CONF_CHILDREN_TYPE_UP: TIME_TYPE_FIXED,
    CONF_CHILDREN_TYPE_DOWN: TIME_TYPE_FIXED,
    CONF_CHILDREN_W_UP_MIN: "05:00",
    CONF_CHILDREN_W_UP_MAX: "06:00",
    CONF_CHILDREN_W_DOWN: "22:00",
    CONF_CHILDREN_WE_UP_MIN: "05:00",
    CONF_CHILDREN_WE_UP_MAX: "06:00",
    CONF_CHILDREN_WE_DOWN: "22:00",
    CONF_LIVING_SUNRISE_OFFSET: 0,
    CONF_LIVING_SUNSET_OFFSET: 0,
    CONF_SLEEP_SUNRISE_OFFSET: 0,
    CONF_SLEEP_SUNSET_OFFSET: 0,
    CONF_CHILDREN_SUNRISE_OFFSET: 0,
    CONF_CHILDREN_SUNSET_OFFSET: 0,
}


def _shutter_schema() -> dict:
    """Return schema for a single shutter."""
    return {
        vol.Required(CONF_COVER_ENTITY_ID): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="cover"),
        ),
        vol.Required(CONF_NAME): str,
        vol.Optional(CONF_WINDOW_ENTITY_ID): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["binary_sensor", "sensor"]),
        ),
        vol.Optional(CONF_WINDOW_OPEN_STATE, default=DEFAULT_WINDOW_OPEN_STATE): str,
        vol.Optional(CONF_WINDOW_TILTED_STATE, default=DEFAULT_WINDOW_TILTED_STATE): str,
        vol.Optional(
            CONF_POSITION_WHEN_WINDOW_OPEN, default=DEFAULT_POSITION_WHEN_WINDOW_OPEN
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional(
            CONF_POSITION_WHEN_WINDOW_TILTED, default=DEFAULT_POSITION_WHEN_WINDOW_TILTED
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional(CONF_LOCK_PROTECTION, default=False): bool,
        vol.Optional(
            CONF_MIN_POSITION_WHEN_OPEN, default=DEFAULT_MIN_POSITION_WHEN_OPEN
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional(CONF_TRIGGER_MODE, default=TRIGGER_MODE_UP_DOWN): vol.In(
            [TRIGGER_MODE_OFF, TRIGGER_MODE_ONLY_UP, TRIGGER_MODE_ONLY_DOWN, TRIGGER_MODE_UP_DOWN]
        ),
        vol.Optional(CONF_GROUP_UP, default=GROUP_LIVING): vol.In(GROUPS),
        vol.Optional(CONF_GROUP_DOWN, default=GROUP_LIVING): vol.In(GROUPS),
        vol.Optional(CONF_POSITION_OPEN, default=DEFAULT_POSITION_OPEN): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(CONF_POSITION_CLOSED, default=DEFAULT_POSITION_CLOSED): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(
            CONF_POSITION_SUN_PROTECT, default=DEFAULT_POSITION_SUN_PROTECT
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional(CONF_BRIGHTNESS_TRIGGER, default=BRIGHTNESS_OFF): vol.In(
            [BRIGHTNESS_OFF, BRIGHTNESS_UP, BRIGHTNESS_DOWN, BRIGHTNESS_BOTH]
        ),
        vol.Optional(CONF_DRIVE_AFTER_CLOSE, default=False): bool,
    }


class ShutterPilotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Shutter Pilot."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Shutter Pilot",
                data={
                    CONF_LATITUDE: self.hass.config.latitude,
                    CONF_LONGITUDE: self.hass.config.longitude,
                },
                options=deepcopy(DEFAULT_OPTIONS),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    async def async_migrate_entry(
        self, hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> bool:
        """Migrate alte Konfigurationseinträge auf vollständige Optionen."""
        opts = dict(entry.options or {})
        defaults = DEFAULT_OPTIONS
        needs_update = False
        for key, default in defaults.items():
            if key not in opts:
                opts[key] = default
                needs_update = True
        if needs_update:
            _LOGGER.info("Shutter Pilot: Migriere Konfigurationseintrag")
            hass.config_entries.async_update_entry(entry, options=opts)
        return True

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ShutterPilotOptionsFlow:
        """Get the options flow for this handler.

        In neuen Home-Assistant-Versionen wird der ConfigEntry intern
        mit dem OptionsFlow verknüpft, daher wird er hier nicht mehr
        an den Konstruktor übergeben.
        """
        _LOGGER.info("Shutter Pilot: Options-Flow wird erstellt")
        return ShutterPilotOptionsFlow()


class ShutterPilotOptionsFlow(config_entries.OptionsFlow):
    """Handle Shutter Pilot options."""

    def _opts(self) -> dict:
        """Safe access to options - merge mit Defaults für alte/inkonsistente Einträge."""
        raw = self.config_entry.options
        if raw is None:
            return dict(DEFAULT_OPTIONS)
        opts = dict(raw)
        for key, default in DEFAULT_OPTIONS.items():
            if key not in opts:
                opts[key] = default
        return opts

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Show options menu."""
        _LOGGER.info("Shutter Pilot: async_step_init aufgerufen")
        try:
            opts = self._opts()
            shutters = opts.get(CONF_SHUTTERS, [])
            if not isinstance(shutters, list):
                shutters = []
            # Dict-Format für menu_options (kein Translation-Lookup nötig)
            menu_opts = {
                "settings_menu": "Einstellungen",
                "add_shutter": "Rollladen hinzufügen",
            }
            if shutters:
                menu_opts["edit_shutter"] = "Rollladen bearbeiten"
            menu_opts["done"] = "Fertig"
            return self.async_show_menu(
                step_id="init",
                menu_options=menu_opts,
                description_placeholders={
                    "shutter_count": str(len(shutters)),
                },
            )
        except Exception as err:
            _LOGGER.exception("Shutter Pilot Options-Flow Fehler: %s", err)
            raise

    async def async_step_settings_menu(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Submenu for settings."""
        return self.async_show_menu(
            step_id="settings_menu",
            menu_options={
                "settings_general": "Allgemeine Einstellungen (Helligkeit, Auto, Sonnenschutz)",
                "settings_schedule_living": "Zeitplan Wohnbereich",
                "settings_schedule_sleep": "Zeitplan Schlafbereich",
                "settings_schedule_children": "Zeitplan Kinderbereich",
            },
        )

    async def async_step_done(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Finish options flow."""
        return self.async_create_entry(title="", data=self._opts())

    def _eid(self, val):
        if isinstance(val, list):
            return val[0] if val else ""
        return val or ""

    def _merge_and_back(self, new_opts: dict) -> FlowResult:
        """Merge new options with existing and return to init menu."""
        merged = {**self._opts(), **new_opts}
        self.hass.config_entries.async_update_entry(self.config_entry, options=merged)
        shutters = merged.get(CONF_SHUTTERS, [])
        if not isinstance(shutters, list):
            shutters = []
        menu_opts = {
            "settings_menu": "Einstellungen",
            "add_shutter": "Rollladen hinzufügen",
        }
        if shutters:
            menu_opts["edit_shutter"] = "Rollladen bearbeiten"
        menu_opts["done"] = "Fertig"
        return self.async_show_menu(
            step_id="init",
            menu_options=menu_opts,
            description_placeholders={"shutter_count": str(len(shutters))},
        )

    async def async_step_settings_general(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """General settings: brightness, elevation, auto, drive_delay."""
        if user_input is not None:
            brightness = user_input.get(CONF_BRIGHTNESS_ENTITY_ID)
            brightness = self._eid(brightness) if brightness else ""
            return self._merge_and_back({
                CONF_DRIVE_DELAY: user_input.get(CONF_DRIVE_DELAY, DEFAULT_DRIVE_DELAY),
                CONF_BRIGHTNESS_ENTITY_ID: brightness,
                CONF_BRIGHTNESS_DOWN_THRESHOLD: user_input.get(
                    CONF_BRIGHTNESS_DOWN_THRESHOLD, DEFAULT_BRIGHTNESS_DOWN_THRESHOLD
                ),
                CONF_BRIGHTNESS_UP_THRESHOLD: user_input.get(
                    CONF_BRIGHTNESS_UP_THRESHOLD, DEFAULT_BRIGHTNESS_UP_THRESHOLD
                ),
                CONF_BRIGHTNESS_DOWN_TIME: user_input.get(
                    CONF_BRIGHTNESS_DOWN_TIME, DEFAULT_BRIGHTNESS_DOWN_TIME
                ),
                CONF_BRIGHTNESS_UP_TIME: user_input.get(
                    CONF_BRIGHTNESS_UP_TIME, DEFAULT_BRIGHTNESS_UP_TIME
                ),
                CONF_BRIGHTNESS_IGNORE_TIME: user_input.get(CONF_BRIGHTNESS_IGNORE_TIME, True),
                CONF_USE_ELEVATION: user_input.get(CONF_USE_ELEVATION, False),
                CONF_ELEVATION_THRESHOLD: user_input.get(
                    CONF_ELEVATION_THRESHOLD, DEFAULT_ELEVATION_THRESHOLD
                ),
                CONF_AUTO_LIVING: self._eid(user_input.get(CONF_AUTO_LIVING)),
                CONF_AUTO_SLEEP: self._eid(user_input.get(CONF_AUTO_SLEEP)),
                CONF_AUTO_CHILDREN: self._eid(user_input.get(CONF_AUTO_CHILDREN)),
            })

        o = self._opts().get
        return self.async_show_form(
            step_id="settings_general",
            data_schema=vol.Schema({
                vol.Optional(CONF_BRIGHTNESS_ENTITY_ID, default=o(CONF_BRIGHTNESS_ENTITY_ID) or ""): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor"),
                ),
                vol.Optional(
                    CONF_BRIGHTNESS_DOWN_THRESHOLD,
                    default=o(CONF_BRIGHTNESS_DOWN_THRESHOLD, DEFAULT_BRIGHTNESS_DOWN_THRESHOLD),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100000)),
                vol.Optional(
                    CONF_BRIGHTNESS_UP_THRESHOLD,
                    default=o(CONF_BRIGHTNESS_UP_THRESHOLD, DEFAULT_BRIGHTNESS_UP_THRESHOLD),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100000)),
                vol.Optional(
                    CONF_BRIGHTNESS_DOWN_TIME,
                    default=o(CONF_BRIGHTNESS_DOWN_TIME, DEFAULT_BRIGHTNESS_DOWN_TIME),
                ): str,
                vol.Optional(
                    CONF_BRIGHTNESS_UP_TIME,
                    default=o(CONF_BRIGHTNESS_UP_TIME, DEFAULT_BRIGHTNESS_UP_TIME),
                ): str,
                vol.Optional(CONF_BRIGHTNESS_IGNORE_TIME, default=o(CONF_BRIGHTNESS_IGNORE_TIME, True)): bool,
                vol.Optional(
                    CONF_DRIVE_DELAY,
                    default=o(CONF_DRIVE_DELAY, DEFAULT_DRIVE_DELAY),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Optional(CONF_USE_ELEVATION, default=o(CONF_USE_ELEVATION, False)): bool,
                vol.Optional(
                    CONF_ELEVATION_THRESHOLD,
                    default=o(CONF_ELEVATION_THRESHOLD, DEFAULT_ELEVATION_THRESHOLD),
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
                vol.Optional(
                    CONF_AUTO_LIVING,
                    default=o(CONF_AUTO_LIVING) or "",
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["input_boolean", "switch"]),
                ),
                vol.Optional(
                    CONF_AUTO_SLEEP,
                    default=o(CONF_AUTO_SLEEP) or "",
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["input_boolean", "switch"]),
                ),
                vol.Optional(
                    CONF_AUTO_CHILDREN,
                    default=o(CONF_AUTO_CHILDREN) or "",
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["input_boolean", "switch"]),
                ),
            }),
        )

    async def async_step_settings_schedule_living(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Schedule for Living group."""
        if user_input is not None:
            return self._merge_and_back({
                CONF_LIVING_TYPE_UP: user_input.get(CONF_LIVING_TYPE_UP, TIME_TYPE_FIXED),
                CONF_LIVING_TYPE_DOWN: user_input.get(CONF_LIVING_TYPE_DOWN, TIME_TYPE_FIXED),
                CONF_LIVING_SUNRISE_OFFSET: user_input.get(CONF_LIVING_SUNRISE_OFFSET, 0),
                CONF_LIVING_SUNSET_OFFSET: user_input.get(CONF_LIVING_SUNSET_OFFSET, 0),
                CONF_LIVING_W_UP_MIN: user_input.get(CONF_LIVING_W_UP_MIN, "05:00"),
                CONF_LIVING_W_UP_MAX: user_input.get(CONF_LIVING_W_UP_MAX, "06:00"),
                CONF_LIVING_W_DOWN: user_input.get(CONF_LIVING_W_DOWN, "22:00"),
                CONF_LIVING_WE_UP_MIN: user_input.get(CONF_LIVING_WE_UP_MIN, "05:00"),
                CONF_LIVING_WE_UP_MAX: user_input.get(CONF_LIVING_WE_UP_MAX, "06:00"),
                CONF_LIVING_WE_DOWN: user_input.get(CONF_LIVING_WE_DOWN, "22:00"),
                CONF_W_SHUTTER_UP_MIN: user_input.get(CONF_LIVING_W_UP_MIN, "05:00"),
                CONF_W_SHUTTER_UP_MAX: user_input.get(CONF_LIVING_W_UP_MAX, "06:00"),
                CONF_W_SHUTTER_DOWN: user_input.get(CONF_LIVING_W_DOWN, "22:00"),
                CONF_WE_SHUTTER_UP_MIN: user_input.get(CONF_LIVING_WE_UP_MIN, "05:00"),
                CONF_WE_SHUTTER_UP_MAX: user_input.get(CONF_LIVING_WE_UP_MAX, "06:00"),
                CONF_WE_SHUTTER_DOWN: user_input.get(CONF_LIVING_WE_DOWN, "22:00"),
            })
        o = self._opts().get
        return self.async_show_form(
            step_id="settings_schedule_living",
            data_schema=vol.Schema({
                vol.Optional(CONF_LIVING_TYPE_UP, default=o(CONF_LIVING_TYPE_UP, TIME_TYPE_FIXED)): vol.In([TIME_TYPE_FIXED, TIME_TYPE_SUNRISE]),
                vol.Optional(CONF_LIVING_TYPE_DOWN, default=o(CONF_LIVING_TYPE_DOWN, TIME_TYPE_FIXED)): vol.In([TIME_TYPE_FIXED, TIME_TYPE_SUNSET]),
                vol.Optional(CONF_LIVING_SUNRISE_OFFSET, default=o(CONF_LIVING_SUNRISE_OFFSET, 0)): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
                vol.Optional(CONF_LIVING_SUNSET_OFFSET, default=o(CONF_LIVING_SUNSET_OFFSET, 0)): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
                vol.Optional(CONF_LIVING_W_UP_MIN, default=o(CONF_LIVING_W_UP_MIN) or o(CONF_W_SHUTTER_UP_MIN, "05:00")): str,
                vol.Optional(CONF_LIVING_W_UP_MAX, default=o(CONF_LIVING_W_UP_MAX) or o(CONF_W_SHUTTER_UP_MAX, "06:00")): str,
                vol.Optional(CONF_LIVING_W_DOWN, default=o(CONF_LIVING_W_DOWN) or o(CONF_W_SHUTTER_DOWN, "22:00")): str,
                vol.Optional(CONF_LIVING_WE_UP_MIN, default=o(CONF_LIVING_WE_UP_MIN) or o(CONF_WE_SHUTTER_UP_MIN, "05:00")): str,
                vol.Optional(CONF_LIVING_WE_UP_MAX, default=o(CONF_LIVING_WE_UP_MAX) or o(CONF_WE_SHUTTER_UP_MAX, "06:00")): str,
                vol.Optional(CONF_LIVING_WE_DOWN, default=o(CONF_LIVING_WE_DOWN) or o(CONF_WE_SHUTTER_DOWN, "22:00")): str,
            }),
        )

    async def async_step_settings_schedule_sleep(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Schedule for Sleep group."""
        if user_input is not None:
            return self._merge_and_back({
                CONF_SLEEP_TYPE_UP: user_input.get(CONF_SLEEP_TYPE_UP, TIME_TYPE_FIXED),
                CONF_SLEEP_TYPE_DOWN: user_input.get(CONF_SLEEP_TYPE_DOWN, TIME_TYPE_FIXED),
                CONF_SLEEP_SUNRISE_OFFSET: user_input.get(CONF_SLEEP_SUNRISE_OFFSET, 0),
                CONF_SLEEP_SUNSET_OFFSET: user_input.get(CONF_SLEEP_SUNSET_OFFSET, 0),
                CONF_SLEEP_W_UP_MIN: user_input.get(CONF_SLEEP_W_UP_MIN, "05:00"),
                CONF_SLEEP_W_UP_MAX: user_input.get(CONF_SLEEP_W_UP_MAX, "06:00"),
                CONF_SLEEP_W_DOWN: user_input.get(CONF_SLEEP_W_DOWN, "22:00"),
                CONF_SLEEP_WE_UP_MIN: user_input.get(CONF_SLEEP_WE_UP_MIN, "05:00"),
                CONF_SLEEP_WE_UP_MAX: user_input.get(CONF_SLEEP_WE_UP_MAX, "06:00"),
                CONF_SLEEP_WE_DOWN: user_input.get(CONF_SLEEP_WE_DOWN, "22:00"),
            })
        o = self._opts().get
        return self.async_show_form(
            step_id="settings_schedule_sleep",
            data_schema=vol.Schema({
                vol.Optional(CONF_SLEEP_TYPE_UP, default=o(CONF_SLEEP_TYPE_UP, TIME_TYPE_FIXED)): vol.In([TIME_TYPE_FIXED, TIME_TYPE_SUNRISE]),
                vol.Optional(CONF_SLEEP_TYPE_DOWN, default=o(CONF_SLEEP_TYPE_DOWN, TIME_TYPE_FIXED)): vol.In([TIME_TYPE_FIXED, TIME_TYPE_SUNSET]),
                vol.Optional(CONF_SLEEP_SUNRISE_OFFSET, default=o(CONF_SLEEP_SUNRISE_OFFSET, 0)): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
                vol.Optional(CONF_SLEEP_SUNSET_OFFSET, default=o(CONF_SLEEP_SUNSET_OFFSET, 0)): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
                vol.Optional(CONF_SLEEP_W_UP_MIN, default=o(CONF_SLEEP_W_UP_MIN, "05:00")): str,
                vol.Optional(CONF_SLEEP_W_UP_MAX, default=o(CONF_SLEEP_W_UP_MAX, "06:00")): str,
                vol.Optional(CONF_SLEEP_W_DOWN, default=o(CONF_SLEEP_W_DOWN, "22:00")): str,
                vol.Optional(CONF_SLEEP_WE_UP_MIN, default=o(CONF_SLEEP_WE_UP_MIN, "05:00")): str,
                vol.Optional(CONF_SLEEP_WE_UP_MAX, default=o(CONF_SLEEP_WE_UP_MAX, "06:00")): str,
                vol.Optional(CONF_SLEEP_WE_DOWN, default=o(CONF_SLEEP_WE_DOWN, "22:00")): str,
            }),
        )

    async def async_step_settings_schedule_children(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Schedule for Children group."""
        if user_input is not None:
            return self._merge_and_back({
                CONF_CHILDREN_TYPE_UP: user_input.get(CONF_CHILDREN_TYPE_UP, TIME_TYPE_FIXED),
                CONF_CHILDREN_TYPE_DOWN: user_input.get(CONF_CHILDREN_TYPE_DOWN, TIME_TYPE_FIXED),
                CONF_CHILDREN_SUNRISE_OFFSET: user_input.get(CONF_CHILDREN_SUNRISE_OFFSET, 0),
                CONF_CHILDREN_SUNSET_OFFSET: user_input.get(CONF_CHILDREN_SUNSET_OFFSET, 0),
                CONF_CHILDREN_W_UP_MIN: user_input.get(CONF_CHILDREN_W_UP_MIN, "05:00"),
                CONF_CHILDREN_W_UP_MAX: user_input.get(CONF_CHILDREN_W_UP_MAX, "06:00"),
                CONF_CHILDREN_W_DOWN: user_input.get(CONF_CHILDREN_W_DOWN, "22:00"),
                CONF_CHILDREN_WE_UP_MIN: user_input.get(CONF_CHILDREN_WE_UP_MIN, "05:00"),
                CONF_CHILDREN_WE_UP_MAX: user_input.get(CONF_CHILDREN_WE_UP_MAX, "06:00"),
                CONF_CHILDREN_WE_DOWN: user_input.get(CONF_CHILDREN_WE_DOWN, "22:00"),
            })
        o = self._opts().get
        return self.async_show_form(
            step_id="settings_schedule_children",
            data_schema=vol.Schema({
                vol.Optional(CONF_CHILDREN_TYPE_UP, default=o(CONF_CHILDREN_TYPE_UP, TIME_TYPE_FIXED)): vol.In([TIME_TYPE_FIXED, TIME_TYPE_SUNRISE]),
                vol.Optional(CONF_CHILDREN_TYPE_DOWN, default=o(CONF_CHILDREN_TYPE_DOWN, TIME_TYPE_FIXED)): vol.In([TIME_TYPE_FIXED, TIME_TYPE_SUNSET]),
                vol.Optional(CONF_CHILDREN_SUNRISE_OFFSET, default=o(CONF_CHILDREN_SUNRISE_OFFSET, 0)): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
                vol.Optional(CONF_CHILDREN_SUNSET_OFFSET, default=o(CONF_CHILDREN_SUNSET_OFFSET, 0)): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
                vol.Optional(CONF_CHILDREN_W_UP_MIN, default=o(CONF_CHILDREN_W_UP_MIN, "05:00")): str,
                vol.Optional(CONF_CHILDREN_W_UP_MAX, default=o(CONF_CHILDREN_W_UP_MAX, "06:00")): str,
                vol.Optional(CONF_CHILDREN_W_DOWN, default=o(CONF_CHILDREN_W_DOWN, "22:00")): str,
                vol.Optional(CONF_CHILDREN_WE_UP_MIN, default=o(CONF_CHILDREN_WE_UP_MIN, "05:00")): str,
                vol.Optional(CONF_CHILDREN_WE_UP_MAX, default=o(CONF_CHILDREN_WE_UP_MAX, "06:00")): str,
                vol.Optional(CONF_CHILDREN_WE_DOWN, default=o(CONF_CHILDREN_WE_DOWN, "22:00")): str,
            }),
        )

    async def async_step_add_shutter(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Add a shutter configuration."""
        if user_input is not None:
            _raw = self._opts().get(CONF_SHUTTERS, [])
            shutters = list(_raw) if isinstance(_raw, list) else []
            raw_cover = user_input.get(CONF_COVER_ENTITY_ID)
            cover_id = raw_cover[0] if isinstance(raw_cover, list) else (raw_cover or "")
            shutter_cfg = {
                CONF_COVER_ENTITY_ID: cover_id,
                CONF_NAME: user_input.get(CONF_NAME, "Shutter"),
                CONF_WINDOW_ENTITY_ID: "",
                CONF_WINDOW_OPEN_STATE: user_input.get(CONF_WINDOW_OPEN_STATE, DEFAULT_WINDOW_OPEN_STATE),
                CONF_WINDOW_TILTED_STATE: user_input.get(CONF_WINDOW_TILTED_STATE, DEFAULT_WINDOW_TILTED_STATE),
                CONF_POSITION_WHEN_WINDOW_OPEN: user_input.get(CONF_POSITION_WHEN_WINDOW_OPEN, 100),
                CONF_POSITION_WHEN_WINDOW_TILTED: user_input.get(CONF_POSITION_WHEN_WINDOW_TILTED, 50),
                CONF_LOCK_PROTECTION: user_input.get(CONF_LOCK_PROTECTION, False),
                CONF_MIN_POSITION_WHEN_OPEN: user_input.get(CONF_MIN_POSITION_WHEN_OPEN, DEFAULT_MIN_POSITION_WHEN_OPEN),
                CONF_TRIGGER_MODE: user_input.get(CONF_TRIGGER_MODE, TRIGGER_MODE_UP_DOWN),
                CONF_GROUP_UP: user_input.get(CONF_GROUP_UP, GROUP_LIVING),
                CONF_GROUP_DOWN: user_input.get(CONF_GROUP_DOWN, GROUP_LIVING),
                CONF_POSITION_OPEN: user_input.get(CONF_POSITION_OPEN, DEFAULT_POSITION_OPEN),
                CONF_POSITION_CLOSED: user_input.get(CONF_POSITION_CLOSED, DEFAULT_POSITION_CLOSED),
                CONF_POSITION_SUN_PROTECT: user_input.get(CONF_POSITION_SUN_PROTECT, DEFAULT_POSITION_SUN_PROTECT),
                CONF_BRIGHTNESS_TRIGGER: user_input.get(CONF_BRIGHTNESS_TRIGGER, BRIGHTNESS_OFF),
                CONF_DRIVE_AFTER_CLOSE: user_input.get(CONF_DRIVE_AFTER_CLOSE, False),
            }
            win_entity = user_input.get(CONF_WINDOW_ENTITY_ID)
            if win_entity:
                shutter_cfg[CONF_WINDOW_ENTITY_ID] = win_entity if isinstance(win_entity, str) else (win_entity[0] if win_entity else "")
            shutters.append(shutter_cfg)
            new_options = {**self._opts(), CONF_SHUTTERS: shutters}
            self.hass.config_entries.async_update_entry(
                self.config_entry, options=new_options
            )
            _opts = {
                "settings_menu": "Einstellungen",
                "add_shutter": "Rollladen hinzufügen",
                "done": "Fertig",
            }
            if shutters:
                _opts["edit_shutter"] = "Rollladen bearbeiten"
            return self.async_show_menu(
                step_id="init",
                menu_options=_opts,
                description_placeholders={"shutter_count": str(len(shutters))},
            )

        return self.async_show_form(
            step_id="add_shutter",
            data_schema=vol.Schema(_shutter_schema()),
        )

    async def async_step_edit_shutter(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Select shutter to edit or remove."""
        _raw = self._opts().get(CONF_SHUTTERS, [])
        shutters = list(_raw) if isinstance(_raw, list) else []

        if user_input is not None:
            idx = user_input.get("shutter_index")
            action = user_input.get("action")
            if idx is not None and action == "remove":
                shutters = [s for i, s in enumerate(shutters) if i != idx]
                new_opts = {**self._opts(), CONF_SHUTTERS: shutters}
                self.hass.config_entries.async_update_entry(
                    self.config_entry, options=new_opts
                )
                return self.async_create_entry(title="", data=new_opts)
            if idx is not None and action == "edit":
                self._edit_index = int(idx)
                return await self.async_step_edit_shutter_form()

        options = {i: f"{s.get(CONF_NAME, 'Shutter')} ({s.get(CONF_COVER_ENTITY_ID, '')})" for i, s in enumerate(shutters)}
        schema = vol.Schema(
            {
                vol.Required("shutter_index"): vol.In(options),
                vol.Required("action"): vol.In(["edit", "remove"]),
            }
        )
        return self.async_show_form(
            step_id="edit_shutter",
            data_schema=schema,
        )

    async def async_step_edit_shutter_form(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Edit a shutter (form pre-filled)."""
        _raw = self._opts().get(CONF_SHUTTERS, [])
        shutters = list(_raw) if isinstance(_raw, list) else []
        idx = getattr(self, "_edit_index", 0)
        if idx >= len(shutters):
            return self.async_abort(reason="not_found")

        if user_input is not None:
            raw_cover = user_input.get(CONF_COVER_ENTITY_ID)
            cover_id = raw_cover[0] if isinstance(raw_cover, list) else (raw_cover or "")
            shutter_cfg = {
                CONF_COVER_ENTITY_ID: cover_id,
                CONF_NAME: user_input.get(CONF_NAME, "Shutter"),
                CONF_WINDOW_ENTITY_ID: "",
                CONF_WINDOW_OPEN_STATE: user_input.get(CONF_WINDOW_OPEN_STATE, DEFAULT_WINDOW_OPEN_STATE),
                CONF_WINDOW_TILTED_STATE: user_input.get(CONF_WINDOW_TILTED_STATE, DEFAULT_WINDOW_TILTED_STATE),
                CONF_POSITION_WHEN_WINDOW_OPEN: user_input.get(CONF_POSITION_WHEN_WINDOW_OPEN, 100),
                CONF_POSITION_WHEN_WINDOW_TILTED: user_input.get(CONF_POSITION_WHEN_WINDOW_TILTED, 50),
                CONF_LOCK_PROTECTION: user_input.get(CONF_LOCK_PROTECTION, False),
                CONF_MIN_POSITION_WHEN_OPEN: user_input.get(CONF_MIN_POSITION_WHEN_OPEN, DEFAULT_MIN_POSITION_WHEN_OPEN),
                CONF_TRIGGER_MODE: user_input.get(CONF_TRIGGER_MODE, TRIGGER_MODE_UP_DOWN),
                CONF_GROUP_UP: user_input.get(CONF_GROUP_UP, GROUP_LIVING),
                CONF_GROUP_DOWN: user_input.get(CONF_GROUP_DOWN, GROUP_LIVING),
                CONF_POSITION_OPEN: user_input.get(CONF_POSITION_OPEN, DEFAULT_POSITION_OPEN),
                CONF_POSITION_CLOSED: user_input.get(CONF_POSITION_CLOSED, DEFAULT_POSITION_CLOSED),
                CONF_POSITION_SUN_PROTECT: user_input.get(CONF_POSITION_SUN_PROTECT, DEFAULT_POSITION_SUN_PROTECT),
                CONF_BRIGHTNESS_TRIGGER: user_input.get(CONF_BRIGHTNESS_TRIGGER, BRIGHTNESS_OFF),
                CONF_DRIVE_AFTER_CLOSE: user_input.get(CONF_DRIVE_AFTER_CLOSE, False),
            }
            win_entity = user_input.get(CONF_WINDOW_ENTITY_ID)
            if win_entity:
                shutter_cfg[CONF_WINDOW_ENTITY_ID] = win_entity if isinstance(win_entity, str) else (win_entity[0] if win_entity else "")
            shutters[idx] = shutter_cfg
            new_opts = {**self._opts(), CONF_SHUTTERS: shutters}
            self.hass.config_entries.async_update_entry(self.config_entry, options=new_opts)
            return self.async_create_entry(title="", data=new_opts)

        s = shutters[idx]
        base = _shutter_schema()
        edit_schema = {}
        for k, v in base.items():
            def_val = s.get(k)
            if k in (CONF_COVER_ENTITY_ID, CONF_NAME):
                edit_schema[k] = vol.Required(k, default=def_val or "")
            else:
                edit_schema[k] = vol.Optional(k, default=def_val if def_val is not None else (v.default if hasattr(v, "default") else None))
        return self.async_show_form(
            step_id="edit_shutter_form",
            data_schema=vol.Schema(edit_schema),
        )
