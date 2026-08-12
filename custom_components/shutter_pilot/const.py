"""Constants for Shutter Pilot integration."""

DOMAIN = "shutter_pilot"

# Bus events
EVENT_COVER_MOVED = "shutter_pilot_cover_moved"

# Config entry keys
CONF_SHUTTERS = "shutters"

# Areas (dynamic groups)
CONF_AREAS = "areas"
CONF_AREA_ID = "id"
CONF_AREA_NAME = "name"
CONF_AREA_MODE = "mode"  # "time" | "brightness" | "sun"

AREA_MODE_TIME = "time"
AREA_MODE_BRIGHTNESS = "brightness"
AREA_MODE_SUN = "sun"
AREA_MODES = [AREA_MODE_TIME, AREA_MODE_BRIGHTNESS, AREA_MODE_SUN]

# Per-area common settings
CONF_AREA_DRIVE_DELAY = "drive_delay"  # seconds between shutters in this area
DEFAULT_AREA_DRIVE_DELAY = 10

# Per-area automation enable (optional switch entity id created by integration)
CONF_AREA_AUTO_ENTITY_ID = "auto_entity_id"

# Shutter config keys
CONF_COVER_ENTITY_ID = "cover_entity_id"
CONF_NAME = "name"
# Per-shutter automation enable. Third level below the master switch and the
# per-area switch: a defective shutter stays put while the rest of its area
# keeps running, and its configuration survives. A missing value means "on" –
# otherwise every existing installation would stand still after an update.
# Manual actions (services, dashboard buttons) are not affected.
CONF_SHUTTER_AUTOMATION_ENABLED = "automation_enabled"
CONF_SHUTTER_AUTO_ENTITY_ID = "shutter_auto_entity_id"
CONF_WINDOW_ENTITY_ID = "window_entity_id"
CONF_WINDOW_OPEN_STATE = "window_open_state"
CONF_WINDOW_TILTED_STATE = "window_tilted_state"
# Optional second contact that only reports the tilted state. Some window
# sensors expose "open" and "tilted" as two separate entities instead of one
# entity with three states.
CONF_WINDOW_TILTED_ENTITY_ID = "window_tilted_entity_id"
CONF_WINDOW_TILTED_ENTITY_STATE = "window_tilted_entity_state"
DEFAULT_WINDOW_TILTED_ENTITY_STATE = "on"
CONF_POSITION_WHEN_WINDOW_OPEN = "position_when_window_open"
CONF_POSITION_WHEN_WINDOW_TILTED = "position_when_window_tilted"
# One-way radio covers (Somfy RTS and relatives) never report a position.
# In blind mode Shutter Pilot reasons with the position it last sent instead,
# so window triggers and ventilation work there too – they would otherwise
# bail out the moment they cannot read the cover.
CONF_BLIND_DRIVE = "blind_drive"

CONF_LOCK_PROTECTION = "lock_protection"
CONF_MIN_POSITION_WHEN_OPEN = "min_position_when_open"
# Turning the handle from "tilted" to "open" drags the contact through
# "closed" for a moment. Without a wait the shutter drives back right away and
# never reaches the open position. Seconds, 0 disables the wait.
CONF_WINDOW_CLOSE_DEBOUNCE = "window_close_debounce"
DEFAULT_WINDOW_CLOSE_DEBOUNCE = 5
MAX_WINDOW_CLOSE_DEBOUNCE = 30
CONF_AREA_UP_ID = "area_up_id"
CONF_AREA_DOWN_ID = "area_down_id"
CONF_POSITION_OPEN = "position_open"
CONF_POSITION_CLOSED = "position_closed"
CONF_POSITION_SUN_PROTECT = "position_sun_protect"

# Slat/tilt angles per shutter (venetian blinds). Disabled unless tilt_enabled.
CONF_TILT_ENABLED = "tilt_enabled"
CONF_TILT_OPEN = "tilt_open"
CONF_TILT_CLOSED = "tilt_closed"
CONF_TILT_SUN_PROTECT = "tilt_sun_protect"
DEFAULT_TILT_OPEN = 100
DEFAULT_TILT_CLOSED = 0
DEFAULT_TILT_SUN_PROTECT = 30

