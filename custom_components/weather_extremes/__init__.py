"""
The Weather Extremes integration.
For more details about this integration, please refer to the documentation at
https://github.com/custom-components/weather-extremes
"""

import logging
import voluptuous as vol
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "weather_extremes"
PLATFORMS = [Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                # Add any domain-wide configuration options here if needed
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Weather Extremes component."""
    if DOMAIN in config:
        hass.data[DOMAIN] = {}
        _LOGGER.info("Weather Extremes integration initialized")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Weather Extremes from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store the entry data
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Reload entry when configuration is updated
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload sensors
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove config entry from domain data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        # Add migration code here if needed in the future
        
        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: Any
) -> bool:
    """Remove a config entry from a device."""
    return True