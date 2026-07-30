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
CONF_WINDOW_ENTITY_ID = "window_entity_id"
CONF_WINDOW_OPEN_STATE = "window_open_state"
CONF_WINDOW_TILTED_STATE = "window_tilted_state"
CONF_POSITION_WHEN_WINDOW_OPEN = "position_when_window_open"
CONF_POSITION_WHEN_WINDOW_TILTED = "position_when_window_tilted"
CONF_LOCK_PROTECTION = "lock_protection"
CONF_MIN_POSITION_WHEN_OPEN = "min_position_when_open"
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

# Per-area sun protection (elevation range: active when min <= elev <= max)
CONF_AREA_SUN_PROTECT_ENABLED = "sun_protect_enabled"
CONF_AREA_ELEVATION_THRESHOLD = "elevation_threshold"  # legacy → maps to elevation_max
CONF_AREA_ELEVATION_MIN = "elevation_min"
CONF_AREA_ELEVATION_MAX = "elevation_max"
DEFAULT_AREA_ELEVATION_THRESHOLD = 4.0
DEFAULT_AREA_ELEVATION_MIN = 0.0
DEFAULT_AREA_ELEVATION_MAX = 15.0

# Per-area sun protection: compass direction of the windows (azimuth, degrees).
# 0 = North, 90 = East, 180 = South, 270 = West.
# Full circle (0–360) means "any direction" and keeps legacy behaviour.
CONF_AREA_AZIMUTH_ENABLED = "azimuth_enabled"
CONF_AREA_AZIMUTH_MIN = "azimuth_min"
CONF_AREA_AZIMUTH_MAX = "azimuth_max"
DEFAULT_AREA_AZIMUTH_MIN = 90.0
DEFAULT_AREA_AZIMUTH_MAX = 270.0

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