# Roles used to resolve position/tilt for a shutter
ROLE_OPEN = "open"
ROLE_CLOSED = "closed"
ROLE_SUN_PROTECT = "sun_protect"
# Ventilation reuses the position configured for a tilted window, so it needs
# no extra config key – it just makes that position reachable on purpose.
ROLE_VENTILATION = "ventilation"
# Partial close, used when the area's close condition is met.
ROLE_CLOSED_ALT = "closed_alt"
# Partial close against frost. Wins over closed_alt: protection beats comfort.
ROLE_CLOSED_FROST = "closed_frost"

# Drive after close: wenn Zeit zum Schließen, Fenster aber offen -> merken, bei Fenster zu fahren
CONF_DRIVE_AFTER_CLOSE = "drive_after_close"

# Per-area schedule: time mode (weekday = default, weekend = optional override)
CONF_AREA_TIME_UP = "time_up"  # HH:MM weekday
CONF_AREA_TIME_DOWN = "time_down"  # HH:MM weekday
CONF_AREA_TIME_WE_UP = "time_we_up"  # HH:MM weekend (falls back to time_up)
CONF_AREA_TIME_WE_DOWN = "time_we_down"  # HH:MM weekend (falls back to time_down)

# Per-area schedule: sun mode
CONF_AREA_SUNRISE_OFFSET = "sunrise_offset"  # minutes
CONF_AREA_SUNSET_OFFSET = "sunset_offset"  # minutes
DEFAULT_AREA_SUNRISE_OFFSET = 0
DEFAULT_AREA_SUNSET_OFFSET = 0

# Per-area brightness mode config
CONF_AREA_BRIGHTNESS_SENSOR = "brightness_sensor"
CONF_AREA_BRIGHTNESS_DOWN_THRESHOLD = "lux_down"
CONF_AREA_BRIGHTNESS_UP_THRESHOLD = "lux_up"

# Brightness allowed time windows (week + weekend, each with from/to)
CONF_AREA_W_UP_FROM = "w_up_from"
CONF_AREA_W_UP_TO = "w_up_to"
CONF_AREA_W_DOWN_FROM = "w_down_from"
CONF_AREA_W_DOWN_TO = "w_down_to"
CONF_AREA_WE_UP_FROM = "we_up_from"
CONF_AREA_WE_UP_TO = "we_up_to"
CONF_AREA_WE_DOWN_FROM = "we_down_from"
CONF_AREA_WE_DOWN_TO = "we_down_to"

# Extra sun-relative bounds on top of the clock windows above. A thunderstorm
# in the afternoon drives the lux below the threshold, and without this the
# shutters closed in broad daylight. "No earlier than sunset minus 60 minutes"
# is what the clock windows cannot express, because sunset moves all year.
# Offsets are in minutes; None/empty means the bound does not apply.
CONF_AREA_B_DOWN_AFTER_SUNSET = "b_down_after_sunset"
CONF_AREA_B_UP_BEFORE_SUNRISE = "b_up_before_sunrise"

# Deadlines that drive *without* the lux value. In the dark half of the year
# the up threshold may never be reached, and the clock windows only ever
# permit a drive – they never trigger one. Off by default: switched on
# unasked, a deadline would move shutters in installations that are happy.
# The weekend value falls back to the weekday value when left empty.
CONF_AREA_B_LATEST_UP_ENABLED = "b_latest_up_enabled"
CONF_AREA_B_LATEST_UP = "b_latest_up"
CONF_AREA_B_WE_LATEST_UP = "b_we_latest_up"
CONF_AREA_B_LATEST_DOWN_ENABLED = "b_latest_down_enabled"
CONF_AREA_B_LATEST_DOWN = "b_latest_down"
CONF_AREA_B_WE_LATEST_DOWN = "b_we_latest_down"

# Per-area sun protection (elevation range: active when min <= elev <= max)
CONF_AREA_SUN_PROTECT_ENABLED = "sun_protect_enabled"
CONF_AREA_ELEVATION_THRESHOLD = "elevation_threshold"  # legacy → maps to elevation_max
CONF_AREA_ELEVATION_MIN = "elevation_min"
CONF_AREA_ELEVATION_MAX = "elevation_max"
# Whether the sun's height is consulted at all. Off means a brightness sensor
# alone decides – the setup people with a lux meter per window actually want.
# Default on, so nothing changes for anyone who already has a range set.
CONF_AREA_ELEVATION_ENABLED = "elevation_enabled"
DEFAULT_AREA_ELEVATION_ENABLED = True
DEFAULT_AREA_ELEVATION_THRESHOLD = 4.0
DEFAULT_AREA_ELEVATION_MIN = 0.0
# 15° was a poor starting point: in summer the midday sun stands at 60°, so a
# freshly created area with shading switched on never shaded during the day.
# Only new areas are affected – the fallback for stored configs stays put.
DEFAULT_AREA_ELEVATION_MAX = 90.0

