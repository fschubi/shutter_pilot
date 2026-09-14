"""Brightness sensor logic - per area (brightness mode)."""

from __future__ import annotations

import asyncio
import logging
import time as time_mod
from datetime import datetime, time, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_AREA_ID,
    CONF_AREA_MODE,
    AREA_MODE_BRIGHTNESS,
    CONF_AREA_B_DOWN_AFTER_SUNSET,
    CONF_AREA_B_LATEST_DOWN,
    CONF_AREA_B_LATEST_DOWN_ENABLED,
    CONF_AREA_B_LATEST_UP,
    CONF_AREA_B_LATEST_UP_ENABLED,
    CONF_AREA_B_UP_BEFORE_SUNRISE,
    CONF_AREA_B_WE_LATEST_DOWN,
    CONF_AREA_B_WE_LATEST_UP,
    DEFAULT_AREA_B_LATEST_DOWN,
    DEFAULT_AREA_B_LATEST_UP,
    CONF_AREA_BRIGHTNESS_SENSOR,
    CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    CONF_AREA_BRIGHTNESS_UP_THRESHOLD,
    CONF_AREA_LUX_HOLD,
    DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD,
    DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD,
    DEFAULT_AREA_LUX_HOLD,
    MAX_AREA_LUX_HOLD,
    CONF_AREA_W_UP_FROM,
    CONF_AREA_W_UP_TO,
    CONF_AREA_W_DOWN_FROM,
    CONF_AREA_W_DOWN_TO,
    CONF_AREA_WE_UP_FROM,
    CONF_AREA_WE_UP_TO,
    CONF_AREA_WE_DOWN_FROM,
    CONF_AREA_WE_DOWN_TO,
    CONF_AREA_DRIVE_DELAY,
    DEFAULT_AREA_DRIVE_DELAY,
    CONF_SHUTTERS,
    CONF_COVER_ENTITY_ID,
    CONF_AREA_UP_ID,
    CONF_AREA_DOWN_ID,
    CONF_DRIVE_AFTER_CLOSE,
    ROLE_CLOSED,
    ROLE_OPEN,
)
from .helpers import (
    automated_up_blocked,
    clear_manual_override_for_covers,
    clear_stale_window_cycle_after_automated_up,
    get_position_for_role,
    get_tilt_for_role,
    is_auto_enabled,
    is_shutter_automation_enabled,
    only_shutters,
    register_minute_callback,
    remember_drive_after_close,
    resolve_close_role,
    set_cover_position,
    should_skip_automated_up,
    sun_protect_area_ids_from_options,
)
from .window_helper import (
    get_deferred_close_position,
    get_effective_close_position,
    is_window_open_or_tilted,
)
from .group_actions import run_group_light_action
from .schedule_times import (
    _local_sun_time,
    infer_today_sun_time,
    is_weekend_schedule,
    parse_time,
)

_LOGGER = logging.getLogger(__name__)

_parse_time = parse_time


def _sun_bound_ok(
    hass: HomeAssistant | None, area: dict, now: datetime, direction: str
) -> bool:
    """True unless a sun-relative bound still blocks this direction.

    The clock windows cannot express "not before sunset minus 60 minutes",
    because sunset moves through the year. Without it a thunderstorm in the
    afternoon pushed the lux below the threshold and closed the shutters in
    broad daylight.
    """
    if hass is None:
        return True
    key = (
        CONF_AREA_B_DOWN_AFTER_SUNSET
        if direction == "down"
        else CONF_AREA_B_UP_BEFORE_SUNRISE
    )
    raw = area.get(key)
    if raw is None or str(raw).strip() == "":
        return True
    try:
        offset = int(raw)
    except (TypeError, ValueError):
        return True

    sun_state = hass.states.get("sun.sun")
    if sun_state is None:
        # No sun data – never block, same fail-open rule as everywhere else.
        return True
    attrs = sun_state.attributes or {}
    now_local = dt_util.as_local(now)
    event = _local_sun_time(
        attrs.get("next_setting" if direction == "down" else "next_rising")
    )
    today = infer_today_sun_time(event, now_local)
    if today is None:
        return True

    if direction == "down":
        # "Not before sunset minus N minutes".
        return now_local >= today - timedelta(minutes=offset)
    # "Not before sunrise minus N minutes".
    return now_local >= today - timedelta(minutes=offset)


