# MHRV Monitor (ESPHome)

Open-source, credential-free ESP8266 firmware for a four-probe mechanical heat recovery ventilation (MHRV / MVHR) temperature monitor. Firmware is designed for a Wemos D1 mini-compatible board, four DS18B20 digital sensors, and Home Assistant.

## Features

- Four 12-bit DS18B20 probes on a shared GPIO4 / D2 1-Wire bus.
- **Four named duct temperatures:** Outdoor Air, Supply Air, Extract Air, and Exhaust Air.
- **Four Home Assistant dropdowns** let you assign any of the four physical probes to each duct without editing YAML or reflashing.
- Configurable polling interval (1–300 seconds; default 5 seconds).
- Four independent per-sensor calibration offsets (±5 °C in 0.05 °C steps).
- Sliding-window moving average (1–20 samples; default 4).
- 0.1 °C quantisation plus user-configurable hysteresis (default 0.02 °C).
- Device settings saved to flash and restored across restarts.
- Encrypted ESPHome native API, with a different key provisioned for every device.
- **Compiled factory firmware**, installable via USB, with no preprogrammed user credentials.
- **Published HTTP OTA binaries and firmware manifest** with a Home Assistant update entity that checks for updates every 6 hours.
- Browser-based USB installation via ESP Web Tools (after enabling GitHub Pages).

**Important security limitation:** This design uses ESP8266 with ESPHome HTTP OTA. Its HTTP client cannot verify TLS server certificates, and the downloaded firmware is only checked against the MD5 provided in the same manifest. A network attacker able to replace both the firmware and manifest could install malicious firmware. This is **not an authenticated update channel**. Only deploy on networks where you accept this risk; prefer an ESP32 with supported signed OTA verification for a security-sensitive product.

## Hardware and wiring

Use a D1 mini-compatible ESP8266 with 4 MB flash if possible, four externally powered DS18B20 probes, and a **4.7 kΩ pull-up** between 3.3 V and DATA. Connect each sensor **VDD → 3.3 V**, **GND → GND**, **DATA → GPIO4 / D2**. Never drive an ESP8266 GPIO with 5 V.

Place your DS18B20 probes in the four ducts. The physical probes appear as the existing **Temperature 1–4** diagnostic measurements (also referred to as **Probe 1–4** in the mapping dropdowns), and four additional sensors expose stable duct-oriented names:

| Named temperature | Airflow measurement |
| --- | --- |
| **Outdoor Air** | Outside air entering the ventilation unit |
| **Supply Air** | Treated air delivered from the unit to the rooms |
| **Extract Air** | Air returning from rooms into the ventilation unit |
| **Exhaust Air** | Air discharged from the unit back outdoors |

**Important:** Probe numbers follow the DS18B20 hardware-address index (0–3), **not physical duct position or wiring order**. Index assignments can change if a sensor is added, removed, or replaced. The four dropdowns let the user correct mapping without reflashing. The mapping choices themselves persist across restarts and normal OTA updates, but aren't a guarantee that the physical probe indexes remain unchanged after hardware replacements.

## Install the compiled factory image

