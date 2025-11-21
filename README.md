# Home Assistant Automations

This repository is where I'll store all things related to Home Assistant; at the moment it highlights a holiday lighting automation for Govee Permanent Lights Pro (Govee Permanent Outdoor Lights).

## Govee Permanent Lights Pro Christmas Automation

- Runs daily from November 15 through January 2 (inclusive).
- Triggers 34 minutes before sunset.
- Turns on `light.permanent_lights_pro` (Govee Permanent Lights Pro) with the "Christmas Tree" effect/profile.
- Turns off after 7 hours and 6 minutes.
- Uses the new Home Assistant automation format.

File: `automation_permanent_lights_pro_christmas.yaml`

### YAML (for reference)
```yaml
alias: Govee Permanent Lights Pro Christmas Tree
description: >
  Turn on Govee Permanent Lights Pro with the Christmas Tree scene each day between
  Nov 15 and Jan 2, 34 minutes before sunset, and turn off 7 hours 6 minutes later.
triggers:
  - event: sunset
    offset: "-00:34:00"
    trigger: sun
conditions:
  - condition: template
    value_template: >
      {% set m = now().month %} {% set d = now().day %} {{ (m == 11 and d >= 15)
      or (m == 12) or (m == 1 and d <= 2) }}
actions:
  - target:
      entity_id: light.permanent_lights_pro
    data:
      effect: Christmas Tree
      profile: Christmas Tree
    action: light.turn_on
  - delay:
      hours: 7
      minutes: 6
      seconds: 0
      milliseconds: 0
  - target:
      entity_id: light.permanent_lights_pro
    action: light.turn_off
mode: single
```

## Installation

1. Copy `automation_permanent_lights_pro_christmas.yaml` into your Home Assistant `automations` directory (or paste the YAML into the UI).
2. Reload automations or restart Home Assistant.

## Customization

- Adjust the `offset` for a different start time relative to sunset.
- Tweak the `delay` to change how long the lights stay on.
- Change the `effect`/`profile` or `entity_id` to match your setup.

## License

This project is licensed under the GNU General Public License v3.0 - see the `LICENSE` file for details.