# Purely for the dashboard: a room temperature to show on the area card.
# Never read by any automation – it decides nothing.
CONF_AREA_TEMP_SENSOR = "temp_sensor"

# Per-area sun protection: compass direction of the windows (azimuth, degrees).
# 0 = North, 90 = East, 180 = South, 270 = West.
# Full circle (0–360) means "any direction" and keeps legacy behaviour.
CONF_AREA_AZIMUTH_ENABLED = "azimuth_enabled"
CONF_AREA_AZIMUTH_MIN = "azimuth_min"
CONF_AREA_AZIMUTH_MAX = "azimuth_max"
DEFAULT_AREA_AZIMUTH_MIN = 90.0
DEFAULT_AREA_AZIMUTH_MAX = 270.0

# Up to four extra conditions that must hold before shading kicks in.
# One mechanism covers radiation, brightness and temperature:
#   binary_sensor -> "on" satisfies the condition (hysteresis lives in the
#                    sensor itself, which is how most such helpers work)
#   numeric sensor -> satisfied at value >= on_above, released below off_below
# An unset, unknown or unavailable sensor never blocks shading (fail open).
SUN_CONDITION_SLOTS = ("a", "b", "c", "d")
# Domains whose state is on/off and nothing else, so they answer a condition
# directly instead of being read as a number. Helpers belong here: a house mode
# or a cleaning-service flag is an input_boolean, and without this it fell into
# the numeric branch, failed to parse and was *ignored* – a fail-open that
# looks exactly like a satisfied condition from the outside.
BOOLEAN_CONDITION_DOMAINS = (
    "binary_sensor.",
    "input_boolean.",
    "switch.",
    "schedule.",
)
CONF_SUN_COND_ENTITY = "sun_cond_{slot}_entity"
CONF_SUN_COND_ON_ABOVE = "sun_cond_{slot}_on_above"
CONF_SUN_COND_OFF_BELOW = "sun_cond_{slot}_off_below"
# Allowed states for a text condition, e.g. a weather entity or a scrape
# sensor reporting "sunny" / "bewölkt". Stored as a list of strings.
CONF_SUN_COND_STATES = "sun_cond_{slot}_states"
# Flips the numeric comparison: satisfied *below* on_above, released above
# off_below. Frost protection needs "colder than", every other user of this
# mechanism asks "warmer / brighter than". Kept out of sun_condition_keys()
# so the three places that unpack that tuple stay untouched.
CONF_SUN_COND_INVERT = "sun_cond_{slot}_invert"

# Awning protection reuses the very same slot mechanism, with one deliberate
# difference in meaning: here a satisfied slot means *danger*, not permission.
# "on" at a rain sensor, "wind above 30" and "colder than -2" all read the
# natural way round that, and the existing hysteresis then does exactly what is
# wanted – retract at on_above, release only below off_below.
AWNING_GUARD_WIND = "wind"
AWNING_GUARD_RAIN = "rain"
AWNING_GUARD_ICE = "ice"
AWNING_GUARD_SLOTS = (AWNING_GUARD_WIND, AWNING_GUARD_RAIN, AWNING_GUARD_ICE)

# Slot used for the alternative closing position. Same evaluation, own name.
CLOSE_CONDITION_SLOT = "close"
# Two slots, like ventilation: "warm today AND somebody at home" needs both.
# The first keeps its old key so existing setups carry over untouched.
CLOSE_CONDITION_SLOTS = (CLOSE_CONDITION_SLOT, "close_b")

# Automatic ventilation: drive to the ventilation position while every
# configured condition holds, and back to where the shutter stood before once
# one drops out. Two slots cover the asked-for case (a switch AND a value).
CONF_AREA_VENT_ENABLED = "vent_enabled"
VENT_CONDITION_SLOTS = ("vent_a", "vent_b")
# Frost protection: do not close all the way, so the slats cannot freeze shut.
FROST_CONDITION_SLOT = "frost"
# Slots that ask "below" rather than "above" unless told otherwise. Frost is
# always about falling temperatures, so users should not have to say so – and
# ice on an awning is the same question asked at the other end of the house.
INVERTED_BY_DEFAULT_SLOTS = (FROST_CONDITION_SLOT, AWNING_GUARD_ICE)

