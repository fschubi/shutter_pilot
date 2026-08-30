"""Shutter Pilot services - open_group, close_group, sun_protect_group (area-based)."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_MIN_DRIVE_GAP,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_DOWN_ID,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
    DEFAULT_MIN_DRIVE_GAP,
    MAX_MIN_DRIVE_GAP,
    ROLE_CLOSED,
    ROLE_OPEN,
    ROLE_SUN_PROTECT,
    ROLE_VENTILATION,
)
from .awning_guard import (
    async_retract_awning,
    clamp_to_rest,
    describe_reasons,
    guard_status,
    is_barred,
)
from .helpers import (
    filter_shutters_by_area,
    get_position_for_role,
    get_tilt_for_role,
    is_awning,
    has_guard,
    forget_shading_for_cover,
    clear_manual_override_for_covers,
    get_position_for_role,
    is_cover_sun_protected,
    only_awnings,
    resolve_shade_position,
    set_cover_position,
    shading_enabled,
)
from .window_helper import get_effective_close_position

_LOGGER = logging.getLogger(__name__)

SERVICE_OPEN_GROUP = "open_group"
SERVICE_STOP_GROUP = "stop_group"
SERVICE_CLOSE_GROUP = "close_group"
SERVICE_SUN_PROTECT_GROUP = "sun_protect_group"
SERVICE_VENTILATE_GROUP = "ventilate_group"
SERVICE_RETRACT_AWNINGS = "retract_awnings"
SERVICE_RESUME_AUTOMATION = "resume_automation"

# area_id is optional throughout: "all shutters up" is the button people build
# their dashboard around, and building it out of one call per area means the
# card has to be rewritten every time an area is added. Left out, the service
# walks every area – each shutter still lands in exactly one of them, because
# the up services filter on area_up_id and the down ones on area_down_id.
SERVICE_SCHEMA = vol.Schema(
    {vol.Optional("area_id"): str}
)
# "Storm warning received" is a house-wide event, not an area one.
RETRACT_SCHEMA = vol.Schema({vol.Optional("area_id"): str})
# Resuming is usually about one room – the nursery whose shutter was darkened
# by hand – so a single cover can be named. Without either argument it applies
# to the whole house, like the group services.
RESUME_SCHEMA = vol.Schema(
    {
        vol.Optional("area_id"): str,
        vol.Optional("entity_id"): vol.Any(str, [str]),
    }
)


async def _drive_group(
    hass: HomeAssistant,
    entry: ConfigEntry,
    shutters: list,
    role: str,
    direction: str,
    delay: int,
    area_id: str,
    apply_lock_protection: bool = False,
) -> None:
    """Drive every shutter of a group to its own configured position for `role`."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    areas = entry.options.get(CONF_AREAS, [])
    area_cfg = None
    if isinstance(areas, list):
        area_cfg = next(
            (
                a
                for a in areas
                if isinstance(a, dict)
                and str(a.get(CONF_AREA_ID) or "").strip() == area_id
            ),
            None,
        )
    driven = 0
    for shutter in shutters:
        cover = shutter.get(CONF_COVER_ENTITY_ID)
        if not cover:
            continue
        # The per-shutter automation switch is deliberately *not* asked here.
        # These services are the manual path – a shutter taken out of the
        # automation must still be drivable, or it cannot be tested after the
        # repair. The dashboard's area buttons do skip it: there the switch sits
        # two lines above the button, and driving it anyway read as a fault to
        # two people independently.
        if role == ROLE_SUN_PROTECT:
            if not shading_enabled(shutter):
                _LOGGER.info(
                    "%s: %s skipped – takes no part in the shading",
                    direction,
                    cover,
                )
                continue
            position = resolve_shade_position(hass, area_cfg, shutter, data)[0]
        else:
            position = get_position_for_role(shutter, role)
        # An awning that must not be out stays in, whoever asked. Judged by the
        # target rather than by the role: close_group on an awning means
        # "retract it", and refusing *that* during a storm would be absurd.
        if has_guard(shutter) and is_barred(data, cover):
            if clamp_to_rest(shutter, position) != position:
                _LOGGER.info(
                    "%s: %s skipped – awning protection active (%s)",
                    direction,
                    cover,
                    describe_reasons(guard_status(data, cover).get("reasons")),
                )
                continue
        tilt = get_tilt_for_role(shutter, role)
        eff_pos = position
        if apply_lock_protection:
            eff_pos = get_effective_close_position(hass, shutter, position)
        try:
            if driven > 0 and delay > 0:
                await asyncio.sleep(delay)
            await set_cover_position(
                hass,
                entry,
                cover,
                eff_pos,
                direction,
                tilt_position=tilt,
                area_id=area_id,
            )
            driven += 1
            if eff_pos != position:
                _LOGGER.info(
                    "%s: %s -> %d%% (Aussperrschutz: Tür offen)",
                    direction,
                    cover,
                    int(eff_pos),
                )
            if isinstance(data, dict):
                if role == ROLE_OPEN:
                    data.setdefault("covers_driven_up", set()).add(cover)
                    data.setdefault("covers_driven_down", set()).discard(cover)
                else:
                    data.setdefault("covers_driven_down", set()).add(cover)
                    data.setdefault("covers_driven_up", set()).discard(cover)
        except Exception as e:
            _LOGGER.warning("Failed %s %s: %s", direction, cover, e)


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register Shutter Pilot services."""
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []

    def _delay_for_area(area_id: str) -> int:
        for a in areas:
            if not isinstance(a, dict):
                continue
            if str(a.get(CONF_AREA_ID) or "").strip() != area_id:
                continue
            try:
                return max(0, int(a.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
            except (TypeError, ValueError):
                return DEFAULT_AREA_DRIVE_DELAY
        return DEFAULT_AREA_DRIVE_DELAY

    def _target_area_ids(call) -> list[str]:
        """The areas this call addresses – the named one, or all of them."""
        area_id = str(call.data.get("area_id") or "").strip()
        if area_id:
            return [area_id]
        return [
            str(a.get(CONF_AREA_ID) or "").strip()
            for a in areas
            if isinstance(a, dict) and str(a.get(CONF_AREA_ID) or "").strip()
        ]

    def _shutter_list() -> list:
        shutters = entry.options.get(CONF_SHUTTERS, [])
        if not isinstance(shutters, list):
            _LOGGER.warning(
                "Invalid shutters options type in group service: %r – resetting to empty list",
                type(shutters),
            )
            return []
        return shutters

    async def _run_group(
        call,
        role: str,
        label: str,
        use_up: bool,
        *,
        shutters_only: bool = False,
        apply_lock_protection: bool = False,
    ) -> None:
        for area_id in _target_area_ids(call):
            picked = filter_shutters_by_area(
                _shutter_list(), area_id, use_up=use_up, shutters_only=shutters_only
            )
            if not picked:
                continue
            await _drive_group(
                hass,
                entry,
                picked,
                role,
                f"{label}({area_id})",
                _delay_for_area(area_id),
                area_id,
                apply_lock_protection=apply_lock_protection,
            )

    async def open_group(call) -> None:
        await _run_group(call, ROLE_OPEN, "open_group", use_up=True)

    async def close_group(call) -> None:
        await _run_group(
            call, ROLE_CLOSED, "close_group", use_up=False, apply_lock_protection=True
        )

    async def sun_protect_group(call) -> None:
        await _run_group(
            call,
            ROLE_SUN_PROTECT,
            "sun_protect_group",
            use_up=False,
            apply_lock_protection=True,
        )

    async def ventilate_group(call) -> None:
        """Move a group to its ventilation position (tilted-window position)."""
        await _run_group(
            call,
            ROLE_VENTILATION,
            "ventilate_group",
            use_up=False,
            # Awnings have no ventilation position – it is the tilted-window one.
            shutters_only=True,
            # Der Aussperrschutz galt an jedem automatisierten Fahrweg – nur
            # hier nicht, und Lueften faehrt nach unten wie jedes Schliessen.
            apply_lock_protection=True,
        )

    async def stop_group(call) -> None:
        """Halt everything that is moving, area by area.

        No position and no role: a stop is the one command that means the same
        thing whichever way the cover was going, awnings included. Staggered
        like the rest all the same – a swallowed stop lets a shutter run to the
        end stop, one that arrives a second later does not.
        """
        try:
            gap = float(entry.options.get(CONF_MIN_DRIVE_GAP, DEFAULT_MIN_DRIVE_GAP) or 0)
        except (TypeError, ValueError):
            gap = 0.0
        seen: set[str] = set()
        covers: list[str] = []
        for area_id in _target_area_ids(call):
            for use_up in (True, False):
                for shutter in filter_shutters_by_area(
                    _shutter_list(), area_id, use_up=use_up
                ):
                    cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
                    if cover and cover not in seen:
                        seen.add(cover)
                        covers.append(cover)
        for i, cover in enumerate(covers):
            if i and gap > 0:
                await asyncio.sleep(min(gap, MAX_MIN_DRIVE_GAP))
            try:
                await hass.services.async_call(
                    "cover", "stop_cover", {"entity_id": cover}, blocking=True
                )
            except Exception as e:  # pragma: no cover - one cover must not stop the rest
                _LOGGER.warning("Failed stop %s: %s", cover, e)

    async def retract_awnings(call) -> None:
        """Pull every awning in at once, for an announced storm.

        No stagger and no drive gap: spacing four awnings ten seconds apart
        would leave the last one out for half a minute, and that is the half
        minute this service exists for.
        """
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if not isinstance(data, dict):
            return
        shutters = entry.options.get(CONF_SHUTTERS, [])
        if not isinstance(shutters, list):
            return
        area_id = str(call.data.get("area_id") or "").strip()
        targets = only_awnings(shutters)
        if area_id:
            targets = [
                s for s in targets
                if str(s.get(CONF_AREA_DOWN_ID) or "").strip() == area_id
            ]
        for shutter in targets:
            await async_retract_awning(hass, entry, data, shutter, ["service"])

    async def resume_automation(call) -> None:
        """Hand a shutter back to the automation after an outside drive.

        pcsv17's case: a helper switch darkens the nursery to 20 % while the
        baby sleeps and drives back up afterwards. Both drives are foreign
        ones, so the manual override blocks the next automated opening – and,
        less obviously, the shading still counts the shutter as shaded and
        therefore never brings it back to the shading height.

        Deliberately a service and not something that happens by itself: only
        the person in the room knows when the nap is over. Doing it
        automatically would haul the shutter back up a minute after somebody
        deliberately darkened the room, which is the opposite of what the
        override is for.
        """
        wanted = call.data.get("entity_id")
        if isinstance(wanted, str):
            wanted = [wanted]
        wanted_set = {str(x).strip() for x in (wanted or []) if str(x).strip()}

        targets: list[dict] = []
        for area_id in _target_area_ids(call):
            for shutter in filter_shutters_by_area(
                _shutter_list(), area_id, use_up=False
            ):
                cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
                if not cover or (wanted_set and cover not in wanted_set):
                    continue
                if not any(
                    str(t.get(CONF_COVER_ENTITY_ID) or "") == cover for t in targets
                ):
                    targets.append(shutter)
        if not targets:
            _LOGGER.debug("resume_automation: nothing matched")
            return

        data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if not isinstance(data, dict):
            return

        covers = [str(s.get(CONF_COVER_ENTITY_ID) or "").strip() for s in targets]
        await clear_manual_override_for_covers(hass, entry, covers)
        for cover in covers:
            forget_shading_for_cover(data, cover)

        # Let the shading decide first and *wait* for it: it knows the
        # conditions, the hysteresis and the second position, and duplicating
        # that here would be a second answer to the same question.
        evaluate = data.get("_elevation_evaluate")
        if callable(evaluate):
            await evaluate()

        # Whatever the shading did not claim belongs to the half of the day the
        # shutter is in. The scheduler's own bookkeeping says which one that is
        # – it is kept up to date by foreign drives too, since 2.17.0.
        down: set = data.get("covers_driven_down") or set()
        for shutter in targets:
            cover = str(shutter.get(CONF_COVER_ENTITY_ID) or "").strip()
            if is_cover_sun_protected(data, cover):
                continue
            role = ROLE_CLOSED if cover in down else ROLE_OPEN
            position = get_position_for_role(shutter, role)
            if role == ROLE_CLOSED:
                position = get_effective_close_position(hass, shutter, position)
            await set_cover_position(
                hass, entry, cover, position, "Resume automation"
            )
        _LOGGER.info(
            "resume_automation: %d cover(s) handed back to the automation",
            len(targets),
        )

    def _unregister() -> None:
        hass.services.async_remove(DOMAIN, SERVICE_RESUME_AUTOMATION)
        hass.services.async_remove(DOMAIN, SERVICE_RETRACT_AWNINGS)
        hass.services.async_remove(DOMAIN, SERVICE_OPEN_GROUP)
        hass.services.async_remove(DOMAIN, SERVICE_STOP_GROUP)
        hass.services.async_remove(DOMAIN, SERVICE_CLOSE_GROUP)
        hass.services.async_remove(DOMAIN, SERVICE_SUN_PROTECT_GROUP)
        hass.services.async_remove(DOMAIN, SERVICE_VENTILATE_GROUP)
        _LOGGER.debug("Services unregistered")

    hass.services.async_register(
        DOMAIN, SERVICE_OPEN_GROUP, open_group, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STOP_GROUP, stop_group, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLOSE_GROUP, close_group, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SUN_PROTECT_GROUP, sun_protect_group, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_VENTILATE_GROUP, ventilate_group, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RETRACT_AWNINGS, retract_awnings, schema=RETRACT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESUME_AUTOMATION, resume_automation, schema=RESUME_SCHEMA
    )
    entry.async_on_unload(_unregister)
    _LOGGER.info(
        "Services registered: open_group, close_group, stop_group, "
        "sun_protect_group, ventilate_group, retract_awnings, resume_automation"
    )
