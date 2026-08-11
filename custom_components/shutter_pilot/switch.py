"""Auto-Mode and master switches for Shutter Pilot."""

from __future__ import annotations

from copy import deepcopy
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
    CONF_COVER_ENTITY_ID,
    CONF_MASTER_ENTITY_ID,
    CONF_NAME,
    CONF_SHUTTERS,
    CONF_SHUTTER_AUTOMATION_ENABLED,
    CONF_SHUTTER_AUTO_ENTITY_ID,
)
from .helpers import is_awning

# Zustände, die keine Nutzerentscheidung sind: Die Entität war beim letzten
# Beenden noch nicht bereit oder der Wert stammt aus einer früheren
# Installation. In beiden Fällen muss der Schalter eingeschaltet starten –
# sonst steht die Automatik nach einer Neuinstallation still, ohne dass
# jemand sie ausgeschaltet hätte.
_ON_STATES = ("on", "true", "1")
_UNSET_STATES = ("", "unknown", "unavailable", "none")
# Kennzeichnet, aus welchem Config-Entry ein gespeicherter Zustand stammt.
# RestoreEntity merkt sich Zustände über die entity_id, nicht über die
# unique_id: Nach Entfernen und erneutem Hinzufügen bekommt der Schalter
# denselben Namen und würde sonst das alte "aus" erben.
ATTR_ENTRY_ID = "config_entry_id"


def _restored_is_on(last_state: Any, entry_id: str) -> bool:
    """Return the restored switch state, defaulting to on."""
    if last_state is None:
        return True
    stored_entry = str(last_state.attributes.get(ATTR_ENTRY_ID) or "")
    # Fehlt die Kennung, stammt der Zustand aus einer Version vor 2.4.1 –
    # dann gehört er zur laufenden Installation und bleibt gültig. Steht dort
    # ein anderes Entry, ist es eine Neuinstallation.
    if stored_entry and stored_entry != entry_id:
        return True
    value = str(last_state.state or "").strip().lower()
    if value in _UNSET_STATES:
        return True
    return value in _ON_STATES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shutter Pilot switches for a config entry."""
    entities: list[SwitchEntity] = [
        ShutterPilotMasterSwitch(hass=hass, entry=entry),
    ]

    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []
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

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    for index, shutter in enumerate(shutters):
        if not isinstance(shutter, dict):
            continue
        cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
        if not cover:
            continue
        # Der Name aus dem Panel ist der, unter dem der Nutzer den Rollladen
        # kennt – der gehört auch in die Entität. Ohne ihn der Anzeigename des
        # Covers, erst zuletzt die nackte Entity-ID.
        name = str(shutter.get(CONF_NAME) or "").strip()
        if not name:
            cover_state = hass.states.get(cover)
            name = str(
                (cover_state.attributes.get("friendly_name") if cover_state else "") or ""
            ).strip() or cover.split(".")[-1]
        # "Rollladen" statt "Auto": Bereiche heissen bereits "Auto <Bereich>",
        # und Bereich und Rollladen tragen oft denselben Namen (Wohnzimmer).
        # Sonst stünden zwei gleichnamige Schalter in der Liste und Home
        # Assistant hängte an einen davon ein "_2". Die Entity-ID bleibt über
        # die unique_id erhalten, wenn eine Markise umbenannt wird – umgekehrt
        # hiesse der Schalter einer Markise dauerhaft "Rollladen".
        entities.append(
            ShutterPilotShutterAutomationSwitch(
                hass=hass,
                entry=entry,
                index=index,
                cover_entity_id=cover,
                name=f"{'Markise' if is_awning(shutter) else 'Rollladen'} {name}",
                configured_on=bool(shutter.get(CONF_SHUTTER_AUTOMATION_ENABLED, True)),
            )
        )

    if entities:
        async_add_entities(entities)


class ShutterPilotMasterSwitch(RestoreEntity, SwitchEntity):
    """Global switch to enable/disable all Shutter Pilot automation."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:window-shutter-settings"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_name = "Shutter Pilot System"
        self._attr_unique_id = f"{entry.entry_id}_master"
        self._attr_is_on = True
        self._attr_extra_state_attributes = {ATTR_ENTRY_ID: entry.entry_id}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        self._attr_is_on = _restored_is_on(last_state, self._entry.entry_id)

        data = self._hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id, {}
        )
        data["master_enabled"] = self._attr_is_on

        opts = deepcopy(dict(self._entry.options or {}))
        if not str(opts.get(CONF_MASTER_ENTITY_ID) or "").strip():
            opts[CONF_MASTER_ENTITY_ID] = self.entity_id
            self._hass.config_entries.async_update_entry(self._entry, options=opts)

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
        data = self._hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id, {}
        )
        data["master_enabled"] = self._attr_is_on
        self.async_write_ha_state()


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
        self._attr_name = f"Shutter Pilot {name}"
        self._attr_unique_id = f"{entry.entry_id}_auto_area_{area_id}"
        self._attr_is_on = True
        self._attr_extra_state_attributes = {ATTR_ENTRY_ID: entry.entry_id}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        self._attr_is_on = _restored_is_on(last_state, self._entry.entry_id)

        data = self._hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id, {}
        )
        auto_state = data.setdefault("auto_modes", {})
        auto_state[self._area_id] = self._attr_is_on

        opts = deepcopy(dict(self._entry.options or {}))
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
        data = self._hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id,
            {},
        )
        auto_state = data.setdefault("auto_modes", {})
        auto_state[self._area_id] = self._attr_is_on
        self.async_write_ha_state()


