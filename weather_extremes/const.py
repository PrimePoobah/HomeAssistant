"""Constants for the Weather Extremes integration."""
from typing import Final

DOMAIN: Final = "weather_extremes"
DATA_FILENAME: Final = "weather_extremes_data.json"

# Configuration constants
CONF_AVERAGING_WINDOW: Final = "averaging_window"
CONF_PERSISTENCE: Final = "persistence"
CONF_DECIMAL_PLACES: Final = "decimal_places"

# Default values
DEFAULT_AVERAGING_WINDOW: Final = 5
DEFAULT_DECIMAL_PLACES: Final = 1
DEFAULT_PERSISTENCE: Final = True

# Time periods
PERIODS: Final = ["day", "week", "month", "year", "all_time"]
AVERAGING_PERIODS: Final = ["current", "day", "week", "month", "year"]

# Version
VERSION = "1.0.0"
REQUIRED_FILES = [
    "const.py",
    "manifest.json",
    "sensor.py",
    "services.yaml",
    "__init__.py",
]