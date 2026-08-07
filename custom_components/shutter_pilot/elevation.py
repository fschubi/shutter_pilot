"""Sun protection per area - elevation range plus optional compass direction."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_SUN_PROTECT_ENABLED,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_DOWN_ID,
    CONF_AREA_UP_ID,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
    ROLE_OPEN,
    ROLE_SUN_PROTECT,
)
from .helpers import (
    get_azimuth_bounds,
    get_elevation_bounds,
    get_position_for_role,
    get_sun_angles,
    get_tilt_for_role,
    is_auto_enabled,
    is_shutter_automation_enabled,
    is_cover_sun_protected,
    register_minute_callback,
    resolve_shading_config,
    season_allows_shading,
    set_cover_position,
    set_cover_sun_protected,
    set_sun_protect_active,
    sun_extra_conditions_met,
    sun_protect_conditions_met,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted

_LOGGER = logging.getLogger(__name__)


async def setup_elevation_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up periodic sun evaluation for sun protection."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []

    protect_areas: list[dict] = []
    for a in areas:
        if not isinstance(a, dict):
            continue
        if not bool(a.get(CONF_AREA_SUN_PROTECT_ENABLED, False)):
            continue
        protect_areas.append(a)
    if not protect_areas:
        register_minute_callback(data, "elevation", None)
        return

    def _delay_for(area: dict) -> int:
        try:
            return max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            return DEFAULT_AREA_DRIVE_DELAY

    async def _drive_sun_protect(
        area: dict, elev: float, azim: float | None, targets: list[dict]
    ) -> int:
        """Drive the given shutters to their sun protection position."""
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            return 0
        moved = 0
        delay = _delay_for(area)
        idx = 0
        for shutter in targets:
            cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover_entity:
                continue
            pos = get_position_for_role(shutter, ROLE_SUN_PROTECT)
            tilt = get_tilt_for_role(shutter, ROLE_SUN_PROTECT)
            if shutter.get(CONF_DRIVE_AFTER_CLOSE, False) and is_window_open_or_tilted(
                hass, shutter
            ):
                data.setdefault("drive_after_close_pending", {})[cover_entity] = {
                    "position": pos,
                    "tilt": tilt,
                    "reason": "Sun protect",
                    "shutter": shutter,
                }
                continue
            pos = get_effective_close_position(hass, shutter, pos)
            e_min, e_max = get_elevation_bounds(area)
            _LOGGER.info(
                "[sun-protect] area=%s: elev=%.1f in [%.1f–%.1f], azimuth=%s → %s -> %d%%",
                area_id,
                elev,
                e_min,
                e_max,
                f"{azim:.1f}" if azim is not None else "n/a",
                cover_entity,
                int(pos),
            )
            if idx > 0 and delay > 0:
                await asyncio.sleep(delay)
            await set_cover_position(
                hass,
                entry,
                cover_entity,
                pos,
                f"Sun protect (area={area_id})",
                tilt_position=tilt,
                area_id=area_id,
            )
            idx += 1
            moved += 1
        return moved

    async def _release_sun_protect(
        area: dict, reason: str, targets: list[dict]
    ) -> int:
        """Drive the given shutters back to open once shading is not needed."""
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            return 0
        moved = 0
        delay = _delay_for(area)
        idx = 0
        for shutter in targets:
            cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover_entity:
                continue
            pos = get_position_for_role(shutter, ROLE_OPEN)
            tilt = get_tilt_for_role(shutter, ROLE_OPEN)
            _LOGGER.info(
                "[sun-protect] area=%s: release (%s) → %s -> %d%%",
                area_id, reason, cover_entity, int(pos),
            )
            if idx > 0 and delay > 0:
                await asyncio.sleep(delay)
            await set_cover_position(
                hass,
                entry,
                cover_entity,
                pos,
                f"Sun protect release (area={area_id})",
                tilt_position=tilt,
                area_id=area_id,
            )
            idx += 1
            moved += 1
        return moved

    async def _evaluate() -> None:
        elev, azim = get_sun_angles(hass)
        if elev is None:
            return

        protect_by_id = {
            str(a.get(CONF_AREA_ID) or "").strip(): a
            for a in protect_areas
            if str(a.get(CONF_AREA_ID) or "").strip()
        }
        to_shade: dict[str, list[dict]] = {}
        to_release: dict[str, list[tuple[dict, str]]] = {}

        for shutter in shutters:
            cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
            if not cover:
                continue

            # The area a shutter closes with owns its shading, and it alone
            # decides. Judging the release by the *up* area instead let two
            # areas contradict each other: one shaded, the other released, and
            # the shutter travelled back and forth every minute.
            area_id = str(shutter.get(CONF_AREA_DOWN_ID) or "").strip()
            area = protect_by_id.get(area_id)
            if area is None:
                # No shading here – but a leftover flag would keep blocking
                # automated opening through the area aggregate.
                set_cover_sun_protected(data, cover, False)
                continue

            if not is_auto_enabled(hass, entry, area):
                continue
            # Automation switched off at this shutter: neither shade nor
            # release it. The sun protection flag keeps its value, so a
            # shutter that was shaded before is released properly once the
            # automation is switched back on.
            if not is_shutter_automation_enabled(hass, entry, shutter):
                continue

            # A room may have windows facing different ways and watching
            # different sensors, so each shutter is judged with its own
            # merged config – area values apply where nothing is set.
            geo = resolve_shading_config(area, shutter)
            geometry_ok = sun_protect_conditions_met(elev, azim, geo)
            conditions_ok = sun_extra_conditions_met(hass, geo, data, cover)
            season_ok = season_allows_shading(area)
            should_protect = geometry_ok and conditions_ok and season_ok
            was_active = is_cover_sun_protected(data, cover)

            if should_protect:
                if not was_active:
                    to_shade.setdefault(area_id, []).append(shutter)
                    set_cover_sun_protected(data, cover, True)
                continue

            if not was_active:
                continue

            e_min, e_max = get_elevation_bounds(geo)
            set_cover_sun_protected(data, cover, False)
            if elev < e_min:
                # Below the range the shutters belong to the evening
                # schedule, not to shading. Drop the flag, do not drive.
                _LOGGER.debug(
                    "[sun-protect] %s: elev=%.1f below %.1f – off, no drive",
                    cover, elev, e_min,
                )
                continue

            if elev > e_max:
                reason = "sun above range"
            elif not geometry_ok:
                a_min, a_max = get_azimuth_bounds(geo)
                reason = f"sun left window direction ({a_min:.0f}°–{a_max:.0f}°)"
            elif not season_ok:
                reason = "outside shading season"
            else:
                # Geometry still fits, so a condition dropped out – clouds
                # moved in or it cooled down. Let the light back in.
                reason = "shading condition no longer met"
            to_release.setdefault(area_id, []).append((shutter, reason))

        for area_id, targets in to_shade.items():
            await _drive_sun_protect(protect_by_id[area_id], elev, azim, targets)
        for area_id, entries in to_release.items():
            area = protect_by_id[area_id]
            for reason in {r for _, r in entries}:
                await _release_sun_protect(
                    area, reason, [s for s, r in entries if r == reason]
                )

        # Area flag stays as the aggregate so brightness, the binary sensor,
        # diagnostics and the panel keep working unchanged.
        covers = data.get("sun_protect_covers", set())
        for area_id in protect_by_id:
            any_active = any(
                str(s.get(CONF_COVER_ENTITY_ID) or "") in covers
                for s in shutters
                if str(s.get(CONF_AREA_DOWN_ID) or "").strip() == area_id
            )
            set_sun_protect_active(data, area_id, any_active)

    def _tick(_now) -> None:
        hass.async_create_task(_evaluate())

    register_minute_callback(data, "elevation", _tick)
    hass.async_create_task(_evaluate())
    _LOGGER.info(
        "Sun protection: %d areas (elevation + azimuth, minute tick)",
        len(protect_areas),
    )
