"""
Weather Extremes Tracker for Home Assistant
Track high and low values for temperature and other weather metrics
across different time periods with data persistence and averaging.

Copyright (C) 2024 Weather Extremes Tracker Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import voluptuous as vol
from datetime import datetime, timedelta
import json
import os
import statistics
from typing import Dict, List, Optional, Union
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change, async_track_time_change
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME,
    CONF_SENSORS,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "weather_extremes"
DATA_FILENAME = "weather_extremes_data.json"

# Configuration constants
CONF_AVERAGING_WINDOW = "averaging_window"
CONF_PERSISTENCE = "persistence"
CONF_DECIMAL_PLACES = "decimal_places"

# Configuration schema
SENSOR_SCHEMA = vol.Schema({
    vol.Required('entity_id'): cv.entity_id,
    vol.Required('name'): cv.string,
    vol.Optional('unit_of_measurement'): cv.string,
    vol.Optional(CONF_AVERAGING_WINDOW): vol.All(
        cv.positive_int,
        vol.Range(min=1, max=60)
    ),
    vol.Optional(CONF_DECIMAL_PLACES, default=1): vol.All(
        cv.positive_int,
        vol.Range(min=0, max=3)
    ),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SENSORS): vol.Schema([SENSOR_SCHEMA]),
    vol.Optional(CONF_PERSISTENCE, default=True): cv.boolean,
})

class WeatherExtremesTracker:
    """Enhanced class to track weather extremes for sensors."""
    
    def __init__(self, hass: HomeAssistant, config):
        """Initialize the tracker."""
        self.hass = hass
        self.config = config
        self.sensors = {}
        self.extremes = {}
        self.averages = {}
        self.data_points = {}
        self.persistence = config.get(CONF_PERSISTENCE, True)
        self.config_path = hass.config.path(DATA_FILENAME)
        
        # Load persistent data if enabled
        if self.persistence:
            self._load_persistent_data()
        
        # Set up tracking for each configured sensor
        for sensor_config in config[CONF_SENSORS]:
            sensor_id = sensor_config['entity_id']
            self.sensors[sensor_id] = {
                'name': sensor_config['name'],
                'unit': sensor_config.get('unit_of_measurement', ''),
                'averaging_window': sensor_config.get(CONF_AVERAGING_WINDOW, 5),
                'decimal_places': sensor_config.get(CONF_DECIMAL_PLACES, 1)
            }
            
            if sensor_id not in self.extremes:
                self.extremes[sensor_id] = self._initialize_extremes()
            
            self.data_points[sensor_id] = []
            self.averages[sensor_id] = {
                'current': None,
                'day': None,
                'week': None,
                'month': None,
                'year': None
            }
            
            # Set up state change listener
            async_track_state_change(
                hass,
                sensor_id,
                self._handle_state_change
            )
        
        # Set up periodic tasks
        async_track_time_change(
            hass,
            self._handle_midnight,
            hour=0,
            minute=0,
            second=0
        )
        
        # Set up periodic data saving
        if self.persistence:
            async_track_time_change(
                hass,
                self._save_persistent_data,
                minute=0,
                second=0
            )
    
    def _initialize_extremes(self):
        """Initialize extremes structure for a sensor."""
        return {
            'day': {
                'high': {'value': None, 'timestamp': None},
                'low': {'value': None, 'timestamp': None},
                'last_reset': None
            },
            'week': {
                'high': {'value': None, 'timestamp': None},
                'low': {'value': None, 'timestamp': None},
                'last_reset': None
            },
            'month': {
                'high': {'value': None, 'timestamp': None},
                'low': {'value': None, 'timestamp': None},
                'last_reset': None
            },
            'year': {
                'high': {'value': None, 'timestamp': None},
                'low': {'value': None, 'timestamp': None},
                'last_reset': None
            },
            'all_time': {
                'high': {'value': None, 'timestamp': None},
                'low': {'value': None, 'timestamp': None}
            }
        }
    
    def _load_persistent_data(self):
        """Load persistent data from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    data = json.load(file)
                    self.extremes = data.get('extremes', {})
                    
                    # Convert timestamp strings back to datetime objects
                    for sensor_id in self.extremes:
                        for period in self.extremes[sensor_id]:
                            for extreme_type in ['high', 'low']:
                                if self.extremes[sensor_id][period][extreme_type]['timestamp']:
                                    self.extremes[sensor_id][period][extreme_type]['timestamp'] = \
                                        datetime.fromisoformat(
                                            self.extremes[sensor_id][period][extreme_type]['timestamp']
                                        )
                            if 'last_reset' in self.extremes[sensor_id][period] and \
                               self.extremes[sensor_id][period]['last_reset']:
                                self.extremes[sensor_id][period]['last_reset'] = \
                                    datetime.fromisoformat(self.extremes[sensor_id][period]['last_reset'])
        except Exception as e:
            _LOGGER.error(f"Error loading persistent data: {e}")
    
    @callback
    async def _save_persistent_data(self, *args):
        """Save persistent data to file."""
        if not self.persistence:
            return
            
        try:
            data = {'extremes': {}}
            
            # Deep copy extremes and convert datetime objects to strings
            for sensor_id in self.extremes:
                data['extremes'][sensor_id] = {}
                for period in self.extremes[sensor_id]:
                    data['extremes'][sensor_id][period] = {
                        'high': {
                            'value': self.extremes[sensor_id][period]['high']['value'],
                            'timestamp': self.extremes[sensor_id][period]['high']['timestamp'].isoformat() \
                                if self.extremes[sensor_id][period]['high']['timestamp'] else None
                        },
                        'low': {
                            'value': self.extremes[sensor_id][period]['low']['value'],
                            'timestamp': self.extremes[sensor_id][period]['low']['timestamp'].isoformat() \
                                if self.extremes[sensor_id][period]['low']['timestamp'] else None
                        }
                    }
                    if 'last_reset' in self.extremes[sensor_id][period]:
                        data['extremes'][sensor_id][period]['last_reset'] = \
                            self.extremes[sensor_id][period]['last_reset'].isoformat() \
                            if self.extremes[sensor_id][period]['last_reset'] else None
            
            with open(self.config_path, 'w') as file:
                json.dump(data, file, indent=2)
        except Exception as e:
            _LOGGER.error(f"Error saving persistent data: {e}")
    
    def _calculate_averages(self, sensor_id: str, current_value: float, now: datetime):
        """Calculate rolling and period averages."""
        # Update rolling average data points
        self.data_points[sensor_id].append({
            'value': current_value,
            'timestamp': now
        })
        
        # Remove old data points outside the averaging window
        window_minutes = self.sensors[sensor_id]['averaging_window']
        cutoff_time = now - timedelta(minutes=window_minutes)
        self.data_points[sensor_id] = [
            dp for dp in self.data_points[sensor_id]
            if dp['timestamp'] > cutoff_time
        ]
        
        # Calculate current rolling average
        values = [dp['value'] for dp in self.data_points[sensor_id]]
        if values:
            self.averages[sensor_id]['current'] = statistics.mean(values)
        
        # Calculate period averages (day, week, month, year)
        periods = ['day', 'week', 'month', 'year']
        for period in periods:
            if self.extremes[sensor_id][period]['high']['value'] is not None and \
               self.extremes[sensor_id][period]['low']['value'] is not None:
                self.averages[sensor_id][period] = statistics.mean([
                    self.extremes[sensor_id][period]['high']['value'],
                    self.extremes[sensor_id][period]['low']['value']
                ])
    
    @callback
    async def _handle_midnight(self, *args):
        """Handle daily reset and check for other period resets."""
        now = datetime.now()
        
        for sensor_id in self.extremes:
            # Check and reset daily extremes
            self._reset_period_if_needed(sensor_id, 'day', now)
            
            # Check and reset weekly extremes
            if now.weekday() == 0:  # Monday
                self._reset_period_if_needed(sensor_id, 'week', now)
            
            # Check and reset monthly extremes
            if now.day == 1:
                self._reset_period_if_needed(sensor_id, 'month', now)
            
            # Check and reset yearly extremes
            if now.month == 1 and now.day == 1:
                self._reset_period_if_needed(sensor_id, 'year', now)
    
    def _reset_period_if_needed(self, sensor_id: str, period: str, now: datetime):
        """Reset extremes for a specific period if needed."""
        self.extremes[sensor_id][period]['high']['value'] = None
        self.extremes[sensor_id][period]['high']['timestamp'] = None
        self.extremes[sensor_id][period]['low']['value'] = None
        self.extremes[sensor_id][period]['low']['timestamp'] = None
        self.extremes[sensor_id][period]['last_reset'] = now
        self.averages[sensor_id][period] = None
    
    @callback
    def _handle_state_change(self, entity_id, old_state, new_state):
        """Handle state changes for tracked sensors."""
        if new_state is None or new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return
        
        try:
            current_value = float(new_state.state)
            decimal_places = self.sensors[entity_id]['decimal_places']
            current_value = round(current_value, decimal_places)
        except (ValueError, TypeError):
            _LOGGER.warning(f"Invalid state value for {entity_id}: {new_state.state}")
            return
        
        now = datetime.now()
        self._update_extremes(entity_id, current_value, now)
        self._calculate_averages(entity_id, current_value, now)
        self._update_sensor_entities(entity_id)
    
    def _update_extremes(self, entity_id: str, value: float, now: datetime):
        """Update extremes for all time periods."""
        periods = {
            'day': lambda x: x.date() == now.date(),
            'week': lambda x: x.isocalendar()[1] == now.isocalendar()[1] and x.year == now.year,
            'month': lambda x: x.month == now.month and x.year == now.year,
            'year': lambda x: x.year == now.year
        }
        
        extremes = self.extremes[entity_id]
        
        # Update period-based extremes
        for period, is_current in periods.items():
            if extremes[period]['last_reset'] is None or not is_current(extremes[period]['last_reset']):
                self._reset_period_if_needed(entity_id, period, now)
            
            if extremes[period]['high']['value'] is None or value > extremes[period]['high']['value']:
                extremes[period]['high']['value'] = value
                extremes[period]['high']['timestamp'] = now
            if extremes[period]['low']['value'] is None or value < extremes[period]['low']['value']:
                extremes[period]['low']['value'] = value
                extremes[period]['low']['timestamp'] = now
        
        # Update all-time extremes
        if extremes['all_time']['high']['value'] is None or value > extremes['all_time']['high']['value']:
            extremes['all_time']['high']['value'] = value
            extremes['all_time']['high']['timestamp'] = now
        if extremes['all_time']['low']['value'] is None or value < extremes['all_time']['low']['value']:
            extremes['all_time']['low']['value'] = value
            extremes['all_time']['low']['timestamp'] = now
    
    def _update_sensor_entities(self, entity_id: str):
        """Update or create sensor entities for the extremes and averages."""
        base_name = self.sensors[entity_id]['name']
        unit = self.sensors[entity_id]['unit']
        extremes = self.extremes[entity_id]
        decimal_places = self.sensors[entity_id]['decimal_places']
        
        # Update extreme sensors
        for period in extremes:
            for extreme_type in ['high', 'low']:
                sensor_name = f"{base_name} {period} {extreme_type}"
                value = extremes[period][extreme_type]['value']
                timestamp = extremes[period][extreme_type]['timestamp']
                
                if value is not None:
                    value = round(value, decimal_places)
                
                entity_id_extreme = f"sensor.{DOMAIN}_{base_name.lower()}_{period}_{extreme_type}"
                
                attributes = {
                    'unit_of_measurement': unit,
                    'friendly_name': sensor_name,
                    'last_reset': extremes[period].get('last_reset'),
                    'timestamp': timestamp.isoformat() if timestamp else None
                }
                
                self.hass.states.async_set(entity_id_extreme, value, attributes)
        
        # Update average sensors
        for period in ['current'] + list(extremes.keys()):
            if period != 'all_time':  # Skip all-time average as it might not be meaningful
                value = self.averages[entity_id][period]
                if value is not None:
                    value = round(value, decimal_places)
                
                sensor_name = f"{base_name} {period} average"
                entity_id_avg = f"sensor.{DOMAIN}_{base_name.lower()}_{period}_average"
                
                attributes = {
                    'unit_of_measurement': unit,
                    'friendly_name': sensor_name,
                    'last_reset': extremes[period].get('last_reset') if period != 'current' else None,
                    'averaging_window': self.sensors[entity_id]['averaging_window'] if period == 'current' else None
                }
                
                self.hass.states.async_set(entity_id_avg, value, attributes)

