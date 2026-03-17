"""Auto-Mode switches for Shutter Pilot (per area)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_NAME,
    CONF_AREA_AUTO_ENTITY_ID,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shutter Pilot auto-mode switches for a config entry."""
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []
    entities: list[ShutterPilotAutoModeSwitch] = []
    for area in areas:
        if not isinstance(area, dict):
            continue
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            continue
        name = str(area.get(CONF_AREA_NAME) or area_id).strip()
        entities.append(
            ShutterPilotAutoModeSwitch(
                hass=hass,
                entry=entry,
                area_id=area_id,
                name=f"Auto {name}",
            )
        )
    if entities:
        async_add_entities(entities)


class ShutterPilotAutoModeSwitch(RestoreEntity, SwitchEntity):
    """Switch to enable/disable automation for an area."""

    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        area_id: str,
        name: str,
    ) -> None:
        self._hass = hass
        self._entry = entry
        self._area_id = area_id

        # Entity name and unique_id – user can rename in UI
        self._attr_name = f"Shutter Pilot {name}"
        self._attr_unique_id = f"{entry.entry_id}_auto_area_{area_id}"

        # Default state before RestoreEntity kicks in
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        """Restore last state and register in hass.data and options."""
        await super().async_added_to_hass()

        # Restore last known state; default to ON on first install
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = str(last_state.state).lower() in ("on", "true", "1")
        else:
            self._attr_is_on = True

        # Mirror into hass.data so the automation logic can read it cheaply
        data = self._hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id, {}
        )
        auto_state = data.setdefault("auto_modes", {})
        auto_state[self._area_id] = self._attr_is_on

        # Mirror our entity_id into the corresponding area config for UI/runtime lookups
        opts = dict(self._entry.options or {})
        areas = opts.get(CONF_AREAS, [])
        if isinstance(areas, list):
            changed = False
            for a in areas:
                if not isinstance(a, dict):
                    continue
                if str(a.get(CONF_AREA_ID) or "").strip() != self._area_id:
                    continue
                if not str(a.get(CONF_AREA_AUTO_ENTITY_ID) or "").strip():
                    a[CONF_AREA_AUTO_ENTITY_ID] = self.entity_id
                    changed = True
            if changed:
                opts[CONF_AREAS] = areas
                self._hass.config_entries.async_update_entry(self._entry, options=opts)

        # Ensure state is written once after restore
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return bool(self._attr_is_on)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._set_state(False)

    def _set_state(self, value: bool) -> None:
        self._attr_is_on = bool(value)

        # Update shared state used by the schedulers/brightness/elevation
        data = self._hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id,
            {},
        )
        auto_state = data.setdefault("auto_modes", {})
        auto_state[self._area_id] = self._attr_is_on

        self.async_write_ha_state()