# Standard weather conditions in Home Assistant, offered as checkboxes.
WEATHER_CONDITIONS = (
    "clear-night", "cloudy", "exceptional", "fog", "hail", "lightning",
    "lightning-rainy", "partlycloudy", "pouring", "rainy", "snowy",
    "snowy-rainy", "sunny", "windy", "windy-variant",
)


def sun_condition_keys(slot: str) -> tuple[str, str, str, str]:
    """Return (entity, on_above, off_below, states) option keys for a slot."""
    return (
        CONF_SUN_COND_ENTITY.format(slot=slot),
        CONF_SUN_COND_ON_ABOVE.format(slot=slot),
        CONF_SUN_COND_OFF_BELOW.format(slot=slot),
        CONF_SUN_COND_STATES.format(slot=slot),
    )


def sun_condition_invert_key(slot: str) -> str:
    """Return the "compare downwards" option key for a slot."""
    return CONF_SUN_COND_INVERT.format(slot=slot)


# Earliest and latest clock time for the sun mode. The moment computed from
# sunrise/sunset plus offset is clamped into this window, so "drive by sun
# elevation, but not before 07:30 and not after 09:00" becomes possible.
# Weekend values fall back to the weekday ones, like time_we_up does.
CONF_AREA_SUN_EARLIEST_UP = "sun_earliest_up"
CONF_AREA_SUN_LATEST_UP = "sun_latest_up"
CONF_AREA_SUN_EARLIEST_DOWN = "sun_earliest_down"
CONF_AREA_SUN_LATEST_DOWN = "sun_latest_down"
CONF_AREA_SUN_WE_EARLIEST_UP = "sun_we_earliest_up"
CONF_AREA_SUN_WE_LATEST_UP = "sun_we_latest_up"
CONF_AREA_SUN_WE_EARLIEST_DOWN = "sun_we_earliest_down"
CONF_AREA_SUN_WE_LATEST_DOWN = "sun_we_latest_down"

# Verify that a cover actually reached the requested position. Radio-driven
# shutters lose commands, and without this the integration would keep working
# with a position the cover never reached.
CONF_VERIFY_ENABLED = "verify_enabled"
CONF_VERIFY_AFTER = "verify_after"
CONF_VERIFY_TOLERANCE = "verify_tolerance"
CONF_VERIFY_RETRIES = "verify_retries"
DEFAULT_VERIFY_AFTER = 45
DEFAULT_VERIFY_TOLERANCE = 8
DEFAULT_VERIFY_RETRIES = 1
EVENT_COVER_FAILED = "shutter_pilot_cover_failed"

# Global minimum distance between two drive commands, in seconds. The per-area
# delay cannot cover this: every area drives in its own task, so two areas still
# fire at the same moment – and radio protocols (433 MHz, HmIP) swallow commands
# that collide. 0 disables the throttle and is the previous behaviour.
CONF_MIN_DRIVE_GAP = "min_drive_gap"
DEFAULT_MIN_DRIVE_GAP = 0.0
MAX_MIN_DRIVE_GAP = 10.0

# How long shading is held after it is no longer needed, in minutes. Values and
# hysteresis already stop the shading from chattering on sensor noise, but a
# cloud drifting past ends the condition outright – and the shutters went up
# straight away. 0 keeps the immediate release.
CONF_AREA_SHADE_HOLD = "shade_hold"
DEFAULT_AREA_SHADE_HOLD = 0
MAX_AREA_SHADE_HOLD = 120

# Per-area shading season, as month numbers 1-12. Empty means all year.
# Ranges may wrap across the turn of the year (e.g. 10 -> 3 for winter).
CONF_AREA_SEASON_FROM = "season_from"
CONF_AREA_SEASON_TO = "season_to"

# Clock window in which shading may run at all, "HH:MM". Either bound may be
# left empty. Elevation, azimuth and the conditions all describe *the sun*;
# this one describes the household – "not before nine during the holidays,
# the room has to stay dark". Overridable per shutter, because that request
# is always about one window, not about the whole area.
#
# Deliberately no wrap across midnight, unlike the season and the azimuth: a
# shading window that runs through the night is not a configuration anybody
# means, and reading `from > to` as a wrap is exactly the range-versus-point
# confusion that cost four condition slots their effect in 2.8.0.
CONF_AREA_SHADE_FROM = "shade_from"
CONF_AREA_SHADE_TO = "shade_to"

# Global weather entity used to fetch today's forecast.
CONF_WEATHER_ENTITY = "weather_entity"