def _latest_deadline(
    hass: HomeAssistant | None, area: dict, now: datetime, direction: str
) -> time | None:
    """The clock time this direction runs at regardless of the lux value.

    None means no deadline: the option is off, which is the default. The
    weekend value falls back to the weekday one when left empty, like every
    other weekend value in this integration.
    """
    if direction == "up":
        enabled_key = CONF_AREA_B_LATEST_UP_ENABLED
        week_key, we_key = CONF_AREA_B_LATEST_UP, CONF_AREA_B_WE_LATEST_UP
        default = DEFAULT_AREA_B_LATEST_UP
    else:
        enabled_key = CONF_AREA_B_LATEST_DOWN_ENABLED
        week_key, we_key = CONF_AREA_B_LATEST_DOWN, CONF_AREA_B_WE_LATEST_DOWN
        default = DEFAULT_AREA_B_LATEST_DOWN
    if not bool(area.get(enabled_key, False)):
        return None

    raw = ""
    if is_weekend_schedule(hass, area, now):
        raw = str(area.get(we_key) or "").strip()
    if not raw:
        raw = str(area.get(week_key) or "").strip()
    if not raw:
        raw = default
    return parse_time(raw, parse_time(default))


def _area_window(
    area: dict, now: datetime, direction: str, hass: HomeAssistant | None = None
) -> bool:
    """True if `now` lies inside the allowed window. direction: 'up' or 'down'."""
    if not _sun_bound_ok(hass, area, now, direction):
        return False
    is_we = is_weekend_schedule(hass, area, now)
    if direction == "up":
        f_key = CONF_AREA_WE_UP_FROM if is_we else CONF_AREA_W_UP_FROM
        t_key = CONF_AREA_WE_UP_TO if is_we else CONF_AREA_W_UP_TO
    else:
        f_key = CONF_AREA_WE_DOWN_FROM if is_we else CONF_AREA_W_DOWN_FROM
        t_key = CONF_AREA_WE_DOWN_TO if is_we else CONF_AREA_W_DOWN_TO
    start = parse_time(area.get(f_key, "00:00"))
    end = parse_time(area.get(t_key, "23:59"))
    t = now.time()
    if start <= end:
        return start <= t <= end
    return t >= start or t <= end


