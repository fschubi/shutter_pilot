"""Helper functions for area-based follow-up actions (e.g. lights)."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_DOWN_LIGHT_ENTITY,
    CONF_AREA_DOWN_LIGHT_BRIGHTNESS,
)


async def run_group_light_action(
    hass: HomeAssistant,
    entry: ConfigEntry,
    group: str,
    direction: str,
) -> None:
    """Execute configured light/switch action for an area and direction.

    direction: \"down\" = shutters close -> light on (optional brightness)
               \"up\"   = shutters open  -> light off
    """
    opts: dict[str, Any] = entry.options or {}
    areas = opts.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        return
    area_cfg = None
    for a in areas:
        if not isinstance(a, dict):
            continue
        if str(a.get(CONF_AREA_ID) or "").strip() == str(group or "").strip():
            area_cfg = a
            break
    if not area_cfg:
        return

    entity_id = str(area_cfg.get(CONF_AREA_DOWN_LIGHT_ENTITY) or "").strip()
    brightness_pct = area_cfg.get(CONF_AREA_DOWN_LIGHT_BRIGHTNESS)

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

