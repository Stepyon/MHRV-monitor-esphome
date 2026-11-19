# MHRV Monitor — ESPHome

Wi-Fi temperature monitoring for mechanical heat-recovery ventilation (MHRV/MVHR), using an ESP8266 D1 mini, four DS18B20 digital probes, and Home Assistant.

## Features

- Four 12-bit temperature channels on a shared 1-Wire GPIO4 (D2) bus.
- Configurable polling from 1–300 s (default 5 s).
- Separate adjustable calibration offsets (±5 °C) for all four probes.
- Sliding-window moving average from 1 to 20 raw samples (default 4).
- 0.1 °C quantisation and adjustable 0–0.05 °C hysteresis (default 0.02 °C).
- Only publishes a temperature when it crosses a hysteresis threshold.
- Home Assistant controls persist after a reboot via ESP8266 flash storage.
- Encrypted ESPHome native API and authenticated/encrypted OTA using the same per-device key (ESPHome 2026.9+).
- Wi-Fi fallback hotspot and captive portal.

## Hardware

Use an ESP8266 board compatible with `d1_mini` and **four externally powered DS18B20** probes. Connect **all four** VDD to 3.3 V, GND to GND, DATA to GPIO4 / D2; place a **4.7 kΩ pull-up resistor** from DATA to 3.3 V. Avoid 5 V on the ESP8266 GPIO. Check the actual pin markings on your board.

Place probes at the supply, extract, exhaust, and outdoor-air ducts as desired. **Temperature 1–4 are deliberately generic**; map sensors to physical ducts before renaming them.

## Files

| File | Purpose |
| --- | --- |
| `mhrv-monitor.yaml` | Main ESPHome firmware configuration |
| `.temperature_filters.yaml` | Included per-channel moving average, calibration, and hysteresis filter |
| `secrets.example.yaml` | Template for local private configuration |
| `.gitignore` | Prevents accidentally committing `secrets.yaml` or compiled images |
| `.github/workflows/validate.yml` | YAML validation and compile on PRs and main |
| `.github/workflows/release.yml` | Version-tagged GitHub source releases |

**Important:** `.temperature_filters.yaml` starts with a dot. Show hidden files when copying the project; it must be alongside the main YAML.

## Getting started

