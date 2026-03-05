"""Helper functions for group-based follow-up actions (e.g. lights)."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LIVING_DOWN_LIGHT_ENTITY,
    CONF_LIVING_DOWN_LIGHT_BRIGHTNESS,
    CONF_SLEEP_DOWN_LIGHT_ENTITY,
    CONF_SLEEP_DOWN_LIGHT_BRIGHTNESS,
    CONF_CHILDREN_DOWN_LIGHT_ENTITY,
    CONF_CHILDREN_DOWN_LIGHT_BRIGHTNESS,
    GROUP_LIVING,
    GROUP_SLEEP,
    GROUP_CHILDREN,
)


async def run_group_light_action(
    hass: HomeAssistant,
    entry: ConfigEntry,
    group: str,
    direction: str,
) -> None:
    """Execute configured light/switch action for a group and direction.

    direction: \"down\" = shutters close -> light on (optional brightness)
               \"up\"   = shutters open  -> light off
    """
    opts: dict[str, Any] = entry.options or {}

    if group == GROUP_LIVING:
        entity_id = str(opts.get(CONF_LIVING_DOWN_LIGHT_ENTITY) or "").strip()
        brightness_pct = opts.get(CONF_LIVING_DOWN_LIGHT_BRIGHTNESS)
    elif group == GROUP_SLEEP:
        entity_id = str(opts.get(CONF_SLEEP_DOWN_LIGHT_ENTITY) or "").strip()
        brightness_pct = opts.get(CONF_SLEEP_DOWN_LIGHT_BRIGHTNESS)
    elif group == GROUP_CHILDREN:
        entity_id = str(opts.get(CONF_CHILDREN_DOWN_LIGHT_ENTITY) or "").strip()
        brightness_pct = opts.get(CONF_CHILDREN_DOWN_LIGHT_BRIGHTNESS)
    else:
        return

    if not entity_id:
        return

    domain = entity_id.split(".", 1)[0]
    is_light = domain == "light"
    is_switch = domain == "switch"
    if not (is_light or is_switch):
        return

    if direction == "down":
        service_domain = "light" if is_light else "switch"
        service_name = "turn_on"
        data: dict[str, Any] = {"entity_id": entity_id}
        if is_light and brightness_pct is not None:
            try:
                pct = int(brightness_pct)
            except (TypeError, ValueError):
                pct = None
            if pct is not None and 0 < pct <= 100:
                # Map 1–100% to 1–255 brightness
                data["brightness"] = max(1, min(255, round(255 * pct / 100)))
    elif direction == "up":
        service_domain = "light" if is_light else "switch"
        service_name = "turn_off"
        data = {"entity_id": entity_id}
    else:
        return

    try:
        await hass.services.async_call(
            service_domain,
            service_name,
            data,
            blocking=True,
        )
    except Exception:  # pragma: no cover - defensive
        # Fehler bewusst nur schlucken, damit Rollladen-Fahrt nicht fehlschlägt
        return

