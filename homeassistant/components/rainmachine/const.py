"""Define constants for the SimpliSafe component."""
import logging

LOGGER = logging.getLogger(__package__)

DOMAIN = "rainmachine"

CONF_DURATION = "duration"
CONF_DEFAULT_ZONE_RUN_TIME = "zone_run_time"
CONF_USE_APP_RUN_TIMES = "use_app_run_times"

DATA_API_VERSIONS = "api.versions"
DATA_MACHINE_FIRMWARE_UPDATE_STATUS = "machine.firmware_update_status"
DATA_PROGRAMS = "programs"
DATA_PROVISION_SETTINGS = "provision.settings"
DATA_RESTRICTIONS_CURRENT = "restrictions.current"
DATA_RESTRICTIONS_UNIVERSAL = "restrictions.universal"
DATA_ZONES = "zones"

DEFAULT_PORT = 8080
DEFAULT_ZONE_RUN = 60 * 10

ICON_WATER_PUMP = "mdi:water-pump"
ICON_PIPE_LEAK = "mdi:pipe-leak"
ICON_CANCEL = "mdi:cancel"
