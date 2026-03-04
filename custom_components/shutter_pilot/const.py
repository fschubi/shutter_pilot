"""Constants for Shutter Pilot integration."""

DOMAIN = "shutter_pilot"

# Config entry keys
CONF_SHUTTERS = "shutters"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

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
CONF_TRIGGER_MODE = "trigger_mode"
CONF_GROUP_UP = "group_up"
CONF_GROUP_DOWN = "group_down"
CONF_POSITION_OPEN = "position_open"
CONF_POSITION_CLOSED = "position_closed"
CONF_POSITION_SUN_PROTECT = "position_sun_protect"
CONF_BRIGHTNESS_TRIGGER = "brightness_trigger"

# Trigger modes
TRIGGER_MODE_OFF = "off"
TRIGGER_MODE_ONLY_UP = "only_up"
TRIGGER_MODE_ONLY_DOWN = "only_down"
TRIGGER_MODE_UP_DOWN = "up_down"

# Groups
GROUP_LIVING = "living"
GROUP_SLEEP = "sleep"
GROUP_CHILDREN = "children"
GROUP_ALL = "all"

GROUPS = [GROUP_LIVING, GROUP_SLEEP, GROUP_CHILDREN, GROUP_ALL]

# Brightness trigger modes
BRIGHTNESS_OFF = "off"
BRIGHTNESS_UP = "up"
BRIGHTNESS_DOWN = "down"
BRIGHTNESS_BOTH = "both"

# Brightness config (global)
CONF_BRIGHTNESS_ENTITY_ID = "brightness_entity_id"
CONF_BRIGHTNESS_DOWN_THRESHOLD = "brightness_down_threshold"
CONF_BRIGHTNESS_UP_THRESHOLD = "brightness_up_threshold"
CONF_BRIGHTNESS_DOWN_TIME = "brightness_down_time"
CONF_BRIGHTNESS_UP_TIME = "brightness_up_time"
CONF_BRIGHTNESS_IGNORE_TIME = "brightness_ignore_time"

# Time config (per group) - Living, Sleep, Children each get full schedule
# type_up / type_down: "fixed" | "sunrise" | "sunset"
TIME_TYPE_FIXED = "fixed"
TIME_TYPE_SUNRISE = "sunrise"
TIME_TYPE_SUNSET = "sunset"

# Legacy/fallback keys (used if per-group not set)
CONF_W_SHUTTER_UP_MIN = "w_shutter_up_min"
CONF_W_SHUTTER_UP_MAX = "w_shutter_up_max"
CONF_W_SHUTTER_DOWN = "w_shutter_down"
CONF_WE_SHUTTER_UP_MIN = "we_shutter_up_min"
CONF_WE_SHUTTER_UP_MAX = "we_shutter_up_max"
CONF_WE_SHUTTER_DOWN = "we_shutter_down"

# Sunrise/Sunset offset (minutes: negative = before, positive = after)
CONF_SUNRISE_OFFSET = "sunrise_offset"
CONF_SUNSET_OFFSET = "sunset_offset"
DEFAULT_SUNRISE_OFFSET = 0
DEFAULT_SUNSET_OFFSET = 0

# Living
CONF_LIVING_TYPE_UP = "living_type_up"
CONF_LIVING_TYPE_DOWN = "living_type_down"
CONF_LIVING_W_UP_MIN = "living_w_up_min"
CONF_LIVING_W_UP_MAX = "living_w_up_max"
CONF_LIVING_W_DOWN = "living_w_down"
CONF_LIVING_WE_UP_MIN = "living_we_up_min"
CONF_LIVING_WE_UP_MAX = "living_we_up_max"
CONF_LIVING_WE_DOWN = "living_we_down"
CONF_LIVING_SUNRISE_OFFSET = "living_sunrise_offset"
CONF_LIVING_SUNSET_OFFSET = "living_sunset_offset"

# Sleep
CONF_SLEEP_TYPE_UP = "sleep_type_up"
CONF_SLEEP_TYPE_DOWN = "sleep_type_down"
CONF_SLEEP_SUNRISE_OFFSET = "sleep_sunrise_offset"
CONF_SLEEP_SUNSET_OFFSET = "sleep_sunset_offset"
CONF_SLEEP_W_UP_MIN = "sleep_w_up_min"
CONF_SLEEP_W_UP_MAX = "sleep_w_up_max"
CONF_SLEEP_W_DOWN = "sleep_w_down"
CONF_SLEEP_WE_UP_MIN = "sleep_we_up_min"
CONF_SLEEP_WE_UP_MAX = "sleep_we_up_max"
CONF_SLEEP_WE_DOWN = "sleep_we_down"

# Children
CONF_CHILDREN_TYPE_UP = "children_type_up"
CONF_CHILDREN_TYPE_DOWN = "children_type_down"
CONF_CHILDREN_SUNRISE_OFFSET = "children_sunrise_offset"
CONF_CHILDREN_SUNSET_OFFSET = "children_sunset_offset"
CONF_CHILDREN_W_UP_MIN = "children_w_up_min"
CONF_CHILDREN_W_UP_MAX = "children_w_up_max"
CONF_CHILDREN_W_DOWN = "children_w_down"
CONF_CHILDREN_WE_UP_MIN = "children_we_up_min"
CONF_CHILDREN_WE_UP_MAX = "children_we_up_max"
CONF_CHILDREN_WE_DOWN = "children_we_down"

# Auto mode triggers (optional input_boolean entities)
CONF_AUTO_LIVING = "auto_living"
CONF_AUTO_SLEEP = "auto_sleep"
CONF_AUTO_CHILDREN = "auto_children"

# Drive after close: wenn Zeit zum Schließen, Fenster aber offen -> merken, bei Fenster zu fahren
CONF_DRIVE_AFTER_CLOSE = "drive_after_close"

# Elevation / sun protection
CONF_ELEVATION_THRESHOLD = "elevation_threshold"
CONF_USE_ELEVATION = "use_elevation"

# Timing
CONF_DRIVE_DELAY = "drive_delay"
DEFAULT_DRIVE_DELAY = 10  # seconds between shutters

# Defaults
DEFAULT_POSITION_OPEN = 100
DEFAULT_POSITION_CLOSED = 0
DEFAULT_POSITION_SUN_PROTECT = 50
DEFAULT_POSITION_WHEN_WINDOW_OPEN = 100
DEFAULT_POSITION_WHEN_WINDOW_TILTED = 50
DEFAULT_WINDOW_OPEN_STATE = "on"
DEFAULT_WINDOW_TILTED_STATE = "none"  # "none" = no tilted state, use open only
DEFAULT_MIN_POSITION_WHEN_OPEN = 20
DEFAULT_BRIGHTNESS_DOWN_THRESHOLD = 400
DEFAULT_BRIGHTNESS_UP_THRESHOLD = 500
DEFAULT_BRIGHTNESS_DOWN_TIME = "16:00"
DEFAULT_BRIGHTNESS_UP_TIME = "05:00"
DEFAULT_ELEVATION_THRESHOLD = 4