class WeatherExtremesSensor(Entity):
    """Representation of a Weather Extremes Sensor."""

    def __init__(self, tracker, entity_id, period, extreme_type):
        """Initialize the sensor."""
        self._tracker = tracker
        self._entity_id = entity_id
        self._period = period
        self._extreme_type = extreme_type
        self._name = f"{tracker.sensors[entity_id]['name']} {period} {extreme_type}"
        self._unique_id = f"{DOMAIN}_{tracker.sensors[entity_id]['name'].lower()}_{period}_{extreme_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._tracker.extremes[self._entity_id][self._period][self._extreme_type]['value']

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._tracker.sensors[self._entity_id]['unit']

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        # You might want to return appropriate device classes based on the type of measurement
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            'last_reset': self._tracker.extremes[self._entity_id][self._period].get('last_reset'),
            'timestamp': self._tracker.extremes[self._entity_id][self._period][self._extreme_type]['timestamp']
        }

class WeatherExtremesAverageSensor(Entity):
    """Representation of a Weather Extremes Average Sensor."""

    def __init__(self, tracker, entity_id, period):
        """Initialize the sensor."""
        self._tracker = tracker
        self._entity_id = entity_id
        self._period = period
        self._name = f"{tracker.sensors[entity_id]['name']} {period} average"
        self._unique_id = f"{DOMAIN}_{tracker.sensors[entity_id]['name'].lower()}_{period}_average"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._tracker.averages[self._entity_id][self._period]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._tracker.sensors[self._entity_id]['unit']

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = {
            'last_reset': self._tracker.extremes[self._entity_id][self._period].get('last_reset') \
                if self._period != 'current' else None,
        }
        
        if self._period == 'current':
            attributes['averaging_window'] = self._tracker.sensors[self._entity_id]['averaging_window']
        
        return attributes

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the Weather Extremes sensors."""
    tracker = WeatherExtremesTracker(hass, config)
    entities = []

    # Create sensor entities for each configured sensor
    for sensor_config in config[CONF_SENSORS]:
        entity_id = sensor_config['entity_id']
        
        # Create extreme sensors
        for period in ['day', 'week', 'month', 'year', 'all_time']:
            for extreme_type in ['high', 'low']:
                entities.append(WeatherExtremesSensor(tracker, entity_id, period, extreme_type))
        
        # Create average sensors
        for period in ['current', 'day', 'week', 'month', 'year']:
            entities.append(WeatherExtremesAverageSensor(tracker, entity_id, period))

    async_add_entities(entities, True)
    return True

# Add manifest.json content
manifest = {
    "domain": DOMAIN,
    "name": "Weather Extremes Tracker",
    "documentation": "https://github.com/custom-components/weather-extremes",
    "dependencies": [],
    "codeowners": ["@yourusername"],
    "requirements": [],
    "iot_class": "local_polling",
    "version": "1.0.0"
}

# Add services.yaml content
services = """
# No services defined yet
"""