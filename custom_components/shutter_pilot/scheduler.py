"""Time-based scheduler for shutter up/down (per area, time/sun modes)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    AREA_MODE_TIME,
    AREA_MODE_SUN,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_DRIVE_AFTER_CLOSE,
    ROLE_CLOSED,
    ROLE_CLOSED_ALT,
    ROLE_OPEN,
)
from .helpers import (
    resolve_close_role,
    clear_covers_driven_for_direction,
    clear_manual_override_for_covers,
    clear_stale_window_cycle_after_automated_up,
    filter_shutters_by_area,
    get_position_for_role,
    get_tilt_for_role,
    is_auto_enabled,
    is_shutter_automation_enabled,
    register_minute_callback,
    set_cover_position,
    should_skip_automated_up,
    sun_protect_area_ids_from_options,
)
from .schedule_times import (
    get_sun_mode_triggers,
    get_time_mode_triggers,
    parse_time,
)
from .window_helper import get_effective_close_position, is_window_open_or_tilted
from .group_actions import run_group_light_action

_LOGGER = logging.getLogger(__name__)

# Kept for backwards compatibility with existing imports/tests.
_parse_time = parse_time


async def setup_schedulers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up time-based and sun-based schedulers."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    data.setdefault("drive_after_close_pending", {})
    # Pending-Fahrten: Wenn Scheduler im Hoch-Fenster wegen Dunkelheit blockiert,
    # soll die Helligkeitslogik später „nachholen" dürfen (z. B. Living 05:00–06:00,
    # Lux steigt aber erst 06:33 über Schwelle).
    pending_up: dict[str, object] = data.setdefault("_pending_up", {})

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        _LOGGER.warning(
            "Invalid shutters options type in scheduler: %r – resetting to empty list",
            type(shutters),
        )
        shutters = []
    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []

    sun_protect_area_ids = sun_protect_area_ids_from_options(areas)
    areas_by_id = {
        str(a.get(CONF_AREA_ID) or ""): a for a in areas if isinstance(a, dict)
    }

    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())

    async def drive_shutters(
        shutter_list: list[dict],
        direction_up: bool,
        direction: str,
        delay: int,
        apply_lock_protection: bool = False,
        area_id: str = "",
    ) -> int:
        moved = 0
        driven_covers: list[str] = []
        area_cfg = areas_by_id.get(area_id)
        role = ROLE_OPEN if direction_up else ROLE_CLOSED
        for shutter in shutter_list:
            cover = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover:
                continue
            if not is_shutter_automation_enabled(hass, entry, shutter):
                _LOGGER.info("%s: %s übersprungen (Automatik am Rollladen aus)", direction, cover)
                continue
            # Some shutters should only close part way – against frost, or on a
            # mild evening. The area decides when, the shutter decides how far.
            shutter_role = role
            if not direction_up:
                shutter_role = resolve_close_role(hass, area_cfg, shutter, data)
                if shutter_role != ROLE_CLOSED:
                    _LOGGER.info(
                        "%s: %s closes only part way (%s)",
                        direction, cover, shutter_role,
                    )
            position = get_position_for_role(shutter, shutter_role)
            tilt = get_tilt_for_role(shutter, shutter_role)
            drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
            if apply_lock_protection and drive_after and is_window_open_or_tilted(hass, shutter):
                data["drive_after_close_pending"][cover] = {
                    "position": position,
                    "tilt": tilt,
                    "reason": direction,
                    "shutter": shutter,
                }
                _LOGGER.info(
                    "%s: %s Fenster offen – Fahrt wird nach Schließen ausgeführt (drive_after_close)",
                    direction, cover,
                )
                continue
            eff_pos = position
            if apply_lock_protection:
                eff_pos = get_effective_close_position(hass, shutter, position)
            try:
                if direction_up and should_skip_automated_up(
                    hass,
                    entry,
                    shutter,
                    data,
                    sun_protect_area_ids,
                    within_up_window=True,
                    area=area_cfg,
                ):
                    _LOGGER.info(
                        "%s: %s übersprungen (Sonnenschutz/manuelle Position)",
                        direction,
                        cover,
                    )
                    continue
                if moved > 0 and delay > 0:
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
                if direction_up:
                    covers_driven_up.add(cover)
                    covers_driven_down.discard(cover)
                    clear_stale_window_cycle_after_automated_up(data, cover)
                else:
                    covers_driven_down.add(cover)
                    covers_driven_up.discard(cover)
                driven_covers.append(cover)
                moved += 1
                if eff_pos != position:
                    _LOGGER.info("%s: %s -> %d%% (Aussperrschutz)", direction, cover, int(eff_pos))
            except Exception as e:
                _LOGGER.warning("Failed %s %s: %s", direction, cover, e)

        if driven_covers:
            await clear_manual_override_for_covers(hass, entry, driven_covers)
        return moved

    async def _run_up_async(area: dict, trigger: str = "scheduler") -> None:
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            return
        if not is_auto_enabled(hass, entry, area):
            _LOGGER.info("[%s] area=%s: auto disabled – skipping UP", trigger, area_id)
            return
        clear_covers_driven_for_direction(data, "up")
        filtered = filter_shutters_by_area(shutters, area_id, use_up=True)
        filtered = [s for s in filtered if (s.get(CONF_COVER_ENTITY_ID) or "") not in covers_driven_up]
        if not filtered:
            return
        pending_up.pop(area_id, None)
        try:
            delay = max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            delay = DEFAULT_AREA_DRIVE_DELAY
        moved = await drive_shutters(
            filtered, True, f"Schedule up ({area_id})", delay,
            apply_lock_protection=False, area_id=area_id,
        )
        if moved > 0:
            await run_group_light_action(hass, entry, area_id, "up")

    def _run_up(area: dict, trigger: str = "scheduler") -> None:
        hass.async_create_task(_run_up_async(area, trigger=trigger))

    async def _run_down_async(area: dict, trigger: str = "scheduler") -> None:
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            return
        if not is_auto_enabled(hass, entry, area):
            _LOGGER.info("[%s] area=%s: auto disabled – skipping DOWN", trigger, area_id)
            return
        clear_covers_driven_for_direction(data, "down")
        filtered = filter_shutters_by_area(shutters, area_id, use_up=False)
        filtered = [s for s in filtered if (s.get(CONF_COVER_ENTITY_ID) or "") not in covers_driven_down]
        if not filtered:
            return
        try:
            delay = max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            delay = DEFAULT_AREA_DRIVE_DELAY
        moved = await drive_shutters(
            filtered, False, f"Schedule down ({area_id})",
            delay, apply_lock_protection=True, area_id=area_id,
        )
        if moved > 0:
            await run_group_light_action(hass, entry, area_id, "down")

    def _run_down(area: dict, trigger: str = "scheduler") -> None:
        hass.async_create_task(_run_down_async(area, trigger=trigger))

    # Fixed-time schedule: run every minute, fire only once per event per day.
    # On setup/reload we pre-mark already-passed times for today to avoid
    # immediate catch-up movement after restart.
    fired_today = data.setdefault("_scheduler_fired", {})
    setup_now = dt_util.as_local(dt_util.now())
    setup_today = setup_now.date()
    setup_time = setup_now.time()
    for area in areas:
        if not isinstance(area, dict):
            continue
        if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_TIME:
            continue
        area_id = str(area.get(CONF_AREA_ID) or "")
        if not area_id:
            continue
        up_t, down_t = get_time_mode_triggers(hass, area, setup_now)
        if setup_time >= up_t:
            fired_today[f"up_{area_id}"] = setup_today
        if setup_time >= down_t:
            fired_today[f"down_{area_id}"] = setup_today

    fired_sun_up: dict[str, object] = data.setdefault("_sun_fired_up", {})
    fired_sun_down: dict[str, object] = data.setdefault("_sun_fired_down", {})

    # Sun mode: wie Zeit-Modus – bei Start/Reload kein sofortiges Nachholen-UP im Tagesfenster
    # (sonst z. B. Sonnenschutz-Teilposition wieder auf „offen" gezogen).
    for sun_area in areas:
        if not isinstance(sun_area, dict):
            continue
        if str(sun_area.get(CONF_AREA_MODE) or "") != AREA_MODE_SUN:
            continue
        sun_area_id = str(sun_area.get(CONF_AREA_ID) or "")
        if not sun_area_id:
            continue
        trig_up, trig_down = get_sun_mode_triggers(hass, sun_area, setup_now)
        if trig_up is None or trig_down is None:
            continue
        if trig_up <= setup_now < trig_down:
            fired_sun_up[sun_area_id] = setup_today
            _LOGGER.debug(
                "[sun-scheduler] area=%s: Start im Tagesfenster – UP für heute als erledigt markiert",
                sun_area_id,
            )
        if trig_down.date() == setup_today and setup_now >= trig_down:
            fired_sun_down[sun_area_id] = setup_today
            _LOGGER.debug(
                "[sun-scheduler] area=%s: Start nach Sonnenuntergang – DOWN für heute als erledigt markiert",
                sun_area_id,
            )

    def _sun_minute_tick(now_local: datetime) -> None:
        """Sun mode: drive by computed trigger times every minute.

        We do *not* rely on async_track_sunrise/sunset alone: after the astronomical
        sunrise, HA's next_rising points at tomorrow, so offset triggers for *today*
        are often never scheduled. A periodic check matches time/brightness reliability.
        """
        today = now_local.date()
        for area in areas:
            if not isinstance(area, dict):
                continue
            if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_SUN:
                continue
            area_id = str(area.get(CONF_AREA_ID) or "")
            if not area_id:
                continue
            trigger_up, trigger_down = get_sun_mode_triggers(hass, area, now_local)
            if trigger_up is None or trigger_down is None:
                continue

            # UP once per day: after sunrise+offset, before sunset+offset (day window)
            if fired_sun_up.get(area_id) != today:
                if trigger_up <= now_local < trigger_down and is_auto_enabled(
                    hass, entry, area
                ):
                    fired_sun_up[area_id] = today
                    _LOGGER.info(
                        "[sun-minute] area=%s: UP window (trigger=%s) – running UP",
                        area_id,
                        trigger_up.isoformat(),
                    )
                    _run_up(area, trigger="sun-minute")

            # DOWN once per day: after sunset+offset on that calendar day.
            # get_sun_mode_triggers() returns local time, so comparing its date
            # against the local date is sound – with a UTC value a late trigger
            # would fall on tomorrow's date here and never run.
            if fired_sun_down.get(area_id) != today:
                if (
                    trigger_down.date() == today
                    and now_local >= trigger_down
                    and is_auto_enabled(hass, entry, area)
                ):
                    fired_sun_down[area_id] = today
                    _LOGGER.info(
                        "[sun-minute] area=%s: DOWN (trigger=%s) – running DOWN",
                        area_id,
                        trigger_down.isoformat(),
                    )
                    _run_down(area, trigger="sun-minute")

    @callback
    def _scheduler_tick(now: datetime) -> None:
        now_local = dt_util.as_local(now)
        today = now_local.date()
        t = now_local.time()
        for area in areas:
            if not isinstance(area, dict):
                continue
            if str(area.get(CONF_AREA_MODE) or "") != AREA_MODE_TIME:
                continue
            area_id = str(area.get(CONF_AREA_ID) or "")
            if not area_id:
                continue
            up_t, down_t = get_time_mode_triggers(hass, area, now_local)
            if t >= up_t:
                key_up = f"up_{area_id}"
                if fired_today.get(key_up) != today:
                    fired_today[key_up] = today
                    _LOGGER.info("[time-scheduler] area=%s: time_up=%s reached – triggering UP", area_id, up_t)
                    _run_up(area, trigger="time-scheduler")
            if t >= down_t:
                key_down = f"down_{area_id}"
                if fired_today.get(key_down) != today:
                    fired_today[key_down] = today
                    _LOGGER.info("[time-scheduler] area=%s: time_down=%s reached – triggering DOWN", area_id, down_t)
                    _run_down(area, trigger="time-scheduler")

        _sun_minute_tick(now_local)

    register_minute_callback(data, "scheduler", _scheduler_tick)

    _LOGGER.info("Scheduler: %d Rollläden, Bereiche=%d", len(shutters), len(areas))