# Per-shutter override of the shading geometry, for rooms whose windows face
# different directions. Without the switch the area values apply unchanged.
CONF_SUN_GEOMETRY_OVERRIDE = "sun_geometry_override"

# Alternative closing position per shutter, used when the area's close
# condition is met. Empty means the normal closed position applies.
CONF_POSITION_CLOSED_ALT = "position_closed_alt"

# Closing position per shutter while the area's frost condition holds. Leaving
# a gap keeps the slats from freezing to the sill. Empty means no frost
# protection for this shutter, even when the area's condition is met.
CONF_POSITION_CLOSED_FROST = "position_closed_frost"

# Per-area workday sensor. When set, "on" = weekday schedule, "off" = weekend
# schedule. Replaces the hard-coded Saturday/Sunday check (holidays, shift work).
CONF_AREA_WORKDAY_SENSOR = "workday_sensor"

# Per-area presence simulation: random jitter in minutes applied to scheduled
# up/down times. 0 disables it. The offset is stable for a given day.
CONF_AREA_RANDOM_OFFSET = "random_offset"
DEFAULT_AREA_RANDOM_OFFSET = 0

# Per-area handling of manual positions:
#   never       – a manual position blocks automated opening until the next close
#   daily       – manual position only counts on the day it was set
#   next_action – scheduled actions always win over a manual position
CONF_AREA_MANUAL_OVERRIDE = "manual_override"
OVERRIDE_NEVER = "never"
OVERRIDE_DAILY = "daily"
OVERRIDE_NEXT_ACTION = "next_action"
MANUAL_OVERRIDE_MODES = [OVERRIDE_NEVER, OVERRIDE_DAILY, OVERRIDE_NEXT_ACTION]
DEFAULT_AREA_MANUAL_OVERRIDE = OVERRIDE_NEVER

# Global master switch entity id (stored in entry options after first setup)
CONF_MASTER_ENTITY_ID = "master_entity_id"

# Per-area light action
CONF_AREA_DOWN_LIGHT_ENTITY = "down_light_entity"
CONF_AREA_DOWN_LIGHT_BRIGHTNESS = "down_light_brightness"
DEFAULT_AREA_DOWN_LIGHT_BRIGHTNESS = 40

# ---------------------------------------------------------------------------
#  Awnings
# ---------------------------------------------------------------------------
# An awning is a cover like any other – it just shades by moving *out* instead
# of down. That is why it needs no second drive engine: sun protection drives
# to position_sun_protect and releases to position_open, and which number that
# is comes from the configuration, not from the code. Only two things really
# differ: an awning belongs in no schedule, and it has to come in when it blows.
CONF_DEVICE_KIND = "device_kind"
KIND_SHUTTER = "shutter"
KIND_AWNING = "awning"
# A missing key is a shutter, so no stored configuration needs migrating.
DEFAULT_DEVICE_KIND = KIND_SHUTTER

# Defaults when creating an awning: at rest it is retracted, shading extends it.
# Exactly the other way round from a shutter, which is the whole trick.
DEFAULT_AWNING_POSITION_OPEN = 0
DEFAULT_AWNING_POSITION_SUN_PROTECT = 100
# Awnings that go in and out with every passing cloud are the classic
# complaint, and a fabric drive dislikes it more than a shutter motor does.
DEFAULT_AWNING_SHADE_HOLD = 15

# Keys that mean nothing on an awning. Converting a shutter deletes them
# instead of leaving them behind: stored, visible and ineffective is exactly
# the class of fault _silent_setting_notes() has been reporting since 2.10.2.
AWNING_UNUSED_KEYS = (
    CONF_AREA_UP_ID,
    CONF_POSITION_CLOSED,
    CONF_POSITION_CLOSED_ALT,
    CONF_POSITION_CLOSED_FROST,
    CONF_WINDOW_ENTITY_ID,
    CONF_WINDOW_OPEN_STATE,
    CONF_WINDOW_TILTED_STATE,
    CONF_WINDOW_TILTED_ENTITY_ID,
    CONF_WINDOW_TILTED_ENTITY_STATE,
    CONF_POSITION_WHEN_WINDOW_OPEN,
    CONF_POSITION_WHEN_WINDOW_TILTED,
    CONF_LOCK_PROTECTION,
    CONF_MIN_POSITION_WHEN_OPEN,
    CONF_WINDOW_CLOSE_DEBOUNCE,
    CONF_DRIVE_AFTER_CLOSE,
    CONF_TILT_ENABLED,
    CONF_TILT_OPEN,
    CONF_TILT_CLOSED,
    CONF_TILT_SUN_PROTECT,
)

