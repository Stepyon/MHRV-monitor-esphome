#!/usr/bin/env python3
"""Package verified ESPHome factory + OTA images and public manifests."""
import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

from release_notes import summarize_release_notes

if len(sys.argv) not in (2, 3):
    raise SystemExit("Usage: package_release.py VERSION [GITHUB_RELEASE_NOTES.md]")
version = sys.argv[1]
notes_path = Path(sys.argv[2]) if len(sys.argv) == 3 else None
if notes_path is not None and not notes_path.is_file():
    raise SystemExit(f"Release notes file not found: {notes_path}")
if not version or any(c not in "0123456789.-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in version):
    raise SystemExit("Invalid release version")
out = Path("dist")
site = Path("site")
fw = site / "firmware" / version
fw.mkdir(parents=True, exist_ok=True)
out.mkdir(exist_ok=True)
builds = Path(".esphome/build")
for basename in ("firmware.factory.bin", "firmware.ota.bin"):
    matches = list(builds.rglob(basename))
    if len(matches) != 1:
        raise SystemExit(f"Expected one {basename}, found {len(matches)}")
    shutil.copyfile(matches[0], fw / basename)
    shutil.copyfile(matches[0], out / f"mhrv-monitor-v{version}-{basename}")
ota = fw / "firmware.ota.bin"
md5 = hashlib.md5(ota.read_bytes()).hexdigest()
sha = hashlib.sha256(ota.read_bytes()).hexdigest()
rel = f"https://github.com/Stepyon/MHRV-monitor-esphome/releases/tag/v{version}"
release_notes_text = notes_path.read_text(encoding="utf-8") if notes_path is not None else ""
release_summary = summarize_release_notes(release_notes_text, version)
manifest = {
    "name": "MHRV Monitor",
    "version": version,
    "builds": [{
        "chipFamily": "ESP8266",
        "ota": {
            "md5": md5,
            "path": f"/MHRV-monitor-esphome/firmware/{version}/firmware.ota.bin",
            "release_url": rel,
            "summary": release_summary
        }
    }]
}
(site / "firmware" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
web_manifest = {
    "name": "MHRV Monitor",
    "version": version,
    "builds": [{
        "chipFamily": "ESP8266",
        "improv": True,
        "parts": [{"path": f"{version}/firmware.factory.bin", "offset": 0}]
    }]
}
(site / "firmware" / "manifest.web.json").write_text(json.dumps(web_manifest, indent=2) + "\n")
(site / ".nojekyll").touch()
(site / "index.html").write_text("""<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MHRV Monitor — Install Firmware</title>
<style>body{max-width:720px;margin:4rem auto;padding:0 1rem;font:16px/1.5 system-ui,sans-serif}p{max-width:60ch}</style>
<h1>MHRV Monitor</h1>
<p>Install the credential-free factory firmware on a supported ESP8266 D1 mini using a USB cable and a Chromium browser (Chrome or Edge).</p>
<esp-web-install-button manifest="firmware/manifest.web.json"></esp-web-install-button>
<p>After installation, provision Wi-Fi over USB with Improv Serial or by connecting to the <strong>MHRV Monitor Setup</strong> access point. Then add the device to Home Assistant and provision its per-device encryption key.</p>
<p>New firmware versions are advertised in Home Assistant as an update entity. <strong>ESP8266 HTTP OTA cannot validate TLS certificates</strong>; remote updates have a man-in-the-middle risk. Review the <a href="https://github.com/Stepyon/MHRV-monitor-esphome#readme">README</a> before enabling updates.</p>
<script type="module" src="https://unpkg.com/esp-web-tools@10/dist/web/install-button.js?module"></script>
</html>
""")
files = [
    "mhrv-monitor.yaml", ".temperature_filters.yaml",
    "secrets.example.yaml", "README.md"
]
with tarfile.open(out / f"mhrv-monitor-v{version}-source.tar.gz", "w:gz") as tar:
    for path in files:
        tar.add(path)
checksums = []
for path in sorted(out.glob("*")):
    if path.is_file():
        checksums.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
(out / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n")
print(f"Packaged version={version}; ota_md5={md5}; ota_sha256={sha}")
