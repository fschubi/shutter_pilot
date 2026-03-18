"""Config flow for Shutter Pilot integration."""

from __future__ import annotations

import logging
import re
from copy import deepcopy

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    # areas
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREA_MODE,
    AREA_MODE_TIME,
    AREA_MODE_BRIGHTNESS,
    AREA_MODE_SUN,
    AREA_MODES,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
    CONF_AREA_AUTO_ENTITY_ID,
    # area time
    CONF_AREA_TIME_UP,
    CONF_AREA_TIME_DOWN,
    DEFAULT_AREA_TIME_UP,
    DEFAULT_AREA_TIME_DOWN,
    # area sun
    CONF_AREA_SUNRISE_OFFSET,
    CONF_AREA_SUNSET_OFFSET,
    DEFAULT_AREA_SUNRISE_OFFSET,
    DEFAULT_AREA_SUNSET_OFFSET,
    # area brightness
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WE_UP_TO,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_DOWN_TO,
    DEFAULT_AREA_W_UP_FROM,
    DEFAULT_AREA_W_UP_TO,
    DEFAULT_AREA_W_DOWN_FROM,
    DEFAULT_AREA_W_DOWN_TO,
    DEFAULT_AREA_WE_UP_FROM,
    DEFAULT_AREA_WE_UP_TO,
    DEFAULT_AREA_WE_DOWN_FROM,
    DEFAULT_AREA_WE_DOWN_TO,
    # sun protect
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_AREA_ELEVATION_THRESHOLD,
    DEFAULT_AREA_ELEVATION_THRESHOLD,
    # light action
    CONF_AREA_DOWN_LIGHT_ENTITY,
    CONF_AREA_DOWN_LIGHT_BRIGHTNESS,
    DEFAULT_AREA_DOWN_LIGHT_BRIGHTNESS,
    # shutters
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
    CONF_AREA_UP_ID,
    CONF_AREA_DOWN_ID,
    CONF_POSITION_OPEN,
    CONF_POSITION_CLOSED,
    CONF_POSITION_SUN_PROTECT,
    CONF_DRIVE_AFTER_CLOSE,
    DEFAULT_POSITION_OPEN,
    DEFAULT_POSITION_CLOSED,
    DEFAULT_POSITION_SUN_PROTECT,
    DEFAULT_POSITION_WHEN_WINDOW_OPEN,
    DEFAULT_POSITION_WHEN_WINDOW_TILTED,
    DEFAULT_WINDOW_OPEN_STATE,
    DEFAULT_WINDOW_TILTED_STATE,
    DEFAULT_MIN_POSITION_WHEN_OPEN,
)

_LOGGER = logging.getLogger(__name__)

def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(name or "").strip().lower()).strip("_")
    return s or "bereich"


def _default_area(area_id: str, name: str, mode: str) -> dict:
    base = {
        CONF_AREA_ID: area_id,
        CONF_AREA_NAME: name,
        CONF_AREA_MODE: mode,
        CONF_AREA_DRIVE_DELAY: DEFAULT_AREA_DRIVE_DELAY,
        CONF_AREA_AUTO_ENTITY_ID: "",
        CONF_AREA_SUN_PROTECT_ENABLED: False,
        CONF_AREA_ELEVATION_THRESHOLD: DEFAULT_AREA_ELEVATION_THRESHOLD,
        CONF_AREA_DOWN_LIGHT_ENTITY: "",
        CONF_AREA_DOWN_LIGHT_BRIGHTNESS: DEFAULT_AREA_DOWN_LIGHT_BRIGHTNESS,
    }
    if mode == AREA_MODE_TIME:
        base.update(
            {
                CONF_AREA_TIME_UP: DEFAULT_AREA_TIME_UP,
                CONF_AREA_TIME_DOWN: DEFAULT_AREA_TIME_DOWN,
            }
        )
    elif mode == AREA_MODE_SUN:
        base.update(
            {
                CONF_AREA_SUNRISE_OFFSET: DEFAULT_AREA_SUNRISE_OFFSET,
                CONF_AREA_SUNSET_OFFSET: DEFAULT_AREA_SUNSET_OFFSET,
            }
        )
    else:
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
        _default_area("living", "Wohnbereich", AREA_MODE_TIME),
        _default_area("sleep", "Schlafbereich", AREA_MODE_TIME),
        _default_area("children", "Kinderbereich", AREA_MODE_TIME),
    ],
    CONF_SHUTTERS: [],
}