# How long after the last exceedance the awning stays in, in minutes. Value
# hysteresis alone is not enough for wind: a gust is over in twenty seconds and
# the awning still must not go straight back out.
CONF_AWNING_GUARD_LOCKOUT = "guard_{slot}_lockout"
DEFAULT_AWNING_LOCKOUT = {
    AWNING_GUARD_WIND: 20,
    AWNING_GUARD_RAIN: 30,
    # Frost does not gust. The hysteresis on the temperature is the whole story.
    AWNING_GUARD_ICE: 0,
}
MAX_AWNING_LOCKOUT = 120

# How long an unreadable guard sensor is tolerated before the awning is pulled
# in, in minutes. Extending is barred from the first second either way – the
# grace only covers the far more drastic forced retraction, so that a sensor
# blinking out for a moment during a restart does not yank every awning in.
CONF_AWNING_SENSOR_GRACE = "awning_sensor_grace"
DEFAULT_AWNING_SENSOR_GRACE = 10
MAX_AWNING_SENSOR_GRACE = 120

# Why an awning is currently barred from extending.
GUARD_REASON_UNAVAILABLE = "sensor_unavailable"

# Extending further as the sun sinks: at a high sun a short projection shades
# the same area that needs the full one later on. Two anchor points with a
# straight line between them, because that is a rule one can explain in a form
# without asking for the mounting height.
CONF_AWNING_TRACK_ENABLED = "awning_track_enabled"
CONF_AWNING_TRACK_HIGH_ELEV = "awning_track_high_elev"
CONF_AWNING_TRACK_HIGH_POS = "awning_track_high_pos"
CONF_AWNING_TRACK_LOW_ELEV = "awning_track_low_elev"
CONF_AWNING_TRACK_LOW_POS = "awning_track_low_pos"
# Minimum change before the awning is moved again. Without it the motor runs a
# few percent every single minute, which is the surest way to wear out a drive
# and to make the owner switch the whole thing off.
CONF_AWNING_TRACK_STEP = "awning_track_step"
DEFAULT_AWNING_TRACK_HIGH_ELEV = 60.0
DEFAULT_AWNING_TRACK_HIGH_POS = 60
DEFAULT_AWNING_TRACK_LOW_ELEV = 20.0
DEFAULT_AWNING_TRACK_LOW_POS = 100
DEFAULT_AWNING_TRACK_STEP = 10

EVENT_AWNING_RETRACTED = "shutter_pilot_awning_retracted"


def awning_lockout_key(slot: str) -> str:
    """Return the lockout option key for a guard slot."""
    return CONF_AWNING_GUARD_LOCKOUT.format(slot=slot)


# Defaults
DEFAULT_POSITION_OPEN = 100
DEFAULT_POSITION_CLOSED = 0
DEFAULT_POSITION_SUN_PROTECT = 50
DEFAULT_POSITION_WHEN_WINDOW_OPEN = 100
DEFAULT_POSITION_WHEN_WINDOW_TILTED = 50
DEFAULT_WINDOW_OPEN_STATE = "on"
DEFAULT_WINDOW_TILTED_STATE = "none"  # "none" = no tilted state, use open only
DEFAULT_MIN_POSITION_WHEN_OPEN = 20
DEFAULT_AREA_BRIGHTNESS_DOWN_THRESHOLD = 400
DEFAULT_AREA_BRIGHTNESS_UP_THRESHOLD = 500
DEFAULT_AREA_TIME_UP = "07:00"
DEFAULT_AREA_TIME_DOWN = "19:00"
DEFAULT_AREA_TIME_WE_UP = "08:00"
DEFAULT_AREA_TIME_WE_DOWN = "20:00"
DEFAULT_AREA_W_UP_FROM = "05:00"
DEFAULT_AREA_W_UP_TO = "09:00"
DEFAULT_AREA_W_DOWN_FROM = "16:00"
DEFAULT_AREA_W_DOWN_TO = "23:59"
DEFAULT_AREA_WE_UP_FROM = "07:00"
DEFAULT_AREA_WE_UP_TO = "10:00"
DEFAULT_AREA_WE_DOWN_FROM = "16:00"
DEFAULT_AREA_WE_DOWN_TO = "23:59"
DEFAULT_AREA_B_LATEST_UP = "09:00"
DEFAULT_AREA_B_LATEST_DOWN = "18:00"
