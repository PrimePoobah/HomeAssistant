# HomeAssistant

# 🌡️ Weather Extremes Tracker for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![hassfest validation](https://github.com/custom-components/weather-extremes/workflows/Validate%20with%20hassfest/badge.svg)
![Maintenance](https://img.shields.io/maintenance/yes/2024.svg)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

Track temperature and weather extremes over multiple time periods in Home Assistant. This custom component records high and low values for any sensor across daily, weekly, monthly, yearly, and all-time periods.

## Features

### 📊 Comprehensive Tracking
- Track high and low values across multiple time periods:
  - Daily extremes
  - Weekly extremes
  - Monthly extremes
  - Yearly extremes
  - All-time records

### 📈 Advanced Analytics
- Rolling averages with configurable time windows
- Period-based averages (daily, weekly, monthly, yearly)
- Exact timestamps for all extreme values
- Configurable decimal precision

### 💾 Data Management
- Persistent storage across restarts
- Data import/export capabilities
- Backup and restore functionality
- Historical data purging options

### ⚙️ Flexible Configuration
- Track any numeric sensor
- Customizable averaging windows
- Multiple data merge strategies
- Configurable update intervals

## Installation

### HACS (Preferred)
1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Add"
7. Search for "Weather Extremes Tracker"
8. Click Install
9. Restart Home Assistant

### Manual Installation
1. Download the latest release
2. Copy the `weather_extremes` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Basic Configuration
```yaml
# configuration.yaml
sensor:
  - platform: weather_extremes
    sensors:
      - entity_id: sensor.outdoor_temperature
        name: Outdoor Temperature
        unit_of_measurement: °C
```

### Advanced Configuration
```yaml
sensor:
  - platform: weather_extremes
    persistence: true
    sensors:
      - entity_id: sensor.outdoor_temperature
        name: Outdoor Temperature
        unit_of_measurement: °C
        averaging_window: 15
        decimal_places: 1
      
      - entity_id: sensor.wind_speed
        name: Wind Speed
        unit_of_measurement: km/h
        averaging_window: 5
        decimal_places: 0
      
      - entity_id: sensor.rainfall
        name: Rainfall
        unit_of_measurement: mm
        averaging_window: 30
        decimal_places: 2
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `persistence` | boolean | `true` | Enable/disable data persistence |
| `sensors` | list | *Required* | List of sensors to track |

#### Sensor Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `entity_id` | string | *Required* | Entity ID to track |
| `name` | string | *Required* | Display name |
| `unit_of_measurement` | string | Optional | Unit of measurement |
| `averaging_window` | integer | 5 | Minutes for rolling average (1-60) |
| `decimal_places` | integer | 1 | Decimal precision (0-3) |

## Generated Entities

For each configured sensor, the following entities are created:

### Extremes
- `sensor.weather_extremes_[name]_day_high`
- `sensor.weather_extremes_[name]_day_low`
- `sensor.weather_extremes_[name]_week_high`
- `sensor.weather_extremes_[name]_week_low`
- `sensor.weather_extremes_[name]_month_high`
- `sensor.weather_extremes_[name]_month_low`
- `sensor.weather_extremes_[name]_year_high`
- `sensor.weather_extremes_[name]_year_low`
- `sensor.weather_extremes_[name]_all_time_high`
- `sensor.weather_extremes_[name]_all_time_low`

### Averages
- `sensor.weather_extremes_[name]_current_average`
- `sensor.weather_extremes_[name]_day_average`
- `sensor.weather_extremes_[name]_week_average`
- `sensor.weather_extremes_[name]_month_average`
- `sensor.weather_extremes_[name]_year_average`

## Services

### Core Services
- `weather_extremes.reset_period`: Reset extremes for a specific period
- `weather_extremes.clear_history`: Clear historical data
- `weather_extremes.update_extremes`: Manually update values
- `weather_extremes.export_data`: Export data to JSON/CSV
- `weather_extremes.import_data`: Import historical data
- `weather_extremes.update_averaging_window`: Update averaging settings
- `weather_extremes.purge_old_data`: Remove old data

### Data Management
- `weather_extremes.backup_data`: Create complete backup
- `weather_extremes.restore_data`: Restore from backup

## Example Automations

### Record Temperature Alert
```yaml
automation:
  - alias: "New Temperature Record"
    trigger:
      - platform: state
        entity_id: sensor.weather_extremes_outdoor_temperature_all_time_high
    action:
      - service: notify.mobile_app
        data:
          title: "New Temperature Record!"
          message: >
            New all-time high: {{ states('sensor.weather_extremes_outdoor_temperature_all_time_high') }}°C
            Recorded at: {{ state_attr('sensor.weather_extremes_outdoor_temperature_all_time_high', 'timestamp') }}
```

### Daily Weather Summary
```yaml
automation:
  - alias: "Daily Weather Summary"
    trigger:
      - platform: time
        at: "23:59:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Daily Weather Summary"
          message: >
            Today's Temperature:
            High: {{ states('sensor.weather_extremes_outdoor_temperature_day_high') }}°C
            Low: {{ states('sensor.weather_extremes_outdoor_temperature_day_low') }}°C
            Average: {{ states('sensor.weather_extremes_outdoor_temperature_day_average') }}°C
```

## Lovelace Examples

### Basic Card
```yaml
type: entities
entities:
  - entity: sensor.weather_extremes_outdoor_temperature_day_high
  - entity: sensor.weather_extremes_outdoor_temperature_day_low
  - entity: sensor.weather_extremes_outdoor_temperature_day_average
title: Today's Temperature
```

### Advanced Statistics Card
```yaml
type: custom:apex-chart-card
header:
  title: Temperature History
  show: true
series:
  - entity: sensor.weather_extremes_outdoor_temperature_day_high
    type: line
    name: High
  - entity: sensor.weather_extremes_outdoor_temperature_day_low
    type: line
    name: Low
  - entity: sensor.weather_extremes_outdoor_temperature_day_average
    type: line
    name: Average
```

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

### Development
1. Clone this repository
2. Install development dependencies:
   ```bash
   pip install -r requirements_dev.txt
   ```
3. Run tests:
   ```bash
   pytest
   ```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Support

Need help? Try these resources:

- [Documentation](docs)
- [GitHub Issues](../../issues)
- [Discussion Forum](../../discussions)

## Authors

- Original Author: @yourusername
- [List of Contributors](../../contributors)

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/weather-extremes.svg
[commits]: https://github.com/custom-components/weather-extremes/commits/master
[license-shield]: https://img.shields.io/github/license/custom-components/weather-extremes.svg
[releases-shield]: https://img.shields.io/github/release/custom-components/weather-extremes.svg
[releases]: https://github.com/custom-components/weather-extremes/releases
