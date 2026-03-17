"""Constants for Shutter Pilot integration."""

DOMAIN = "shutter_pilot"

# Config entry keys
CONF_SHUTTERS = "shutters"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

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
DEFAULT_AREA_DRIVE_DELAY = DEFAULT_AREA_DRIVE_DELAY  # backwards-compatible alias

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

# Drive after close: wenn Zeit zum Schließen, Fenster aber offen -> merken, bei Fenster zu fahren
CONF_DRIVE_AFTER_CLOSE = "drive_after_close"

# Per-area schedule: time mode
CONF_AREA_TIME_UP = "time_up"  # HH:MM
CONF_AREA_TIME_DOWN = "time_down"  # HH:MM

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

# Per-area sun protection (elevation)
CONF_AREA_SUN_PROTECT_ENABLED = "sun_protect_enabled"
CONF_AREA_ELEVATION_THRESHOLD = "elevation_threshold"
DEFAULT_AREA_ELEVATION_THRESHOLD = 4.0

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
DEFAULT_AREA_W_UP_FROM = "05:00"
DEFAULT_AREA_W_UP_TO = "09:00"
DEFAULT_AREA_W_DOWN_FROM = "16:00"
DEFAULT_AREA_W_DOWN_TO = "23:59"
DEFAULT_AREA_WE_UP_FROM = "07:00"
DEFAULT_AREA_WE_UP_TO = "10:00"
DEFAULT_AREA_WE_DOWN_FROM = "16:00"
DEFAULT_AREA_WE_DOWN_TO = "23:59"