1. Open **[MHRV Monitor firmware installer](https://stepyon.github.io/MHRV-monitor-esphome/)**, after the first release is published and GitHub Pages is enabled. Use a desktop Chrome or Edge browser with Web Serial and connect the ESP8266 via USB.
2. Select **Install** and flash the factory firmware. Alternatively download `mhrv-monitor-vX.Y.Z-firmware.factory.bin` from [GitHub Releases](https://github.com/Stepyon/MHRV-monitor-esphome/releases) and flash via a compatible serial flashing tool at offset `0x0`.
3. Configure Wi-Fi via the USB **Improv Serial** setup, or join the device's initially open **MHRV Monitor Setup** Wi-Fi hotspot and visit `http://192.168.4.1` to enter your home Wi-Fi credentials. The open provisioning AP is for first-time setup; avoid doing this on an untrusted network.
4. Add the new device to **Settings → Devices & services → ESPHome** in Home Assistant. Its name contains a MAC suffix for uniqueness. Complete the **per-device encryption key provisioning** when prompted. Use a current Home Assistant version that supports provisioning.
5. The device exposes **four physical temperature channels (Temperature 1–4)**, **four named duct temperatures**, four probe-mapping dropdowns, seven numeric configuration controls, and an **MHRV Monitor Firmware** update entity. Adjust mapping, offsets and filtering in Home Assistant.

### Assign the probes in Home Assistant

On the ESPHome device page, find the four dropdowns:

| Mapping control | Initial default (placeholder) |
| --- | --- |
| Outdoor Air Probe | Probe 1 |
| Supply Air Probe | Probe 2 |
| Extract Air Probe | Probe 3 |
| Exhaust Air Probe | Probe 4 |

**These defaults are NOT guaranteed to match your actual ducts.** To identify each probe, temporarily warm or cool the probe tip before placing it in its final location and watch which **Temperature 1–4** reading changes. Then choose that numbered probe for the appropriate duct. The named temperature sensors update as soon as the mapping is changed (provided a reading is available), and maintain stable Home Assistant entity IDs even when mappings change.

Mappings are saved in ESP8266 flash through `restore_value: true`. The physical sensor calibration and smoothing still apply **before** any duct mapping. For example, changing the Supply Air dropdown to Probe 4 displays **Temperature 4**, including its individual calibration offset and configured smoothing.

For simplicity, the dropdowns don't prevent choosing the same probe for multiple ducts. For correct ventilation monitoring, **assign each probe to exactly one duct**. If hardware sensors are replaced, check the mapping again because index numbering can change.

The same compiled binary works for every new supported board: Wi-Fi credentials and the API encryption key are provisioned and stored in device flash, **not inside the public image**. ESPHome limits the initial provisioning window to five minutes; power-cycle the device if the setup window expires.

## One-click OTA from Home Assistant

After a release is published, the device reads a version manifest from:

`https://stepyon.github.io/MHRV-monitor-esphome/firmware/manifest.json`

The `update.http_request` component checks periodically and exposes an update entity in Home Assistant. If the published version is newer, Home Assistant can present a firmware update with an **Install** action. The ESP8266 downloads the matching `firmware.ota.bin` from GitHub Pages and flashes it, then reboots. It uses the OTA image, **not** the USB factory image.

Release versions are embedded in the firmware's `esphome.project.version`; both the image and the manifest are generated from the same `vX.Y.Z` tag. This is a **manual one-click update** model; updates are not silently installed. Keeping the flash partition and firmware format compatible matters across updates.

**Caveats:** ESP8266 HTTP OTA is vulnerable to network man-in-the-middle attacks because `verify_ssl: false` is required. A public MD5 checksum detects accidental corruption but does not authenticate a release. ESPHome also has a reported [ESP8266 HTTP OTA issue where stored Wi-Fi credentials can be lost](https://github.com/esphome/esphome/issues/16211), observed on certain 1 MB configurations. Use a D1 mini with 4 MB flash; **physically test whether Wi-Fi credentials, encryption keys and calibration settings survive an HTTP OTA on your chosen board before distributing it**. No compatibility test on hardware is implied by a successful CI compilation.

If an update fails, recovery may require USB serial flashing or re-provisioning Wi-Fi. For high-security deployments switch to ESP32 and a signed-OTA design.

### Local firmware customization

The universal factory firmware intentionally has **no native ESPHome OTA endpoint**. A runtime-provisioned API key cannot be inherited as a native OTA encryption key at build time, and enabling unauthenticated native OTA would expose all devices on the local network. Developers can instead USB-flash a custom image or add native encrypted OTA when building a personalized YAML with a known per-device key. Such builds are outside the common managed release channel.

## Releases and continuous integration

- Pull requests and pushes to `main`: GitHub Actions installs pinned **ESPHome 2026.11.0**, validates the no-secret YAML, compiles, and checks that both factory and OTA images are present.
- Push a tag like `v0.1.0` **after merging to main**: the release workflow compiles with `-s firmware_version 0.1.0`, runs `scripts/package_release.py`, creates a GitHub Release with both images, source archive and SHA256 checksums, and deploys a versioned OTA image plus latest update manifest to GitHub Pages.
- GitHub Pages must be enabled under **Settings → Pages → Build and deployment → Source: GitHub Actions** before the firmware feed works. The deployment workflow attempts to enable Pages but repository settings may still require manual intervention.
- Check the [Actions page](https://github.com/Stepyon/MHRV-monitor-esphome/actions) and published [GitHub Pages firmware manifest](https://stepyon.github.io/MHRV-monitor-esphome/firmware/manifest.json) before advertising a release. A merged PR alone does **not** publish a release or enable OTA notifications.

Release files include:
- `mhrv-monitor-vX.Y.Z-firmware.factory.bin` — serial first-install image.
- `mhrv-monitor-vX.Y.Z-firmware.ota.bin` — HTTP OTA update image.
- `mhrv-monitor-vX.Y.Z-source.tar.gz` — source files.
- `SHA256SUMS.txt` — independently checkable hashes.
- GitHub Pages `firmware/manifest.json` and `firmware/manifest.web.json` — latest-update and browser-installer manifests.

**Release maintenance:** Use an increasing version number, do not retag published versions, verify the release on the exact target ESP8266 board, and retain offline copies of older images for recovery. The public release feed follows the latest deployed tag; prerelease tags would also be published to the stable feed, so only tag versions you intend to offer everyone.

### Publishing a new firmware version

The source version defaults to `0.1.0` for local development; the tagged release workflow overrides it with `-s firmware_version X.Y.Z`. **After merging new changes, create a new version tag** (e.g. `v0.2.0`), rather than changing or retagging `v0.1.0`. Devices running `v0.1.0` will then see the newer release in Home Assistant once the GitHub Pages deployment succeeds.

## Filters, controls, and hardware identity

Each physical DS18B20 sensor receives an independent `.temperature_filters.yaml` lambda instance and history. The filter averages the most recent raw readings over the configured window, applies the sensor-specific calibration, rounds to 0.1 °C and publishes only when the midpoint plus hysteresis is crossed. Filtering does not retroactively reprocess previous samples after a control change.

The four named temperature entities are virtual template sensors driven by **Temperature 1–4** readings. When a physical probe publishes a new filtered temperature, the four mapped entities check their selected physical probes; a delta filter suppresses unchanged duplicate readings. Changing one of the four mapping dropdowns immediately refreshes the named temperatures, without a reboot or firmware rebuild. Mappings don't change the measured data on the physical probes.

| Home Assistant control | Default | Range |
| --- | --- | --- |
| Temperature Polling Interval | 5 s | 1–300 s |
| Temperature Smoothing Window | 4 samples | 1–20 |
| Temperature Hysteresis | 0.02 °C | 0–0.05 °C |
| Temperature 1–4 Calibration | 0 °C each | −5 to +5 °C |

The four Dallas sensor addresses depend on individual physical probes and are intentionally **not** committed. The personal original installation had offsets 0, +0.05, −0.10, and −0.20 °C, which can be entered in HA if suitable for your probes.

## Source and customization

The canonical, credential-free source is `mhrv-monitor.yaml`. The hidden `.temperature_filters.yaml` file must remain beside it. You can run:

```sh
pip install esphome==2026.11.0
esphome config mhrv-monitor.yaml
esphome compile mhrv-monitor.yaml
```

For a personalized fork, you may replace indexed probes with permanent addresses, but note that installing such customized firmware breaks alignment with the shared release channel. Customize with care and do not overwrite personal customizations with the public binary.

The optional `secrets.example.yaml` illustrates how to hold private credentials for a custom fork; the **standard factory source doesn't use secrets.yaml**. Keep any personal secrets out of Git and GitHub Actions.

## License

No license has been selected yet. Add a LICENSE file before encouraging third-party redistribution or contributions.
