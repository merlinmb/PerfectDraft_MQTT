# Homebridge mqttthing Setup

This exposes the PerfectDraft stats published by this bridge as HomeKit accessories, using the [homebridge-mqttthing](https://github.com/arachnetech/homebridge-mqttthing) plugin to read the single retained JSON state topic this bridge publishes.

## 1. Install the plugin

On homebridge.local (or via the Homebridge UI's plugin search):

```
sudo npm install -g homebridge-mqttthing
```

## 2. Merge the accessory config

[homebridge-mqttthing-accessories.json](homebridge-mqttthing-accessories.json) contains four accessories, all reading from the retained topic this bridge publishes to (`stat/mcmdhome/Perfectdraft/528566/state`, i.e. `mqtt.base_topic` + machine ID from `config.yaml`):

| Accessory | HomeKit type | Source field | How it's extracted |
|---|---|---|---|
| PerfectDraft Beer Temp | Temperature Sensor | `details.temperature` | JSONPath suffix: `topic$.details.temperature` |
| PerfectDraft Door | Contact Sensor | `details.doorClosed` | `apply` function — inverted, since mqttthing's contact sensor treats `true`=not detected (open) and `false`=detected (closed), opposite of our `doorClosed` field |
| PerfectDraft Online | Occupancy Sensor | `details.connectedState` | JSONPath suffix |
| PerfectDraft Keg Volume | Light Sensor (repurposed) | `details.kegVolume` | `apply` function, litres reported as "lux" since HomeKit has no native keg/tank-level sensor type |

Copy the `accessories` array entries into your Homebridge `config.json`'s top-level `accessories` array (don't overwrite existing accessories — merge the array entries in).

If you change `mqtt.base_topic` or your machine ID differs from `528566`, update every topic string to match `<base_topic>/<machine_id>/state` from your `config.yaml`. If your MQTT broker isn't at `192.168.1.55:1883`, update the `"url"` field in each accessory (format: `mqtt://host:port`); add `"username"`/`"password"` fields if your broker requires auth.

## 3. Restart Homebridge

```
ssh pi@homebridge.local "sudo systemctl restart homebridge"
```

The four accessories should appear in the Home app once a poll cycle publishes a new retained message (within `poll_interval_seconds`, default 60s).

## Why a Light Sensor for keg volume?

HomeKit has no built-in "tank level" or generic 0–N gauge sensor type, and mqttthing doesn't expose a standalone battery-percentage accessory. Light Sensor is the closest read-only numeric sensor type available (range 0.0001–100000), so it's repurposed here to surface the litres-remaining value — the Home app will just label it as "lux." If that's too confusing day-to-day, this value is also visible directly via any MQTT client or the admin web UI's recent-calls view; you could alternatively pull it into Home Assistant (which has a proper generic sensor entity) instead of Homebridge.

## Not exposed

`firmwareVersion`, `serialNumber`, `errorCodes`, `kegPressure`, `durationOfLastPour`, `volumeOfLastPour`, and `numberOfPoursSinceStartup` aren't mapped to a HomeKit accessory — there's no reasonable HomeKit equivalent for most of these. The full raw JSON is still retained on the MQTT topic, so other tooling (Node-RED, Home Assistant, etc.) can read them directly if needed.