class ShutterPilotShutterAutomationSwitch(RestoreEntity, SwitchEntity):
    """Switch to enable/disable automation for a single shutter.

    For a shutter that must not move for a while – a defective one waiting for
    a spare part, for instance. Manual actions stay available, so the shutter
    can still be driven by hand to test it.
    """

    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        index: int,
        cover_entity_id: str,
        name: str,
        configured_on: bool = True,
    ) -> None:
        self._hass = hass
        self._entry = entry
        self._index = index
        self._cover_entity_id = cover_entity_id
        self._configured_on = configured_on
        self._attr_name = f"Shutter Pilot {name}"
        # The cover entity id keeps the switch stable when a shutter is
        # renamed or moved in the list; the index only says where to write
        # the entity id back.
        slug = cover_entity_id.replace(".", "_")
        self._attr_unique_id = f"{entry.entry_id}_auto_shutter_{slug}"
        self._attr_is_on = True
        self._attr_extra_state_attributes = {ATTR_ENTRY_ID: entry.entry_id}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        # A shutter added with the checkbox already unticked has no stored
        # state yet – then the configured value decides, not the default "on".
        if last_state is None:
            self._attr_is_on = self._configured_on
        else:
            self._attr_is_on = _restored_is_on(last_state, self._entry.entry_id)
        self._publish()

        opts = deepcopy(dict(self._entry.options or {}))
        shutters = opts.get(CONF_SHUTTERS, [])
        if isinstance(shutters, list):
            changed = False
            for s in shutters:
                if not isinstance(s, dict):
                    continue
                if str(s.get(CONF_COVER_ENTITY_ID) or "").strip() != self._cover_entity_id:
                    continue
                if not str(s.get(CONF_SHUTTER_AUTO_ENTITY_ID) or "").strip():
                    s[CONF_SHUTTER_AUTO_ENTITY_ID] = self.entity_id
                    changed = True
            if changed:
                opts[CONF_SHUTTERS] = shutters
                self._hass.config_entries.async_update_entry(self._entry, options=opts)

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
        self._publish()
        self.async_write_ha_state()

    def _publish(self) -> None:
        """Mirror the state into runtime data, keyed by cover entity id."""
        data = self._hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id,
            {},
        )
        state = data.setdefault("shutter_automation", {})
        state[self._cover_entity_id] = self._attr_is_on