def _area_id_options(areas: list[dict]) -> list[str]:
    out: list[str] = []
    for a in areas or []:
        aid = str(a.get(CONF_AREA_ID) or "").strip()
        if aid:
            out.append(aid)
    return out


def _shutter_schema(areas: list[dict]) -> dict:
    """Return schema for a single shutter."""
    area_ids = _area_id_options(areas)
    default_area = area_ids[0] if area_ids else ""
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
        vol.Optional(CONF_AREA_UP_ID, default=default_area): vol.In(area_ids or [""]),
        vol.Optional(CONF_AREA_DOWN_ID, default=default_area): vol.In(area_ids or [""]),
        vol.Optional(CONF_POSITION_OPEN, default=DEFAULT_POSITION_OPEN): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(CONF_POSITION_CLOSED, default=DEFAULT_POSITION_CLOSED): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(
            CONF_POSITION_SUN_PROTECT, default=DEFAULT_POSITION_SUN_PROTECT
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
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
        """No public migration guarantees - keep entry as-is."""
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
        """Return the in-flow working options.

        Important: Do NOT call async_update_entry during the flow. Home Assistant
        persists options when the flow finishes via async_create_entry(data=...).
        Updating the entry directly can appear to work until restart, but the
        changes may not be written to storage reliably.
        """
        if not hasattr(self, "_working_opts") or not isinstance(getattr(self, "_working_opts"), dict):
            raw = dict(self.config_entry.options or {})
            if CONF_AREAS not in raw or not isinstance(raw.get(CONF_AREAS), list):
                raw[CONF_AREAS] = deepcopy(DEFAULT_OPTIONS[CONF_AREAS])
            if CONF_SHUTTERS not in raw or not isinstance(raw.get(CONF_SHUTTERS), list):
                raw[CONF_SHUTTERS] = []
            self._working_opts = raw
        return self._working_opts

    def _set_opts(self, new_opts: dict) -> None:
        self._working_opts = dict(new_opts or {})
        # Ensure required keys/types
        if CONF_AREAS not in self._working_opts or not isinstance(self._working_opts.get(CONF_AREAS), list):
            self._working_opts[CONF_AREAS] = deepcopy(DEFAULT_OPTIONS[CONF_AREAS])
        if CONF_SHUTTERS not in self._working_opts or not isinstance(self._working_opts.get(CONF_SHUTTERS), list):
            self._working_opts[CONF_SHUTTERS] = []

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Show options menu."""
        opts = self._opts()
        shutters = opts.get(CONF_SHUTTERS, [])
        areas = opts.get(CONF_AREAS, [])
        menu_opts = {
            "manage_areas": "Bereiche verwalten",
            "add_shutter": "Rollladen hinzufügen",
        }
        if isinstance(shutters, list) and shutters:
            menu_opts["edit_shutter"] = "Rollladen bearbeiten"
        menu_opts["done"] = "Fertig"
        return self.async_show_menu(
            step_id="init",
            menu_options=menu_opts,
            description_placeholders={
                "shutter_count": str(len(shutters) if isinstance(shutters, list) else 0),
                "area_count": str(len(areas) if isinstance(areas, list) else 0),
            },
        )

    async def async_step_manage_areas(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Manage areas (add/edit/delete)."""
        return self.async_show_menu(
            step_id="manage_areas",
            menu_options={
                "add_area": "Bereich hinzufügen",
                "edit_area": "Bereich bearbeiten/löschen",
                "init": "Zurück",
            },
        )

    async def async_step_settings_menu(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Legacy step kept for compatibility; redirect to new UI."""
        return await self.async_step_init()

    async def async_step_done(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Finish options flow."""
        opts = self._opts()
        areas = opts.get(CONF_AREAS, [])
        area_ids: list[str] = []
        if isinstance(areas, list):
            for a in areas:
                if isinstance(a, dict):
                    aid = str(a.get(CONF_AREA_ID) or "").strip()
                    if aid:
                        area_ids.append(aid)
        shutters = opts.get(CONF_SHUTTERS, [])
        shutter_count = len(shutters) if isinstance(shutters, list) else 0
        _LOGGER.warning(
            "Shutter Pilot OptionsFlow DONE persisting: areas=%s shutters=%d",
            area_ids,
            shutter_count,
        )
        return self.async_create_entry(title="", data=self._opts())

    def _eid(self, val):
        if isinstance(val, list):
            return val[0] if val else ""
        return val or ""

    def _merge_and_back(self, new_opts: dict) -> FlowResult:
        """Merge new options with existing and return to init menu."""
        merged = {**self._opts(), **(new_opts or {})}
        self._set_opts(merged)
        return self.async_show_menu(
            step_id="init",
            menu_options={
                "manage_areas": "Bereiche verwalten",
                "add_shutter": "Rollladen hinzufügen",
                "edit_shutter": "Rollladen bearbeiten",
                "done": "Fertig",
            },
            description_placeholders={
                "shutter_count": str(len(merged.get(CONF_SHUTTERS, []) or [])),
                "area_count": str(len(merged.get(CONF_AREAS, []) or [])),
            },
        )

    def _areas(self) -> list[dict]:
        areas = self._opts().get(CONF_AREAS, [])
        return areas if isinstance(areas, list) else []

    def _shutters(self) -> list[dict]:
        shutters = self._opts().get(CONF_SHUTTERS, [])
        return shutters if isinstance(shutters, list) else []

    def _unique_area_id(self, name: str) -> str:
        base = _slugify(name)
        existing = {str(a.get(CONF_AREA_ID) or "") for a in self._areas()}
        if base not in existing:
            return base
        i = 2
        while f"{base}_{i}" in existing:
            i += 1
        return f"{base}_{i}"

    def _area_details_schema(self, area: dict) -> vol.Schema:
        mode = str(area.get(CONF_AREA_MODE) or AREA_MODE_TIME)
        base: dict = {
            vol.Optional(
                CONF_AREA_DRIVE_DELAY,
                default=area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
            vol.Optional(
                CONF_AREA_SUN_PROTECT_ENABLED,
                default=bool(area.get(CONF_AREA_SUN_PROTECT_ENABLED, False)),
            ): bool,
            vol.Optional(
                CONF_AREA_ELEVATION_THRESHOLD,
                default=area.get(CONF_AREA_ELEVATION_THRESHOLD, DEFAULT_AREA_ELEVATION_THRESHOLD),
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Optional(
                CONF_AREA_DOWN_LIGHT_ENTITY,
                default=[area.get(CONF_AREA_DOWN_LIGHT_ENTITY, "")] if area.get(CONF_AREA_DOWN_LIGHT_ENTITY) else [],
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["light", "switch"], multiple=True),
            ),
            vol.Optional(
                CONF_AREA_DOWN_LIGHT_BRIGHTNESS,
                default=area.get(CONF_AREA_DOWN_LIGHT_BRIGHTNESS, DEFAULT_AREA_DOWN_LIGHT_BRIGHTNESS),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        }

        if mode == AREA_MODE_TIME:
            base.update(
                {
                    vol.Optional(
                        CONF_AREA_TIME_UP,
                        default=area.get(CONF_AREA_TIME_UP, DEFAULT_AREA_TIME_UP),
                    ): str,
                    vol.Optional(
                        CONF_AREA_TIME_DOWN,
                        default=area.get(CONF_AREA_TIME_DOWN, DEFAULT_AREA_TIME_DOWN),
                    ): str,
                }
            )
        elif mode == AREA_MODE_SUN:
            base.update(
                {
                    vol.Optional(
                        CONF_AREA_SUNRISE_OFFSET,
                        default=area.get(CONF_AREA_SUNRISE_OFFSET, DEFAULT_AREA_SUNRISE_OFFSET),
                    ): vol.All(vol.Coerce(int), vol.Range(min=-180, max=180)),
                    vol.Optional(
                        CONF_AREA_SUNSET_OFFSET,
                        default=area.get(CONF_AREA_SUNSET_OFFSET, DEFAULT_AREA_SUNSET_OFFSET),
                    ): vol.All(vol.Coerce(int), vol.Range(min=-180, max=180)),
                }
            )
        else:
            base.update(
                {
                    vol.Optional(
                        CONF_AREA_BRIGHTNESS_SENSOR,
                        default=[area.get(CONF_AREA_BRIGHTNESS_SENSOR, "")] if area.get(CONF_AREA_BRIGHTNESS_SENSOR) else [],
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", multiple=True),
                    ),
                    vol.Optional(
                        CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
                        default=area.get(
                            CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
                            DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100000)),
                    vol.Optional(
                        CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
                        default=area.get(
                            CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
                            DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100000)),
                    vol.Optional(CONF_AREA_W_UP_FROM, default=area.get(CONF_AREA_W_UP_FROM, DEFAULT_AREA_W_UP_FROM)): str,
                    vol.Optional(CONF_AREA_W_UP_TO, default=area.get(CONF_AREA_W_UP_TO, DEFAULT_AREA_W_UP_TO)): str,
                    vol.Optional(CONF_AREA_W_DOWN_FROM, default=area.get(CONF_AREA_W_DOWN_FROM, DEFAULT_AREA_W_DOWN_FROM)): str,
                    vol.Optional(CONF_AREA_W_DOWN_TO, default=area.get(CONF_AREA_W_DOWN_TO, DEFAULT_AREA_W_DOWN_TO)): str,
                    vol.Optional(CONF_AREA_WE_UP_FROM, default=area.get(CONF_AREA_WE_UP_FROM, DEFAULT_AREA_WE_UP_FROM)): str,
                    vol.Optional(CONF_AREA_WE_UP_TO, default=area.get(CONF_AREA_WE_UP_TO, DEFAULT_AREA_WE_UP_TO)): str,
                    vol.Optional(CONF_AREA_WE_DOWN_FROM, default=area.get(CONF_AREA_WE_DOWN_FROM, DEFAULT_AREA_WE_DOWN_FROM)): str,
                    vol.Optional(CONF_AREA_WE_DOWN_TO, default=area.get(CONF_AREA_WE_DOWN_TO, DEFAULT_AREA_WE_DOWN_TO)): str,
                }
            )
        return vol.Schema(base)

    async def async_step_add_area(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            name = str(user_input.get(CONF_AREA_NAME) or "").strip() or "Bereich"
            mode = user_input.get(CONF_AREA_MODE, AREA_MODE_TIME)
            if mode not in AREA_MODES:
                mode = AREA_MODE_TIME
            area_id = self._unique_area_id(name)
            self._pending_area = _default_area(area_id, name, mode)
            return await self.async_step_add_area_details()

        return self.async_show_form(
            step_id="add_area",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA_NAME): str,
                    vol.Required(CONF_AREA_MODE, default=AREA_MODE_TIME): vol.In(AREA_MODES),
                }
            ),
        )

    async def async_step_add_area_details(
        self, user_input: dict | None = None
    ) -> FlowResult:
        area = getattr(self, "_pending_area", None)
        if not isinstance(area, dict):
            return await self.async_step_manage_areas()

        if user_input is not None:
            cleaned = dict(user_input)
            cleaned[CONF_AREA_DOWN_LIGHT_ENTITY] = self._eid(
                user_input.get(CONF_AREA_DOWN_LIGHT_ENTITY)
            )
            cleaned[CONF_AREA_BRIGHTNESS_SENSOR] = self._eid(
                user_input.get(CONF_AREA_BRIGHTNESS_SENSOR)
            )
            area.update(cleaned)
            areas = self._areas()
            areas.append(area)
            new_opts = {**self._opts(), CONF_AREAS: areas}
            self._set_opts(new_opts)
            _LOGGER.warning(
                "Shutter Pilot OptionsFlow add_area updated: areas=%d last_id=%s",
                len(areas),
                str(area.get(CONF_AREA_ID) or ""),
            )
            self._pending_area = None
            return await self.async_step_manage_areas()

        return self.async_show_form(
            step_id="add_area_details",
            data_schema=self._area_details_schema(area),
        )

    async def async_step_edit_area(
        self, user_input: dict | None = None
    ) -> FlowResult:
        areas = self._areas()
        if not areas:
            return await self.async_step_manage_areas()

        if user_input is not None:
            idx = int(user_input.get("area_index"))
            action = user_input.get("action")
            if action == "remove":
                removed = areas.pop(idx)
                removed_id = str(removed.get(CONF_AREA_ID) or "")
                shutters = self._shutters()
                fallback_id = str(areas[0].get(CONF_AREA_ID)) if areas else ""
                for s in shutters:
                    if s.get(CONF_AREA_UP_ID) == removed_id:
                        s[CONF_AREA_UP_ID] = fallback_id
                    if s.get(CONF_AREA_DOWN_ID) == removed_id:
                        s[CONF_AREA_DOWN_ID] = fallback_id
                new_opts = {**self._opts(), CONF_AREAS: areas, CONF_SHUTTERS: shutters}
                self._set_opts(new_opts)
                _LOGGER.warning(
                    "Shutter Pilot OptionsFlow remove area updated: areas=%d shutters=%d",
                    len(areas),
                    len(shutters),
                )
                return await self.async_step_manage_areas()
            self._edit_area_index = idx
            return await self.async_step_edit_area_form()

        options = {
            i: f"{a.get(CONF_AREA_NAME,'Bereich')} ({a.get(CONF_AREA_ID,'')})"
            for i, a in enumerate(areas)
        }
        schema = vol.Schema(
            {
                vol.Required("area_index"): vol.In(options),
                vol.Required("action"): vol.In(["edit", "remove"]),
            }
        )
        return self.async_show_form(step_id="edit_area", data_schema=schema)

    async def async_step_edit_area_form(
        self, user_input: dict | None = None
    ) -> FlowResult:
        areas = self._areas()
        idx = int(getattr(self, "_edit_area_index", 0))
        if idx >= len(areas):
            return await self.async_step_manage_areas()
        area = dict(areas[idx])

        if user_input is not None:
            name = str(user_input.get(CONF_AREA_NAME) or "").strip() or area.get(CONF_AREA_NAME, "Bereich")
            mode = user_input.get(CONF_AREA_MODE, area.get(CONF_AREA_MODE, AREA_MODE_TIME))
            if mode not in AREA_MODES:
                mode = AREA_MODE_TIME
            area[CONF_AREA_NAME] = name
            area[CONF_AREA_MODE] = mode
            self._pending_area = area
            self._pending_area_edit_index = idx
            return await self.async_step_edit_area_details()

        return self.async_show_form(
            step_id="edit_area_form",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA_NAME, default=area.get(CONF_AREA_NAME, "")): str,
                    vol.Required(CONF_AREA_MODE, default=area.get(CONF_AREA_MODE, AREA_MODE_TIME)): vol.In(AREA_MODES),
                }
            ),
        )

    async def async_step_edit_area_details(
        self, user_input: dict | None = None
    ) -> FlowResult:
        area = getattr(self, "_pending_area", None)
        idx = int(getattr(self, "_pending_area_edit_index", -1))
        areas = self._areas()
        if not isinstance(area, dict) or idx < 0 or idx >= len(areas):
            return await self.async_step_manage_areas()

        if user_input is not None:
            cleaned = dict(user_input)
            cleaned[CONF_AREA_DOWN_LIGHT_ENTITY] = self._eid(
                user_input.get(CONF_AREA_DOWN_LIGHT_ENTITY)
            )
            cleaned[CONF_AREA_BRIGHTNESS_SENSOR] = self._eid(
                user_input.get(CONF_AREA_BRIGHTNESS_SENSOR)
            )
            area.update(cleaned)
            areas[idx] = area
            new_opts = {**self._opts(), CONF_AREAS: areas}
            self._set_opts(new_opts)
            _LOGGER.warning(
                "Shutter Pilot OptionsFlow edit_area updated: areas=%d id=%s",
                len(areas),
                str(area.get(CONF_AREA_ID) or ""),
            )
            self._pending_area = None
            self._pending_area_edit_index = None
            return await self.async_step_manage_areas()

        return self.async_show_form(
            step_id="edit_area_details",
            data_schema=self._area_details_schema(area),
        )

    async def async_step_settings_general(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Legacy step kept for compatibility; redirect to new UI."""
        return await self.async_step_init()

    async def async_step_settings_schedule_living(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Legacy step kept for compatibility; redirect to new UI."""
        return await self.async_step_manage_areas()

    async def async_step_settings_schedule_sleep(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Legacy step kept for compatibility; redirect to new UI."""
        return await self.async_step_manage_areas()

    async def async_step_settings_schedule_children(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Legacy step kept for compatibility; redirect to new UI."""
        return await self.async_step_manage_areas()

    async def async_step_add_shutter(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Add a shutter configuration."""
        if user_input is not None:
            shutters = self._shutters()
            raw_cover = user_input.get(CONF_COVER_ENTITY_ID)
            cover_id = raw_cover[0] if isinstance(raw_cover, list) else (raw_cover or "")
            areas = self._areas()
            default_area_id = str(areas[0].get(CONF_AREA_ID)) if areas else ""
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
                CONF_AREA_UP_ID: user_input.get(CONF_AREA_UP_ID, default_area_id),
                CONF_AREA_DOWN_ID: user_input.get(CONF_AREA_DOWN_ID, default_area_id),
                CONF_POSITION_OPEN: user_input.get(CONF_POSITION_OPEN, DEFAULT_POSITION_OPEN),
                CONF_POSITION_CLOSED: user_input.get(CONF_POSITION_CLOSED, DEFAULT_POSITION_CLOSED),
                CONF_POSITION_SUN_PROTECT: user_input.get(CONF_POSITION_SUN_PROTECT, DEFAULT_POSITION_SUN_PROTECT),
                CONF_DRIVE_AFTER_CLOSE: user_input.get(CONF_DRIVE_AFTER_CLOSE, False),
            }
            win_entity = user_input.get(CONF_WINDOW_ENTITY_ID)
            if win_entity:
                shutter_cfg[CONF_WINDOW_ENTITY_ID] = win_entity if isinstance(win_entity, str) else (win_entity[0] if win_entity else "")
            shutters.append(shutter_cfg)
            new_options = {**self._opts(), CONF_SHUTTERS: shutters}
            self._set_opts(new_options)
            _LOGGER.warning(
                "Shutter Pilot OptionsFlow add_shutter updated: shutters=%d",
                len(shutters),
            )
            return await self.async_step_init()

        return self.async_show_form(
            step_id="add_shutter",
            data_schema=vol.Schema(_shutter_schema(self._areas())),
        )

    def _edit_shutter_defaults(self, shutters: list, idx: int) -> dict:
        """Current values for the shutter at idx, for data_schema_defaults (pre-fill edit form).
        Keys must be strings (e.g. 'cover_entity_id') to match the serialized schema.
        """
        s = shutters[idx] if idx < len(shutters) else {}
        base = _shutter_schema(self._areas())
        out = {}
        for k in base:
            key_name = getattr(k, "schema", k)
            if hasattr(key_name, "schema"):
                key_name = getattr(key_name, "schema", key_name)
            if not isinstance(key_name, str):
                key_name = str(key_name)
            val = s.get(key_name)
            if val is not None:
                out[key_name] = val
            else:
                v = base[k]
                out[key_name] = getattr(v, "default", None)
            if out[key_name] is None and key_name in (
                CONF_COVER_ENTITY_ID,
                CONF_NAME,
                CONF_WINDOW_ENTITY_ID,
            ):
                out[key_name] = ""
        return out

    async def async_step_edit_shutter(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Select shutter to edit or remove."""
        shutters = self._shutters()

        if user_input is not None:
            idx = user_input.get("shutter_index")
            action = user_input.get("action")
            if idx is not None and action == "remove":
                shutters = [s for i, s in enumerate(shutters) if i != idx]
                new_opts = {**self._opts(), CONF_SHUTTERS: shutters}
                self._set_opts(new_opts)
                return self.async_create_entry(title="", data=new_opts)
            if idx is not None and action == "edit":
                self._edit_index = int(idx)
                defaults = self._edit_shutter_defaults(shutters, int(idx))
                schema = vol.Schema(_shutter_schema(self._areas()))
                try:
                    if hasattr(self, "add_suggested_values_to_schema"):
                        schema = self.add_suggested_values_to_schema(schema, defaults)
                except Exception:
                    pass
                try:
                    result = self.async_show_form(
                        step_id="edit_shutter_form",
                        data_schema=schema,
                        data_schema_defaults=defaults,
                    )
                except TypeError:
                    result = self.async_show_form(
                        step_id="edit_shutter_form",
                        data_schema=schema,
                    )
                if isinstance(result, dict):
                    result["data_schema_defaults"] = defaults
                return result

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
        """Edit a shutter (form pre-filled). Called when user submits the edit form."""
        shutters = self._shutters()
        idx = getattr(self, "_edit_index", 0)
        if idx >= len(shutters):
            return self.async_abort(reason="not_found")

        if user_input is not None and "shutter_index" not in user_input and "action" not in user_input:
            raw_cover = user_input.get(CONF_COVER_ENTITY_ID)
            cover_id = raw_cover[0] if isinstance(raw_cover, list) else (raw_cover or "")
            areas = self._areas()
            default_area_id = str(areas[0].get(CONF_AREA_ID)) if areas else ""
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
                CONF_AREA_UP_ID: user_input.get(CONF_AREA_UP_ID, default_area_id),
                CONF_AREA_DOWN_ID: user_input.get(CONF_AREA_DOWN_ID, default_area_id),
                CONF_POSITION_OPEN: user_input.get(CONF_POSITION_OPEN, DEFAULT_POSITION_OPEN),
                CONF_POSITION_CLOSED: user_input.get(CONF_POSITION_CLOSED, DEFAULT_POSITION_CLOSED),
                CONF_POSITION_SUN_PROTECT: user_input.get(CONF_POSITION_SUN_PROTECT, DEFAULT_POSITION_SUN_PROTECT),
                CONF_DRIVE_AFTER_CLOSE: user_input.get(CONF_DRIVE_AFTER_CLOSE, False),
            }
            win_entity = user_input.get(CONF_WINDOW_ENTITY_ID)
            if win_entity:
                shutter_cfg[CONF_WINDOW_ENTITY_ID] = win_entity if isinstance(win_entity, str) else (win_entity[0] if win_entity else "")
            shutters[idx] = shutter_cfg
            new_opts = {**self._opts(), CONF_SHUTTERS: shutters}
            self._set_opts(new_opts)
            _LOGGER.warning(
                "Shutter Pilot OptionsFlow edit_shutter_form updated: shutters=%d",
                len(shutters),
            )
            return self.async_create_entry(title="", data=new_opts)

        defaults = self._edit_shutter_defaults(shutters, idx)
        schema = vol.Schema(_shutter_schema(self._areas()))
        try:
            if hasattr(self, "add_suggested_values_to_schema"):
                schema = self.add_suggested_values_to_schema(schema, defaults)
        except Exception:
            pass
        try:
            result = self.async_show_form(
                step_id="edit_shutter_form",
                data_schema=schema,
                data_schema_defaults=defaults,
            )
        except TypeError:
            result = self.async_show_form(
                step_id="edit_shutter_form",
                data_schema=schema,
            )
        if isinstance(result, dict):
            result["data_schema_defaults"] = defaults
        return result