async def setup_brightness_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up brightness sensor listener."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    for unsub in data.get("_brightness_unsubs", []):
        unsub()
    data["_brightness_unsubs"] = []

    covers_driven_down: set[str] = data.setdefault("covers_driven_down", set())
    covers_driven_up: set[str] = data.setdefault("covers_driven_up", set())
    pending_up = data.setdefault("_pending_up", {})

    areas = entry.options.get(CONF_AREAS, [])
    if not isinstance(areas, list):
        areas = []
    brightness_areas: list[dict] = []
    for a in areas:
        if not isinstance(a, dict):
            continue
        if str(a.get(CONF_AREA_MODE) or "") != AREA_MODE_BRIGHTNESS:
            continue
        sensor = str(a.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
        if sensor:
            brightness_areas.append(a)
    if not brightness_areas:
        _LOGGER.debug("No brightness areas configured, skipping")
        register_minute_callback(data, "brightness", None)
        return

    shutters = entry.options.get(CONF_SHUTTERS, [])
    if not isinstance(shutters, list):
        shutters = []

    raw_areas_opts = entry.options.get(CONF_AREAS, [])
    if not isinstance(raw_areas_opts, list):
        raw_areas_opts = []
    sun_protect_area_ids = sun_protect_area_ids_from_options(raw_areas_opts)

    async def _set_cover_position_with_delay(
        entity_id: str,
        position: float,
        reason: str,
        delay: int,
        index: int,
        tilt: float | None = None,
        area_id: str = "",
    ) -> None:
        if delay > 0 and index > 0:
            await asyncio.sleep(delay * index)
        await set_cover_position(
            hass,
            entry,
            entity_id,
            position,
            reason,
            tilt_position=tilt,
            area_id=area_id,
        )

    def _delay_for(area: dict) -> int:
        try:
            return max(0, int(area.get(CONF_AREA_DRIVE_DELAY, DEFAULT_AREA_DRIVE_DELAY)))
        except (TypeError, ValueError):
            return DEFAULT_AREA_DRIVE_DELAY

    def _run_down(area: dict, area_id: str, reason: str) -> bool:
        """Close every shutter of this area that is not closed already."""
        drive_delay = _delay_for(area)
        idx = 0
        moved = False
        down_covers: list[str] = []
        for shutter in only_shutters(
            [s for s in shutters if str(s.get(CONF_AREA_DOWN_ID) or "") == area_id]
        ):
            cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover_entity:
                continue
            if cover_entity in covers_driven_down:
                continue
            if not is_shutter_automation_enabled(hass, entry, shutter):
                continue
            # Same decision as the scheduler: a shutter that must not
            # freeze shut, or only close part way on a mild evening,
            # has to behave that way here too.
            close_role = resolve_close_role(hass, area, shutter, data)
            pos = get_position_for_role(shutter, close_role)
            tilt = get_tilt_for_role(shutter, close_role)
            drive_after = shutter.get(CONF_DRIVE_AFTER_CLOSE, False)
            if drive_after and is_window_open_or_tilted(hass, shutter):
                remember_drive_after_close(
                    hass, entry, data, cover_entity,
                    position=pos, tilt=tilt,
                    reason=reason, shutter=shutter,
                )
                # Wie im Scheduler: die Fahrt gilt als erledigt, sie
                # wartet nur noch aufs Fenster. Sonst ueberspringt der
                # naechste Morgen genau diesen Rollladen – und der
                # Merker wuerde hier jede Minute neu geschrieben.
                covers_driven_down.add(cover_entity)
                covers_driven_up.discard(cover_entity)
                # Optional: schon so weit fahren, wie das offene Fenster es
                # zulaesst. Die volle Fahrt bleibt vorgemerkt.
                vent_pos = get_deferred_close_position(hass, shutter)
                if vent_pos is not None:
                    down_covers.append(cover_entity)
                    hass.async_create_task(
                        _set_cover_position_with_delay(
                            cover_entity, vent_pos,
                            f"{reason} (Fenster offen – Lüftungsposition)",
                            drive_delay, idx, area_id=area_id,
                        )
                    )
                    idx += 1
                    moved = True
                continue
            pos = get_effective_close_position(hass, shutter, pos)
            down_covers.append(cover_entity)
            hass.async_create_task(
                _set_cover_position_with_delay(
                    cover_entity, pos, reason, drive_delay, idx,
                    tilt=tilt, area_id=area_id,
                )
            )
            idx += 1
            covers_driven_down.add(cover_entity)
            covers_driven_up.discard(cover_entity)
            moved = True

        if moved:
            hass.async_create_task(
                clear_manual_override_for_covers(hass, entry, down_covers)
            )
            hass.async_create_task(run_group_light_action(hass, entry, area_id, "down"))
        return moved

    def _run_up(area: dict, area_id: str, reason: str, within_up_window: bool) -> bool:
        """Open every shutter of this area that shading and manual use allow."""
        # Both up paths – the lux threshold and the deadline – come through
        # here, so the holiday and weekend gates cannot drift apart between
        # them. Closing is untouched on purpose.
        blocked = automated_up_blocked(hass, area, data)
        if blocked:
            _LOGGER.info(
                "Brightness up: area %s blocked (%s) – shutters stay down",
                area_id, blocked,
            )
            return False
        # Shading is judged per shutter inside the loop. Asking the
        # area aggregate here as well held back every window of the
        # room as soon as a single one was shaded – rooms whose windows
        # face different ways are exactly the case that has its own
        # sensors and its own direction.
        drive_delay = _delay_for(area)
        idx = 0
        moved = False
        up_covers: list[str] = []
        for shutter in only_shutters(
            [s for s in shutters if str(s.get(CONF_AREA_UP_ID) or "") == area_id]
        ):
            cover_entity = shutter.get(CONF_COVER_ENTITY_ID)
            if not cover_entity:
                continue
            if cover_entity in covers_driven_up:
                continue
            if not is_shutter_automation_enabled(hass, entry, shutter):
                continue
            if should_skip_automated_up(
                hass,
                entry,
                shutter,
                data,
                sun_protect_area_ids,
                within_up_window=within_up_window,
                area=area,
            ):
                _LOGGER.info(
                    "Brightness up: %s übersprungen (Sonnenschutz/manuelle Position)",
                    cover_entity,
                )
                continue
            pos = get_position_for_role(shutter, ROLE_OPEN)
            tilt = get_tilt_for_role(shutter, ROLE_OPEN)
            _LOGGER.info("Brightness up: driving %s -> %d%%", cover_entity, pos)
            up_covers.append(cover_entity)
            hass.async_create_task(
                _set_cover_position_with_delay(
                    cover_entity, pos, reason, drive_delay, idx,
                    tilt=tilt, area_id=area_id,
                )
            )
            idx += 1
            covers_driven_up.add(cover_entity)
            covers_driven_down.discard(cover_entity)
            clear_stale_window_cycle_after_automated_up(data, cover_entity)
            moved = True

        if moved:
            hass.async_create_task(
                clear_manual_override_for_covers(hass, entry, up_covers)
            )
            hass.async_create_task(run_group_light_action(hass, entry, area_id, "up"))
        return moved

    # --- Mindestdauer an der Schwelle ----------------------------------------
    #
    # Ein Helligkeitssensor liefert auch mal Unsinn: eine Wetterstation, die
    # neu startet, meldet kurz 0 lx, ein Funkaussetzer ebenso. Ohne Frist ist
    # diese eine Meldung eine vollstaendige Abendfahrt – bjoergs Haus fuhr um
    # 15:12 bei 21 000 lx komplett zu. Die Frist fragt, ob die Schwelle
    # *anhaltend* ueber- bzw. unterschritten ist; der Zeitpunkt der ersten
    # Ueberschreitung liegt je Bereich und Richtung in `cond_since`.
    cond_since: dict[str, float] = data.setdefault("_b_cond_since", {})
    # Letzter Messwert je Sensor: der Minutentakt braucht ihn, weil ein Sensor,
    # der in der Daemmerung minutenlang denselben Wert meldet, kein Event
    # ausloest – und genau dann laeuft die Frist ab.
    last_lux: dict[str, float] = data.setdefault("_b_last_lux", {})

    def _hold_seconds(area: dict) -> float:
        try:
            minutes = float(area.get(CONF_AREA_LUX_HOLD, DEFAULT_AREA_LUX_HOLD) or 0)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(minutes, MAX_AREA_LUX_HOLD)) * 60.0

    def _held(area: dict, area_id: str, direction: str, met: bool) -> bool:
        """True once `met` has stayed true for the area's hold time.

        A gap resets the clock: the next reading past the threshold starts a
        fresh wait. That is the point – one reading is not a trend.
        """
        key = f"{direction}_{area_id}"
        if not met:
            cond_since.pop(key, None)
            return False
        hold = _hold_seconds(area)
        if hold <= 0:
            return True
        first = cond_since.setdefault(key, time_mod.monotonic())
        waited = time_mod.monotonic() - first
        if waited < hold:
            _LOGGER.info(
                "[brightness] area=%s: %s threshold met – holding for another "
                "%.0f s (of %.0f s) before driving",
                area_id, direction, hold - waited, hold,
            )
            return False
        return True

    def _evaluate_area(area: dict, area_id: str, lux: float, now: datetime) -> None:
        today = now.date()
        sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
        try:
            down_threshold = int(
                area.get(CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD, DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD)
            )
        except (TypeError, ValueError):
            down_threshold = DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD
        try:
            up_threshold = int(
                area.get(CONF_AREA_BRIGHTNESS_UP_THRESHOLD, DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD)
            )
        except (TypeError, ValueError):
            up_threshold = DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD

        _LOGGER.info(
            "Brightness eval: area=%s sensor=%s lux=%.1f up_thresh=%d down_thresh=%d",
            area_id, sensor_id, lux, up_threshold, down_threshold,
        )

        down_met = _area_window(area, now, "down", hass) and lux <= down_threshold
        if _held(area, area_id, "down", down_met):
            _run_down(area, area_id, "Brightness down")

        is_pending = pending_up.get(area_id) == today
        within_up = _area_window(area, now, "up", hass)

        if within_up and lux <= up_threshold:
            pending_up[area_id] = today
            _LOGGER.info(
                "Brightness: area %s marked pending (lux %.1f <= %d)",
                area_id, lux, up_threshold,
            )
        up_met = (within_up or is_pending) and lux > up_threshold
        if _held(area, area_id, "up", up_met):
            if _run_up(
                area, area_id, "Brightness up",
                within_up_window=within_up or is_pending,
            ) and is_pending:
                pending_up.pop(area_id, None)

    def _process_brightness(entity_id: str, new_state) -> None:
        if new_state is None:
            return
        state_str = getattr(new_state, "state", None)
        if state_str in (None, "unknown", "unavailable"):
            return
        try:
            lux = float(state_str)
        except (TypeError, ValueError):
            return

        last_lux[entity_id] = lux
        now = datetime.now()

        for area in brightness_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            if not is_auto_enabled(hass, entry, area):
                continue

            sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
            if entity_id != sensor_id:
                continue
            _evaluate_area(area, area_id, lux, now)

    @callback
    def _on_brightness_change(event) -> None:
        new_state = event.data.get("new_state")
        entity_id = event.data.get("entity_id", "")
        _process_brightness(entity_id, new_state)

    def _hold_tick(now_local: datetime) -> None:
        """Re-ask the last reading for areas with a hold time.

        Only those: without a hold the state event already did everything
        there was to do, and re-running it every minute would change when a
        drive happens (a window opening at 16:00 would drive on an hour-old
        reading) – behaviour nobody asked for on a default installation.
        """
        for area in brightness_areas:
            if _hold_seconds(area) <= 0:
                continue
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id or not is_auto_enabled(hass, entry, area):
                continue
            sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
            lux = last_lux.get(sensor_id)
            if lux is None:
                state = hass.states.get(sensor_id)
                try:
                    lux = float(getattr(state, "state", None))
                except (TypeError, ValueError):
                    continue
                last_lux[sensor_id] = lux
            _evaluate_area(area, area_id, lux, now_local.replace(tzinfo=None))

    tracked_sensors: set[str] = set()
    for area in brightness_areas:
        sensor_id = str(area.get(CONF_AREA_BRIGHTNESS_SENSOR) or "").strip()
        if not sensor_id or sensor_id in tracked_sensors:
            continue
        tracked_sensors.add(sensor_id)
        unsub = async_track_state_change_event(hass, sensor_id, _on_brightness_change)
        if unsub:
            data["_brightness_unsubs"].append(unsub)
        _LOGGER.info("Brightness listener registered: %s (area=%s)", sensor_id, area.get(CONF_AREA_ID))

    # --- Uhrzeit-Notnagel, unabhaengig vom Lux-Wert -------------------------
    #
    # Der Helligkeitsmodus haengt sonst allein am State-Change des Sensors.
    # Eine Uhrzeit braucht den Minutentakt: meldet der Sensor in der Daemmerung
    # minutenlang denselben Wert, feuert kein Event – und genau dann soll die
    # Frist greifen.
    fired_latest: dict[str, Any] = data.setdefault("_b_latest_fired", {})

    setup_now = dt_util.as_local(dt_util.now())
    for area in brightness_areas:
        area_id = str(area.get(CONF_AREA_ID) or "").strip()
        if not area_id:
            continue
        for direction in ("up", "down"):
            deadline = _latest_deadline(hass, area, setup_now, direction)
            # Wie im Scheduler: eine Frist, die heute schon vorbei ist, gilt
            # nach einem Neustart als erledigt. Sonst faehrt ein Reload um
            # 23 Uhr die Rollladen hoch, weil "spaetestens 09:00" laengst
            # ueberschritten ist.
            if deadline is not None and setup_now.time() >= deadline:
                fired_latest[f"{direction}_{area_id}"] = setup_now.date()

    @callback
    def _minute_tick(now: datetime) -> None:
        now_local = dt_util.as_local(now)
        _hold_tick(now_local)
        _latest_tick(now_local)

    def _latest_tick(now_local: datetime) -> None:
        today = now_local.date()
        t = now_local.time()
        for area in brightness_areas:
            area_id = str(area.get(CONF_AREA_ID) or "").strip()
            if not area_id:
                continue
            for direction in ("up", "down"):
                deadline = _latest_deadline(hass, area, now_local, direction)
                if deadline is None or t < deadline:
                    continue
                key = f"{direction}_{area_id}"
                if fired_latest.get(key) == today:
                    continue
                # Der Merker wird auch gesetzt, wenn nichts zu fahren war:
                # die Frist ist damit fuer heute abgehandelt. Sonst liefe sie
                # jede Minute bis Mitternacht erneut auf – und faehrt einen
                # Rollladen wieder hoch, den der Lux-Wert eben geschlossen hat.
                fired_latest[key] = today
                if not is_auto_enabled(hass, entry, area):
                    continue
                _LOGGER.info(
                    "[brightness-latest] area=%s: %s um %s erreicht – fahre ohne Lux-Wert",
                    area_id, direction, deadline.strftime("%H:%M"),
                )
                if direction == "up":
                    # Die Vormerkung ist mit der Frist erledigt, egal ob
                    # gefahren wurde – sonst faehrt der Lux-Wert am Abend
                    # ausserhalb des Zeitfensters noch einmal hoch.
                    pending_up.pop(area_id, None)
                    _run_up(area, area_id, "Brightness latest up", within_up_window=True)
                else:
                    _run_down(area, area_id, "Brightness latest down")

    if any(
        _latest_deadline(hass, area, setup_now, direction) is not None
        for area in brightness_areas
        for direction in ("up", "down")
    ) or any(_hold_seconds(area) > 0 for area in brightness_areas):
        register_minute_callback(data, "brightness", _minute_tick)
    else:
        register_minute_callback(data, "brightness", None)
