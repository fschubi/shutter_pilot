"""Auto-Mode switches for Shutter Pilot.

These simple switch entities allow enabling/disabling the automation per group
directly from the UI (Dashboard). They default to ON and remember their last
state across restarts.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
    CONF_AUTO_LIVING,
    CONF_AUTO_SLEEP,
    CONF_AUTO_CHILDREN,
)


AUTO_GROUPS = (
    (GROUP_LIVING, "Auto mode Living", CONF_AUTO_LIVING),
    (GROUP_SLEEP, "Auto mode Sleep", CONF_AUTO_SLEEP),
    (GROUP_CHILDREN, "Auto mode Children", CONF_AUTO_CHILDREN),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shutter Pilot auto-mode switches for a config entry."""
    entities: list[ShutterPilotAutoModeSwitch] = []
    for group, name, conf_key in AUTO_GROUPS:
        entities.append(
            ShutterPilotAutoModeSwitch(
                hass=hass,
                entry=entry,
                group=group,
                name=name,
                conf_key=conf_key,
            )
        )
    if entities:
        async_add_entities(entities)


class ShutterPilotAutoModeSwitch(RestoreEntity, SwitchEntity):
    """Switch to enable/disable automation for a group."""

    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        group: str,
        name: str,
        conf_key: str,
    ) -> None:
        self._hass = hass
        self._entry = entry
        self._group = group
        self._conf_key = conf_key

        # Entity name and unique_id – user can rename in UI
        self._attr_name = f"Shutter Pilot {name}"
        self._attr_unique_id = f"{entry.entry_id}_auto_{group}"

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
        auto_state[self._group] = self._attr_is_on

        # If no explicit entity has been configured yet for this group,
        # pre-fill our own entity_id into the options so the existing
        # _is_auto_enabled() helpers keep working without changes.
        key_map = {
            GROUP_LIVING: CONF_AUTO_LIVING,
            GROUP_SLEEP: CONF_AUTO_SLEEP,
            GROUP_CHILDREN: CONF_AUTO_CHILDREN,
        }
        key = key_map.get(self._group, self._conf_key)
        opts = dict(self._entry.options)
        if not opts.get(key):
            opts[key] = self.entity_id
            self._hass.config_entries.async_update_entry(
                self._entry,
                options=opts,
            )

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
        auto_state[self._group] = self._attr_is_on

        self.async_write_ha_state()