1. Download or clone the repository and install the [ESPHome Device Builder](https://esphome.io/guides/getting_started_hassio/) in Home Assistant, or the [ESPHome CLI](https://esphome.io/guides/installing_esphome.html).
2. Copy `secrets.example.yaml` to `secrets.yaml`. Fill in the actual Wi-Fi details, a unique fallback AP password, and a **unique 32-byte Base64 API encryption key**, generated with `openssl rand -base64 32` or ESPHome's key generator. Never push `secrets.yaml`.
3. Check the temperature sensor mapping. The public config selects Dallas probes by hardware `index: 0` to `3`, so it can compile for other owners' hardware. **Indexes are sorted by hardware addresses, not physical duct position**, and may change when probes are added or replaced. After checking the discovered addresses in the logs, use each probe's `address: 0x...` instead of `index:` for reliable permanent mapping. Each sensor must have exactly one identifier.
4. Validate: `esphome config mhrv-monitor.yaml`.
5. First-time USB flash: `esphome run mhrv-monitor.yaml` and select the serial port, or install from ESPHome Device Builder. Reset/power-cycle the ESP8266 if the first OTA attempt after flashing fails.
6. In Home Assistant go to **Settings → Devices & services**, add the discovered ESPHome device, and use the encryption key configured above.
7. In the device's entities configure Polling Interval, Smoothing Window, Hysteresis, and Temperature 1–4 Calibration. All these controls retain their values across normal restarts.

The fallback hotspot is only for Wi-Fi recovery and uses the password you supplied. This firmware is designed for a trusted local network.

## Sensor processing

Every polling cycle requests updates of all four sensors consecutively. This is a synchronized *software polling loop*, not a guarantee that four independent DS18B20 sensors perform exactly simultaneous conversions. DS18B20 12-bit conversions can require up to approximately 750 ms; the 5-second default is a reasonable starting point.

Every channel gets its own copy of the included lambda filter with separate static history and last-published value. Invalid values are discarded. The filter stores the last 20 raw values, averages the latest N, adds that channel's calibration offset, and rounds to 0.1 °C. A new value is published only when the average crosses the 0.1 °C midpoint plus/minus the configured hysteresis, so minor fluctuations do not flood Home Assistant with repeated readings.

Changing a control does not immediately reprocess past sensor data. The change applies on the next measurement, except a polling interval change restarts the loop immediately.

### Defaults

| Control | Default | Range |
| --- | --- | --- |
| Temperature Polling Interval | 5 s | 1–300 s |
| Temperature Smoothing Window | 4 samples | 1–20 |
| Temperature Hysteresis | 0.02 °C | 0–0.05 °C |
| Temperature 1–4 Calibration | 0 °C each | −5 to +5 °C, in 0.05 °C steps |

The original personal setup had calibration offsets of 0, +0.05, −0.10, and −0.20 °C. Restore these in your own device controls if appropriate; public defaults remain zero.

## Updating OTA

### Recommended: compile your personalized firmware locally

The device supports native ESPHome OTA. In ESPHome Device Builder choose **Install → Wirelessly**; from a local checkout run:

```sh
esphome run mhrv-monitor.yaml --device mhrv-monitor.local
```

ESPHome compiles firmware containing **your own** Wi-Fi settings, API/OTA encryption key, and hardware mapping, and uploads it to the device via the encrypted OTA protocol. Use the actual hostname/IP if different. Ordinary Home Assistant ESPHome integration does not automatically install GitHub release binaries; it is the ESPHome Device Builder or CLI that performs this source-based update.

### Migrating from the original firmware

The original uploaded firmware already had **unencrypted ESPHome OTA**, but an encrypted native API. It is essential to **keep the same API encryption key** on the first update to preserve connectivity and migrate safely. This repository requires encrypted OTA, supported in ESPHome 2026.9 and later.

**Do not switch directly from an old plaintext-only OTA installation to strict encrypted OTA without following the transition procedure.** Follow the [ESPHome OTA encryption migration guide](https://esphome.io/components/ota/esphome/#encryption), which describes a staged two-upload migration or a one-time `allow_plaintext_upload` exception. Remove any temporary plaintext exception after upgrading.

For the existing device, replace `index: 0..3` with the original four `address:` assignments, in the same sensor order. Your existing original mapping is preserved only if you do this. Keep the existing API key privately in `secrets.yaml`. The original firmware also contained a hardcoded fallback AP password: generate a new unique one, and never put real device secrets in a public issue or commit.

### GitHub Actions and versioned releases

Pull requests and pushes to main run the pinned ESPHome 2026.11.0 validation/compile workflow. CI uses **dummy-only credentials** and deliberately does **not** distribute or upload its test firmware.

A Git tag named `v*` invokes the source-release workflow, publishing `mhrv-monitor-source.tar.gz` with the firmware, filter, example secrets and README. Download that source release and keep your **private** `secrets.yaml` and physical probe address mapping, then use the normal ESPHome OTA command.

**No public universal flashable firmware is provided:** ESPHome embeds credentials and encryption keys in its compiled images. Publishing a binary built for a real user's Wi-Fi or API key would disclose those credentials. A universal CI test image with dummy secrets is not suitable for deployment. This project currently supports secure **manual OTA**, not automatic upstream update notifications or a one-click public factory flasher.

## Troubleshooting

- **Missing filter include:** make sure the dot-prefixed `.temperature_filters.yaml` is in the YAML directory.
- **Missing/mislabeled sensors:** verify 3.3 V, common ground, DATA pull-up, wiring and detected ROM addresses in logs. Indexes depend on ROM addresses, not cable position.
- **Home Assistant cannot connect:** verify network access and that Home Assistant has the correct API encryption key.
- **OTA rejects the firmware:** follow the official migration steps for enabling encrypted OTA on an existing device; serial flashing is a fallback.
- **Wi-Fi changed:** use the configured fallback AP/captive portal or recover by flashing over USB.
- **No measurement yet:** sensor startup/conversion takes time; wait at least one polling cycle.

## Security

Use a **unique API key and fallback AP password per device**. `secrets.yaml` is ignored by Git, as are build outputs. Do not attach deployed-device binaries to public issues or releases. If old credentials were ever shared, rotate them after a successful migration.

## License

No license has yet been selected. Add a LICENSE file to clarify third-party usage and redistribution before publishing it as an open-source project.
